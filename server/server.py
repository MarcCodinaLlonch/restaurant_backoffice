# server.py: Servidor TCP per a Restaurant BackOffice.
#
# CONCEPTE CLAU PER A DAM (Servidor TCP amb sockets bloquejants):
# Aquest programa és el "cervell" de l'arquitectura Client/Servidor:
# 1. Crea un socket TCP utilitzant la llibreria estàndard 'socket' de Python.
# 2. Fa bind() a la IP i Port configurats (per defecte 0.0.0.0:8080).
# 3. Escolta (listen) connexions entrants. Com que l'activitat demana gestionar
#    un sol client a la vegada, fem servir un bucle seqüencial d'accept().
# 4. En rebre una connexió:
#    - Llegeix els bytes del socket i els analitza amb RequestParser.
#    - Passa la petició al Router, que delega als Services i a la Persistència (BD).
#    - Retorna la resposta HTTP amb ResponseBuilder.
#    - Tanca la connexió (model stateless: cada petició obre i tanca).

import os
import sys
import socket

# Assegurem que l'arrel del projecte és la primera ruta de sys.path
# i eliminem el directori 'server' de sys.path perquè Python no confongui el fitxer 'server.py' amb el paquet 'server'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.src.persistence.config import DB_URL, SERVER_HOST, SERVER_PORT
from server.src.persistence.unit_of_work import UnitOfWorkFactory
from server.src.services import (
    CategoryService,
    AllergenService,
    DishService,
    EmployeeService,
    MenuService,
    SaleService,
)
from server.src.protocol import RequestParser, Router, ResponseBuilder


def create_router(db_url: str) -> Router:
    """
    Inicialitza la factoria de persistència, els serveis de negoci i l'enrutador.
    """
    uow_factory = UnitOfWorkFactory(db_url)
    category_svc = CategoryService(uow_factory)
    allergen_svc = AllergenService(uow_factory)
    dish_svc = DishService(uow_factory)
    employee_svc = EmployeeService(uow_factory)
    menu_svc = MenuService(uow_factory)
    sale_svc = SaleService(uow_factory)

    return Router(
        category_service=category_svc,
        allergen_service=allergen_svc,
        dish_service=dish_svc,
        employee_service=employee_svc,
        menu_service=menu_svc,
        sale_service=sale_svc,
    )


def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT, db_url: str = DB_URL):
    """
    Inicia el bucle principal del servidor TCP.
    """
    if not db_url:
        print("[ERROR CRÍTIC] No s'ha definit cap URL de connexió a la base de dades.")
        print("Comprova el fitxer .env o les variables d'entorn.")
        sys.exit(1)

    print(f"[*] Inicialitzant serveis i connexió a la BD ({db_url.split('@')[-1] if '@' in db_url else db_url})...")
    
    # 1. Assegurem que la BD existeix a PostgreSQL (la crea si és una instal·lació neta)
    from server.src.persistence.seed import ensure_database_exists, seed_initial_data
    ensure_database_exists(db_url)

    # 2. Creem les taules de la BD si encara no existeixen
    from server.src.persistence.db import Base, engine, Session
    if engine:
        Base.metadata.create_all(bind=engine)
        # 3. Població automàtica de dades de prova si la base de dades està buida
        seed_initial_data(Session)

    router = create_router(db_url)

    # Creem el socket TCP (AF_INET = IPv4, SOCK_STREAM = TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR permet reiniciar el servidor ràpidament sense esperar el timeout del sistema operatiu
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((host, port))
    # listen(1): Cua per a 1 client simultani, tal com demana l'enunciat
    server_socket.listen(1)

    print("=" * 60)
    print(f" RESTAURANT BACKOFFICE — SERVIDOR TCP EN EXECUCIÓ")
    print(f" Escoltant a: http://{host}:{port}/")
    print(f" Protocol: HTTP/1.1 REST sobre TCP (Sockets bloquejants)")
    print(f" Prem Ctrl+C per aturar el servidor.")
    print("=" * 60)

    try:
        while True:
            # accept() bloqueja el fil d'execució fins que arriba una nova connexió de client
            client_socket, client_address = server_socket.accept()
            # print(f"[+] Connexió rebuda des de {client_address[0]}:{client_address[1]}")

            try:
                # 1. Llegim i parsegem la petició HTTP del client
                request = RequestParser.parse_from_socket(client_socket, timeout=5.0)

                if request:
                    # print(f"    --> {request.method} {request.path}")
                    # 2. El Router delega la feina a la capa de serveis
                    response_bytes = router.handle_request(request)
                else:
                    response_bytes = ResponseBuilder.bad_request("Petició buida o mal formada.")

                # 3. Enviem la resposta completa en bytes pel socket TCP
                client_socket.sendall(response_bytes)

            except socket.timeout:
                print(f"[!] Timeout llegint dades de {client_address}")
            except Exception as e:
                print(f"[!] Error processant petició de {client_address}: {e}")
                err_resp = ResponseBuilder.internal_error(str(e))
                try:
                    client_socket.sendall(err_resp)
                except Exception:
                    pass
            finally:
                # 4. Tanquem el socket (connexió stateless)
                client_socket.close()

    except KeyboardInterrupt:
        print("\n[*] Aturant el servidor per petició de l'usuari...")
    finally:
        server_socket.close()
        print("[*] Servidor aturat correctament.")


if __name__ == "__main__":
    run_server()
