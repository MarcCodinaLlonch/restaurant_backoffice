# request_parser.py: Parser per analitzar les peticions HTTP sobre un socket TCP o StreamReader.
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs

from .errors import ProtocolError


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
    Parser pur per interpretar peticions HTTP/1.1 sense dependències d'I/O.
    """

    @staticmethod
    def parse_head(head_bytes: bytes) -> HttpRequest:
        """
        Interpreta exclusivament la capçalera HTTP (fins a \r\n\r\n).
        Retorna un objecte HttpRequest amb body=None.
        Llança ProtocolError si el format de la capçalera és invàlid.
        """
        raw_text = head_bytes.decode("utf-8", errors="replace")
        lines = raw_text.split("\r\n")
        if not lines or not lines[0].strip():
            raise ProtocolError("Peticio HTTP buida.")

        first_line_parts = lines[0].strip().split()
        if len(first_line_parts) < 2:
            raise ProtocolError(f"Linia de peticio mal formada: {lines[0]}")

        method = first_line_parts[0].upper()
        path = first_line_parts[1]
        version = first_line_parts[2] if len(first_line_parts) > 2 else "HTTP/1.1"

        headers: Dict[str, str] = {}
        for line in lines[1:]:
            if ":" in line:
                key, val = line.split(":", 1)
                headers[key.strip().lower()] = val.strip()

        parsed_url = urlparse(path)
        raw_path = parsed_url.path
        raw_query = parse_qs(parsed_url.query)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in raw_query.items()}

        return HttpRequest(
            method=method,
            path=path,
            raw_path=raw_path,
            version=version,
            headers=headers,
            query_params=query_params,
            body=None
        )

    @staticmethod
    def parse_body(raw_body: bytes, content_type: str = "") -> Any:
        """
        Interpreta els bytes del cos de la petició segons el Content-Type (JSON o text).
        """
        if not raw_body:
            return None
        text = raw_body.decode("utf-8", errors="replace")
        if "application/json" in content_type.lower() or text.startswith(("{", "[")):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return text

    @staticmethod
    def parse_bytes(data: bytes) -> Optional[HttpRequest]:
        """
        Mètode auxiliar pur (útil per a tests): rep els bytes sencers d'una petició
        i reutilitza parse_head i parse_body.
        """
        if not data:
            return None

        if b"\r\n\r\n" in data:
            head_part, body_part = data.split(b"\r\n\r\n", 1)
        else:
            head_part, body_part = data, b""

        try:
            request = RequestParser.parse_head(head_part)
        except ProtocolError:
            return None

        content_length = int(request.headers.get("content-length", "0"))
        if content_length > 0 and body_part:
            body_bytes = body_part[:content_length]
            request.body = RequestParser.parse_body(
                body_bytes, request.headers.get("content-type", "")
            )
        return request

    @staticmethod
    def parse_from_socket(client_socket, timeout: float = 5.0) -> Optional[HttpRequest]:
        """
        Llegeix pas a pas d'un socket síncron reutilitzant parse_head i parse_body.
        (Manté retrocompatibilitat amb la P1).
        """
        client_socket.settimeout(timeout)
        buffer = bytearray()

        while b"\r\n\r\n" not in buffer:
            chunk = client_socket.recv(1024)
            if not chunk:
                if not buffer:
                    return None
                break
            buffer.extend(chunk)

        if not buffer:
            return None

        header_end = buffer.find(b"\r\n\r\n")
        if header_end == -1:
            head_bytes = bytes(buffer)
            remaining_body = b""
        else:
            head_bytes = bytes(buffer[:header_end])
            remaining_body = bytes(buffer[header_end + 4:])

        try:
            request = RequestParser.parse_head(head_bytes)
        except ProtocolError:
            return None

        try:
            content_length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return None

        if content_length > 0:
            body_bytes = bytearray(remaining_body)
            while len(body_bytes) < content_length:
                chunk = client_socket.recv(min(1024, content_length - len(body_bytes)))
                if not chunk:
                    break
                body_bytes.extend(chunk)

            request.body = RequestParser.parse_body(
                bytes(body_bytes[:content_length]),
                request.headers.get("content-type", "")
            )

        return request