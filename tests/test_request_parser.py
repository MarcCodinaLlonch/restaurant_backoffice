# test_request_parser.py: Proves unitàries per a la serialització i deserialització del protocol HTTP.

import pytest
from server.src.protocol.request_parser import RequestParser, HttpRequest


def test_parse_get_request():
    """Comprova que una petició GET simple es parseja correctament."""
    raw = (
        b"GET /categories HTTP/1.1\r\n"
        b"Host: localhost:8080\r\n"
        b"Accept: application/json\r\n"
        b"\r\n"
    )
    req = RequestParser.parse_bytes(raw)

    assert req is not None
    assert req.method == "GET"
    assert req.path == "/categories"
    assert req.raw_path == "/categories"
    assert req.version == "HTTP/1.1"
    assert req.headers["host"] == "localhost:8080"
    assert req.headers["accept"] == "application/json"
    assert req.body is None
    assert req.query_params == {}


def test_parse_post_request_with_json_body():
    """Comprova que una petició POST amb cos JSON i capçaleres es deserialitza a diccionari Python."""
    raw = (
        b"POST /categories HTTP/1.1\r\n"
        b"Host: localhost:8080\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 29\r\n"
        b"\r\n"
        b'{"category_name": "Postres"}'
    )
    req = RequestParser.parse_bytes(raw)

    assert req is not None
    assert req.method == "POST"
    assert req.raw_path == "/categories"
    assert req.body == {"category_name": "Postres"}


def test_parse_query_parameters():
    """Comprova que els query parameters de la URL s'extreuen correctament."""
    raw = (
        b"GET /sales?date=2026-10-11&page=2 HTTP/1.1\r\n"
        b"Host: localhost:8080\r\n"
        b"\r\n"
    )
    req = RequestParser.parse_bytes(raw)

    assert req is not None
    assert req.raw_path == "/sales"
    assert req.query_params["date"] == "2026-10-11"
    assert req.query_params["page"] == "2"


def test_parse_empty_or_invalid_request():
    """Comprova que peticions buides o sense format retornen None."""
    assert RequestParser.parse_bytes(b"") is None
    assert RequestParser.parse_bytes(b"HELLO") is None
