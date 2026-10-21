# http_client.py: Client HTTP personalitzat sobre sockets TCP bloquejants.
#
# CONCEPTE CLAU PER A DAM (Client TCP i peticions HTTP manuals):
# El client no fa servir llibreries externes com 'requests' o 'urllib'.
# Implementa el protocol HTTP/1.1 a baix nivell utilitzant la llibreria 'socket' de Python:
# 1. connect(): Obre una connexió TCP amb el servidor (host, port).
# 2. sendall(): Envia el missatge HTTP (mètode, ruta, capçaleres, línia buida, cos JSON en bytes).
# 3. recv(): Llegeix la resposta en trossos ("chunks") fins que el servidor tanca la connexió.
# 4. Parsegem la resposta:
#    - Línia d'estat per obtenir el codi HTTP (200, 201, 400, 404...).
#    - Descodifiquem el cos JSON a diccionaris/llistes de Python.

import json
import socket
from dataclasses import dataclass
from typing import Any, Optional, Dict


@dataclass
class ApiResponse:
    """
    Encapsula el resultat d'una crida HTTP al servidor.
    Permet a la interfície d'usuari consultar fàcilment si l'operació ha tingut èxit.
    """
    status_code: int # Codi d'estat HTTP (ex: 200, 404, 500)
    data: Any # Dades rebudes del servidor
    error_message: Optional[str] = None # Missatge d'error si la petició ha fallat

    @property
    def is_success(self) -> bool:
        """Retorna True si el codi d'estat és 2xx (èxit)."""
        return 200 <= self.status_code < 300


class HttpClient:
    """
    Client TCP que envia peticions HTTP/1.1 al Servidor del Restaurant BackOffice.
    """

    def __init__(self, host: str = "localhost", port: int = 8088, timeout: float = 10.0):
        # Guardem la configuració bàsica de connexió
        self.host = host
        self.port = port
        self.timeout = timeout

    def _send_request(self, method: str, path: str, body: Any = None) -> ApiResponse:
        """
        Mètode intern que obre el socket TCP, envia la petició i rep la resposta.
        """
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creem el socket TCP bloquejant
        sock.settimeout(self.timeout) # Evita que app quedi penjada esperant infinitament a un servidor que no respon

        try:
            ## Anada de les dades:
            # 1. Connexió TCP amb el servidor
            sock.connect((self.host, self.port))

            # 2. Preparació del cos (si n'hi ha)
            body_bytes = b"" #Inicialitzem el cos buit en format binari (bytes)
            if body is not None:
                body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8") # Si body és Post o Put

            # 3. Construcció de la petició HTTP
            request_lines = [
                f"{method} {path} HTTP/1.1",
                f"Host: {self.host}:{self.port}",
                "Accept: application/json",
                "Connection: close",
            ]

            if body_bytes:
                request_lines.append("Content-Type: application/json; charset=utf-8")
                request_lines.append(f"Content-Length: {len(body_bytes)}")

            request_text = "\r\n".join(request_lines) + "\r\n\r\n"
            full_request_bytes = request_text.encode("utf-8") + body_bytes

            # 4. Enviament de bytes pel socket
            sock.sendall(full_request_bytes)

            ## Tornada de dades:
            # 5. Recepció de la resposta (anem acumulant fins que el servidor tanca el socket)
            response_buffer = bytearray() # Creem contenidor
            while True: # Mentres anem rebent dades...
                chunk = sock.recv(2048) # Demanem fins a 2048 bytes de cop
                if not chunk: # Si no s'han rebut dades -> break
                    break
                response_buffer.extend(chunk) # Si s'han rebut dades s'afegeixen a les que hi havia al contenidor.

            # 6. Processament de la resposta HTTP
            if not response_buffer:
                return ApiResponse(
                    status_code=500,
                    data=None,
                    error_message="El servidor ha tancat la connexió sense enviar resposta."
                )

            # Separem capçaleres i cos
            split_idx = response_buffer.find(b"\r\n\r\n")
            if split_idx != -1: # Si trobo separador -> trobo dades en la resposta
                raw_headers = response_buffer[:split_idx].decode("utf-8", errors="replace")
                raw_body = response_buffer[split_idx + 4:].decode("utf-8", errors="replace")
            else:
                raw_headers = response_buffer.decode("utf-8", errors="replace")
                raw_body = ""

            # Extreiem codi resposta
            header_lines = raw_headers.split("\r\n")
            status_line = header_lines[0].split()
            status_code = int(status_line[1]) if len(status_line) > 1 else 500

            # Descodifiquem el cos JSON
            parsed_data = None
            if raw_body.strip():
                try:
                    parsed_data = json.loads(raw_body)
                except json.JSONDecodeError:
                    parsed_data = raw_body

            # Si hi ha un error al cos (ex: {"error": "El nom no pot estar buit"})
            error_msg = None
            if not (200 <= status_code < 300):
                if isinstance(parsed_data, dict) and "error" in parsed_data:
                    error_msg = parsed_data["error"]
                else:
                    error_msg = f"Error HTTP {status_code}"

            # Retorna tota la informació decodificada en objecte python
            return ApiResponse(status_code=status_code, data=parsed_data, error_message=error_msg) 

        except ConnectionRefusedError:
            return ApiResponse(
                status_code=503,
                data=None,
                error_message=f"No s'ha pogut connectar al servidor ({self.host}:{self.port}). Assegura't que està engegat."
            )
        except socket.timeout:
            return ApiResponse(
                status_code=504,
                data=None,
                error_message="S'ha esgotat el temps d'espera (timeout) amb el servidor."
            )
        except Exception as e:
            return ApiResponse(
                status_code=500,
                data=None,
                error_message=f"Error de comunicació TCP: {str(e)}"
            )
        finally:
            # Passi el que passi es tancarà el socket
            sock.close()

    #El mètodes get/post/put/delete deleguen el treball pesat a _send_request
    def get(self, path: str) -> ApiResponse:
        """Envia una petició GET al servidor."""
        return self._send_request("GET", path)

    def post(self, path: str, data: Any = None) -> ApiResponse:
        """Envia una petició POST al servidor amb dades JSON."""
        return self._send_request("POST", path, body=data)

    def put(self, path: str, data: Any = None) -> ApiResponse:
        """Envia una petició PUT al servidor per modificar un recurs."""
        return self._send_request("PUT", path, body=data)

    def delete(self, path: str) -> ApiResponse:
        """Envia una petició DELETE al servidor."""
        return self._send_request("DELETE", path)
