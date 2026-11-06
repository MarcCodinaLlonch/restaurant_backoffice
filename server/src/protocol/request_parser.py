# request_parser.py: Converteix bytes HTTP en un objecte HttpRequest.
#
# CONCEPTE: funcions PURES (no fan I/O). Reben bytes i retornen objectes.
# Qui llegeix del socket és async_request_reader.py; aquí només interpretem.
import json
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import parse_qs, urlparse

from .errors import ProtocolError


@dataclass
class HttpRequest:
    """
    Representa una petició HTTP ja analitzada i estructurada.
    """

    method: str  # GET, POST, PUT, DELETE, etc.
    path: str  # Ruta completa: /categories/1?sort=id
    raw_path: str  # Ruta sense query params: /categories/1
    version: str  # HTTP/1.1
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    body: Any | None = None  # Dades del cos en format diccionari/llista Python


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
            raise ProtocolError("Petició HTTP buida.")

        first_line_parts = lines[0].strip().split()
        if len(first_line_parts) < 2:
            raise ProtocolError(f"Línia de petició mal formada: {lines[0]}")

        method = first_line_parts[0].upper()
        path = first_line_parts[1]
        version = first_line_parts[2] if len(first_line_parts) > 2 else "HTTP/1.1"

        headers: dict[str, str] = {}
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
            body=None,
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
