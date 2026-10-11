# test_client_server_integration.py: Prova d'integració Client-Servidor sobre TCP real.

import time
import socket
import threading
from unittest.mock import MagicMock
import pytest

from common.domain.entities import CategoryEntity
from client.src.protocol.http_client import HttpClient
from server.src.protocol.router import Router
from server.src.protocol.request_parser import RequestParser
from server.src.protocol.response_builder import ResponseBuilder


def run_test_server(server_sock, router, stop_event):
    """Bucle del servidor de proves."""
    server_sock.settimeout(0.5)
    while not stop_event.is_set():
        try:
            client_sock, _ = server_sock.accept()
            req = RequestParser.parse_from_socket(client_sock)
            if req:
                resp_bytes = router.handle_request(req)
            else:
                resp_bytes = ResponseBuilder.bad_request("Error")
            client_sock.sendall(resp_bytes)
            client_sock.close()
        except socket.timeout:
            continue
        except Exception:
            break


def test_client_server_tcp_communication():
    """Comprova la comunicació completa per xarxa TCP entre HttpClient i el Servidor."""
    # Cerquem un port lliure del sistema
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    port = server_sock.getsockname()[1]
    server_sock.listen(1)

    # Simulem els serveis
    cat_svc = MagicMock()
    cat_svc.get_all.return_value = [CategoryEntity(id=1, category_name="Tapes")]
    cat_svc.create.return_value = CategoryEntity(id=2, category_name="Begudes")

    router = Router(
        category_service=cat_svc,
        allergen_service=MagicMock(),
        dish_service=MagicMock(),
        employee_service=MagicMock(),
        menu_service=MagicMock(),
        sale_service=MagicMock(),
    )

    stop_event = threading.Event()
    th = threading.Thread(target=run_test_server, args=(server_sock, router, stop_event), daemon=True)
    th.start()

    try:
        client = HttpClient(host="127.0.0.1", port=port, timeout=2.0)

        # 1. Prova GET
        resp_get = client.get("/categories")
        assert resp_get.is_success
        assert resp_get.status_code == 200
        assert len(resp_get.data) == 1
        assert resp_get.data[0]["category_name"] == "Tapes"

        # 2. Prova POST
        resp_post = client.post("/categories", {"category_name": "Begudes"})
        assert resp_post.is_success
        assert resp_post.status_code == 201
        assert resp_post.data["category_name"] == "Begudes"

        # 3. Prova 404
        resp_404 = client.get("/recurs_inexistent")
        assert not resp_404.is_success
        assert resp_404.status_code == 404

    finally:
        stop_event.set()
        server_sock.close()
        th.join(timeout=1.0)
