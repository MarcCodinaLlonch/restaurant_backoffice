# test_request_parser.py: Proves de la deserialització del protocol (bytes -> HttpRequest).

import pytest

from server.src.protocol.errors import ProtocolError
from server.src.protocol.request_parser import RequestParser


def test_parse_head_get_request():
    """Una petició GET simple es converteix en un HttpRequest correcte."""
    head = b"GET /categories HTTP/1.1\r\nHost: localhost:8088\r\nAccept: application/json\r\n\r\n"
    request = RequestParser.parse_head(head)

    assert request.method == "GET"
    assert request.raw_path == "/categories"
    assert request.version == "HTTP/1.1"
    assert request.headers["host"] == "localhost:8088"
    assert request.body is None
    assert request.query_params == {}


def test_parse_head_extracts_query_parameters():
    """Els paràmetres de la URL (?date=...&page=...) s'extreuen correctament."""
    request = RequestParser.parse_head(b"GET /sales?date=2026-10-11&page=2 HTTP/1.1\r\n\r\n")

    assert request.raw_path == "/sales"
    assert request.query_params == {"date": "2026-10-11", "page": "2"}


def test_parse_body_json():
    """Un cos JSON es converteix en un diccionari de Python."""
    body = RequestParser.parse_body(b'{"category_name": "Postres"}', "application/json")
    assert body == {"category_name": "Postres"}


def test_parse_body_empty_returns_none():
    """Un cos buit es representa amb None."""
    assert RequestParser.parse_body(b"", "application/json") is None


@pytest.mark.parametrize("head", [b"", b"\r\n\r\n", b"HELLO\r\n\r\n"])
def test_parse_head_invalid_raises_protocol_error(head: bytes):
    """Una línia de petició buida o mal formada llança ProtocolError."""
    with pytest.raises(ProtocolError):
        RequestParser.parse_head(head)
