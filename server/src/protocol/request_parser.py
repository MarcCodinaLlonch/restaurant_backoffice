# request_parser.py: Parser per analitzar les peticions HTTP sobre un socket TCP.
#
# CONCEPTE CLAU PER A DAM (Protocol HTTP sobre TCP):
# Un socket TCP és un flux continu de bytes ("stream"). No sap on acaba un missatge i on comença el següent!
# Per això, el protocol HTTP defineix:
# 1. Cada línia de text acaba amb CRLF: '\r\n' (en bytes: b'\r\n').
# 2. Les capçaleres (headers) acaben quan trobem una línia buida: '\r\n\r\n'.
# 3. Si la petició té un cos (body JSON, típic en POST/PUT), la capçalera 'Content-Length'
#    ens indica exactament quants bytes hem de llegir a continuació.

import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs


@dataclass
class HttpRequest:
    """
    Representa una petició HTTP ja analitzada i estructurada.
    """
    method: str                              # GET, POST, PUT, DELETE, etc.
    path: str                                # Ruta completa: /categories/1?sort=id
    raw_path: str                            # Ruta sense query params: /categories/1
    version: str                             # HTTP/1.1
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None               # Dades del cos en format diccionari/llista Python


class RequestParser:
    """
    Llegeix bytes d'un socket TCP i els converteix en un objecte HttpRequest.
    """

    @staticmethod
    def parse_from_socket(client_socket, timeout: float = 5.0) -> Optional[HttpRequest]:
        """
        Llegeix pas a pas del socket TCP fins a tenir la petició completa.
        Retorna HttpRequest o None si la connexió s'ha tancat.
        """
        client_socket.settimeout(timeout)
        buffer = bytearray()

        # 1. Llegim del socket fins trobar el final de les capçaleres: b'\r\n\r\n'
        while b"\r\n\r\n" not in buffer:
            chunk = client_socket.recv(1024)
            if not chunk:
                # El client ha tancat el socket abans d'enviar capçaleres completes
                if not buffer:
                    return None
                break
            buffer.extend(chunk)

        if not buffer:
            return None

        # 2. Separem la part de capçaleres i el que pugui haver sobrat per al cos
        header_end = buffer.find(b"\r\n\r\n")
        if header_end == -1:
            raw_headers = buffer.decode("utf-8", errors="replace")
            remaining_body = b""
        else:
            raw_headers = buffer[:header_end].decode("utf-8", errors="replace")
            remaining_body = buffer[header_end + 4:]

        lines = raw_headers.split("\r\n")
        if not lines or not lines[0].strip():
            return None

        # 3. Primera línia de la petició: Mètode, Recurs i Versió (ex: GET /categories HTTP/1.1)
        first_line = lines[0].strip().split()
        if len(first_line) < 2:
            return None

        method = first_line[0].upper()
        path = first_line[1]
        version = first_line[2] if len(first_line) > 2 else "HTTP/1.1"

        # 4. Parsegem les capçaleres (clau: valor)
        headers: Dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        # 5. Extraiem els query parameters de la URL (ex: /sales?date=2026-10-11)
        parsed_url = urlparse(path)
        raw_path = parsed_url.path
        raw_query = parse_qs(parsed_url.query)
        # Convertim llistes de valors a valors simples (per comoditat)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in raw_query.items()}

        # 6. Comprovem si hi ha un cos mitjançant la capçalera 'Content-Length'
        content_length = int(headers.get("content-length", "0"))
        body_data = None

        if content_length > 0:
            # Hem de llegir exactament el nombre de bytes indicat per Content-Length
            body_bytes = bytearray(remaining_body)
            while len(body_bytes) < content_length:
                chunk = client_socket.recv(min(1024, content_length - len(body_bytes)))
                if not chunk:
                    break
                body_bytes.extend(chunk)

            raw_body_text = body_bytes[:content_length].decode("utf-8", errors="replace")
            # Si el contingut és JSON, el convertim directament a diccionari Python
            content_type = headers.get("content-type", "")
            if "application/json" in content_type or raw_body_text.startswith(("{", "[")):
                try:
                    body_data = json.loads(raw_body_text)
                except json.JSONDecodeError:
                    body_data = raw_body_text
            else:
                body_data = raw_body_text

        return HttpRequest(
            method=method,
            path=path,
            raw_path=raw_path,
            version=version,
            headers=headers,
            query_params=query_params,
            body=body_data
        )

    @staticmethod
    def parse_bytes(data: bytes) -> Optional[HttpRequest]:
        """
        Mètode auxiliar útil per a proves unitàries (tests) sense necessitat de socket real.
        """
        if b"\r\n\r\n" not in data:
            # Si no té \r\n\r\n, mirem si té almenys la primera línia
            header_part = data.decode("utf-8", errors="replace")
            body_part = ""
        else:
            split_idx = data.find(b"\r\n\r\n")
            header_part = data[:split_idx].decode("utf-8", errors="replace")
            body_part = data[split_idx + 4:].decode("utf-8", errors="replace")

        lines = header_part.split("\r\n")
        if not lines or not lines[0].strip():
            return None

        first_line = lines[0].strip().split()
        if len(first_line) < 2:
            return None

        method = first_line[0].upper()
        path = first_line[1]
        version = first_line[2] if len(first_line) > 2 else "HTTP/1.1"

        headers: Dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        parsed_url = urlparse(path)
        raw_path = parsed_url.path
        raw_query = parse_qs(parsed_url.query)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in raw_query.items()}

        body_data = None
        if body_part.strip():
            try:
                body_data = json.loads(body_part)
            except json.JSONDecodeError:
                body_data = body_part

        return HttpRequest(
            method=method,
            path=path,
            raw_path=raw_path,
            version=version,
            headers=headers,
            query_params=query_params,
            body=body_data
        )
