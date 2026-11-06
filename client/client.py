# client.py: Punt d'entrada de l'aplicació Client per a Restaurant BackOffice.
#
# CONCEPTE CLAU PER A DAM (Client TCP Independent):
# Aquest programa s'executa de forma completament independent del Servidor.
# No requereix cap connexió directa a la base de dades ni instal·lació de PostgreSQL.
# Només necessita conèixer la IP i Port del Servidor per comunicar-s'hi per xarxa TCP.

import os
import sys

# Assegurem que l'arrel del projecte és la primera ruta de sys.path
# i eliminem el directori 'client' de sys.path perquè Python no confongui
# el fitxer 'client.py' amb el paquet 'client'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rich import box  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.text import Text  # noqa: E402

from client.src.protocol.http_client import HttpClient  # noqa: E402
from client.src.ui import (  # noqa: E402
    menu_allergens,
    menu_categories,
    menu_dishes,
    menu_employees,
    menu_menus,
    menu_sales,
)

console = Console()


def print_banner():
    """Mostra el bàner d'inici de l'aplicació."""
    banner_path = os.path.join(os.path.dirname(__file__), "..", "banner.txt")
    try:
        with open(banner_path, "r", encoding="utf-8") as file:
            ascii_art = file.read()
            console.print(Text(ascii_art, style="bold cyan"))
    except FileNotFoundError:
        pass


def main_menu(client: HttpClient):
    """Menú principal interactiu del client."""
    while True:
        console.clear()
        print_banner()

        console.print(
            Panel.fit(
                f"[bold blue]Restaurant BackOffice (Client TCP) — "
                f"Servidor: {client.host}:{client.port}[/bold blue]",
                border_style="blue",
                box=box.DOUBLE,
            )
        )
        console.print("1. Gestió d'Empleats")
        console.print("2. Gestió de Categories")
        console.print("3. Gestió de Plats")
        console.print("4. Gestió d'Al·lèrgens")
        console.print("5. Gestió de Menús")
        console.print("6. Gestió de Vendes")
        console.print("0. Sortir")

        option = console.input("\n[bold yellow]Selecciona una opció:[/bold yellow] ")

        if option == "1":
            menu_employees(client)
        elif option == "2":
            menu_categories(client)
        elif option == "3":
            menu_dishes(client)
        elif option == "4":
            menu_allergens(client)
        elif option == "5":
            menu_menus(client)
        elif option == "6":
            menu_sales(client)
        elif option == "0":
            console.print("[green]Fins aviat![/green]")
            break
        else:
            console.print("[red]Opció no vàlida.[/red]")
            console.input("Prem Enter per continuar...")


if __name__ == "__main__":
    # Obtenim configuració del servidor des de variables d'entorn o valors per defecte
    host = os.getenv("SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("SERVER_PORT", "8088"))

    # Instanciem el client HTTP sobre TCP
    client = HttpClient(host=host, port=port)

    # Iniciem la interfície d'usuari
    main_menu(client)
