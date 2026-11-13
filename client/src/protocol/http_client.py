# http_client.py: client HTTP sobre sockets TCP/TLS (dict ⇄ bytes HTTP, envia i rep).

import json
import socket
import ssl
from dataclasses import dataclass
from typing import Any, Optional

from common.security.digest import DIGEST_HEADER, compute_digest, verify_digest


@dataclass
class ApiResponse:
    """
    Encapsula el resultat d'una crida HTTP al servidor.
    Permet a la interfície d'usuari consultar fàcilment si l'operació ha tingut èxit.
    """

    status_code: int  # Codi d'estat HTTP (ex: 200, 404, 500)
    data: Any  # Dades rebudes del servidor
    error_message: Optional[str] = None  # Missatge d'error si la petició ha fallat

    # propietat calculada, no és un camp desat a la memòria.
    @property
    def is_success(self) -> bool:
        """Retorna True si el codi d'estat és 2xx (èxit)."""
        return 200 <= self.status_code < 300


def encode_request(method: str, path: str, host: str, port: int, body: Any = None) -> bytes:
    """
    Funció pura que construeix els bytes d'una petició HTTP/1.1 vàlida.
    Reutilitzada tant pel client síncron com per l'asíncron (sense duplicació).
    """
    body_bytes = b""
    if body is not None:
        body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")

    request_lines = [
        f"{method} {path} HTTP/1.1",
        f"Host: {host}:{port}",
        "Accept: application/json",
        "Connection: close",
    ]

    if body_bytes:
        request_lines.append("Content-Type: application/json; charset=utf-8")
        request_lines.append(f"Content-Length: {len(body_bytes)}")
        # CLAU (Pràctica 3): afegim el hash SHA-256 del cos per verificar-ne la integritat.
        request_lines.append(f"{DIGEST_HEADER}: {compute_digest(body_bytes)}")

    request_text = "\r\n".join(request_lines) + "\r\n\r\n"
    return request_text.encode("utf-8") + body_bytes


def decode_response(raw_bytes: bytes) -> ApiResponse:
    """
    Funció pura que converteix els bytes bruts d'una resposta HTTP en un ApiResponse.
    """
    # mirall del servidor: separa per línia buida (\r\n\r\n), llegeix codi i fa json.loads.
    if not raw_bytes:
        return ApiResponse(
            status_code=500,
            data=None,
            error_message="El servidor ha tancat la connexió sense enviar resposta.",
        )

    split_idx = raw_bytes.find(b"\r\n\r\n")
    if split_idx != -1:
        raw_headers = raw_bytes[:split_idx].decode("utf-8", errors="replace")
        raw_body_bytes = raw_bytes[split_idx + 4 :]
        raw_body = raw_body_bytes.decode("utf-8", errors="replace")
    else:
        raw_headers = raw_bytes.decode("utf-8", errors="replace")
        raw_body_bytes = b""
        raw_body = ""

    header_lines = raw_headers.split("\r\n")
    status_line = header_lines[0].split()
    status_code = int(status_line[1]) if len(status_line) > 1 else 500

    # CLAU (Pràctica 3): si la resposta té cos, el Content-Hash és obligatori i ha de coincidir.
    headers_dict: dict[str, str] = {}
    for line in header_lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            headers_dict[key.strip().lower()] = val.strip()

    if raw_body_bytes:
        received_digest = headers_dict.get(DIGEST_HEADER.lower())
        if not received_digest or not received_digest.strip():
            return ApiResponse(
                status_code=500,
                data=None,
                error_message=(
                    f"Error d'integritat: falta la capçalera {DIGEST_HEADER} a la resposta."
                ),
            )
        if not verify_digest(raw_body_bytes, received_digest):
            return ApiResponse(
                status_code=500,
                data=None,
                error_message=(
                    f"Error d'integritat: el {DIGEST_HEADER} de la resposta no coincideix."
                ),
            )

    parsed_data = None
    if raw_body.strip():
        try:
            parsed_data = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed_data = raw_body

    error_msg = None
    if not (200 <= status_code < 300):
        if isinstance(parsed_data, dict) and "error" in parsed_data:
            error_msg = parsed_data["error"]
        else:
            error_msg = f"Error HTTP {status_code}"

    return ApiResponse(status_code=status_code, data=parsed_data, error_message=error_msg)


class HttpClient:
    """
    Client TCP/TLS que envia peticions HTTP/1.1 al Servidor del Restaurant BackOffice.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8088,
        timeout: float = 10.0,
        use_ssl: bool = True,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.last_tls_info: tuple[str | None, str | None] | None = None

    def _send_request(self, method: str, path: str, body: Any = None) -> ApiResponse:
        """
        Mètode intern que obre el socket TCP/TLS, envia la petició i rep la resposta.
        """
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_sock.settimeout(self.timeout)

        # CLAU (Pràctica 3): ssl._create_unverified_context() accepta el certificat autosignat
        # del servidor sense llançar CERTIFICATE_VERIFY_FAILED.
        if self.use_ssl:
            context = ssl._create_unverified_context()
            sock = context.wrap_socket(raw_sock, server_hostname=self.host)
        else:
            sock = raw_sock

        try:
            sock.connect((self.host, self.port))
            if self.use_ssl and isinstance(sock, ssl.SSLSocket):
                cipher = sock.cipher()
                self.last_tls_info = (sock.version(), cipher[0] if cipher else None)
            full_request_bytes = encode_request(method, path, self.host, self.port, body)
            # sendall insisteix fins transmetre tots els bytes (a diferència de send).
            sock.sendall(full_request_bytes)

            response_buffer = bytearray()
            # bucle recv llegeix fins a b"" perquè el servidor tanca el socket en acabar.
            while True:
                chunk = sock.recv(2048)
                if not chunk:
                    break
                response_buffer.extend(chunk)

            return decode_response(bytes(response_buffer))

        # CLAU: errors de xarxa convertits a ApiResponse local (503/504/500); el client no peta.
        except ConnectionRefusedError:
            return ApiResponse(
                status_code=503,
                data=None,
                error_message=(
                    f"No s'ha pogut connectar al servidor ({self.host}:{self.port}). "
                    "Assegura't que està engegat."
                ),
            )
        except socket.timeout:
            return ApiResponse(
                status_code=504,
                data=None,
                error_message="S'ha esgotat el temps d'espera (timeout) amb el servidor.",
            )
        except Exception as error:
            return ApiResponse(
                status_code=500, data=None, error_message=f"Error de comunicació TCP: {str(error)}"
            )
        finally:
            sock.close()

    # dreceres HTTP; cadascuna fa l'anada (sendall) i la tornada (recv + decode_response).
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
