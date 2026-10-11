# test_router.py: Proves unitàries del mecanisme d'enrutament (Router).

import json
from unittest.mock import MagicMock
import pytest

from common.domain.entities import CategoryEntity
from server.src.protocol.request_parser import HttpRequest
from server.src.protocol.router import Router


@pytest.fixture
def mock_router():
    """Crea una instància de Router amb tots els serveis simulats."""
    cat_svc = MagicMock()
    al_svc = MagicMock()
    dish_svc = MagicMock()
    emp_svc = MagicMock()
    menu_svc = MagicMock()
    sale_svc = MagicMock()

    router = Router(
        category_service=cat_svc,
        allergen_service=al_svc,
        dish_service=dish_svc,
        employee_service=emp_svc,
        menu_service=menu_svc,
        sale_service=sale_svc,
    )
    return router, cat_svc, dish_svc


def test_router_get_categories(mock_router):
    """Comprova que GET /categories crida a CategoryService.get_all()."""
    router, cat_svc, _ = mock_router
    cat_svc.get_all.return_value = [CategoryEntity(id=1, category_name="Carns")]

    req = HttpRequest(
        method="GET",
        path="/categories",
        raw_path="/categories",
        version="HTTP/1.1"
    )

    resp_bytes = router.handle_request(req)
    assert resp_bytes.startswith(b"HTTP/1.1 200 OK")
    body = json.loads(resp_bytes.split(b"\r\n\r\n")[1].decode("utf-8"))
    assert len(body) == 1
    assert body[0]["category_name"] == "Carns"
    cat_svc.get_all.assert_called_once()


def test_router_post_categories(mock_router):
    """Comprova que POST /categories delega a CategoryService.create()."""
    router, cat_svc, _ = mock_router
    cat_svc.create.return_value = CategoryEntity(id=3, category_name="Peix")

    req = HttpRequest(
        method="POST",
        path="/categories",
        raw_path="/categories",
        version="HTTP/1.1",
        body={"category_name": "Peix"}
    )

    resp_bytes = router.handle_request(req)
    assert resp_bytes.startswith(b"HTTP/1.1 201 Created")
    cat_svc.create.assert_called_once_with("Peix")


def test_router_handles_value_error_as_bad_request(mock_router):
    """Comprova que si el servei llença un ValueError, el Router retorna 400 Bad Request."""
    router, cat_svc, _ = mock_router
    cat_svc.create.side_effect = ValueError("El nom no pot estar buit.")

    req = HttpRequest(
        method="POST",
        path="/categories",
        raw_path="/categories",
        version="HTTP/1.1",
        body={"category_name": ""}
    )

    resp_bytes = router.handle_request(req)
    assert resp_bytes.startswith(b"HTTP/1.1 400 Bad Request")
    body = json.loads(resp_bytes.split(b"\r\n\r\n")[1].decode("utf-8"))
    assert body["error"] == "El nom no pot estar buit."


def test_router_unknown_route_returns_404(mock_router):
    """Comprova que una ruta desconeguda retorna 404 Not Found."""
    router, _, _ = mock_router
    req = HttpRequest(
        method="GET",
        path="/ruta_inexistent",
        raw_path="/ruta_inexistent",
        version="HTTP/1.1"
    )

    resp_bytes = router.handle_request(req)
    assert resp_bytes.startswith(b"HTTP/1.1 404 Not Found")
