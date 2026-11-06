# test_response_builder.py: Proves unitàries per al ResponseBuilder.

import json

from common.domain.entities import CategoryEntity
from server.src.protocol.response_builder import ResponseBuilder


def test_build_ok_response():
    """Verifica que ok() genera status 200, capçaleres i cos JSON en format bytes."""
    data = {"id": 1, "nom": "Amanides"}
    resp_bytes = ResponseBuilder.ok(data)

    assert resp_bytes.startswith(b"HTTP/1.1 200 OK\r\n")
    assert b"Content-Type: application/json; charset=utf-8\r\n" in resp_bytes
    assert b"\r\n\r\n" in resp_bytes

    body = resp_bytes.split(b"\r\n\r\n")[1].decode("utf-8")
    assert json.loads(body) == data


def test_build_created_response():
    """Verifica que created() genera status 201."""
    resp_bytes = ResponseBuilder.created({"id": 5})
    assert resp_bytes.startswith(b"HTTP/1.1 201 Created\r\n")


def test_build_no_content_response():
    """Verifica que no_content() genera 204 sense cos i Content-Length 0."""
    resp_bytes = ResponseBuilder.no_content()
    assert resp_bytes.startswith(b"HTTP/1.1 204 No Content\r\n")
    assert b"Content-Length: 0\r\n" in resp_bytes


def test_build_bad_request_response():
    """Verifica que bad_request() retorna 400 amb el missatge d'error."""
    resp_bytes = ResponseBuilder.bad_request("Nom invàlid")
    assert resp_bytes.startswith(b"HTTP/1.1 400 Bad Request\r\n")
    body = resp_bytes.split(b"\r\n\r\n")[1].decode("utf-8")
    assert json.loads(body) == {"error": "Nom invàlid"}


def test_build_not_found_response():
    """Verifica que not_found() retorna 404."""
    resp_bytes = ResponseBuilder.not_found("Categoria no existeix")
    assert resp_bytes.startswith(b"HTTP/1.1 404 Not Found\r\n")


def test_serialize_domain_entities():
    """Verifica que els objectes del domini amb to_dict() es serialitzen correctament."""
    entity = CategoryEntity(id=10, category_name="Tapes")
    resp_bytes = ResponseBuilder.ok(entity)

    body = resp_bytes.split(b"\r\n\r\n")[1].decode("utf-8")
    parsed = json.loads(body)
    assert parsed["id"] == 10
    assert parsed["category_name"] == "Tapes"
