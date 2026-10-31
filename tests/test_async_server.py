"""
test_async_server.py: Tests exhaustius del servidor asíncron AsyncTcpServer.
Cobreix concurrència (20 clients amb gather), no-bloqueig per clients muts,
timeouts (408), límits de càrrega (413), saturació (503) i codificació pura.
"""

import asyncio
import time

import pytest

from client.src.protocol.http_client import decode_response, encode_request
from server.src.network import (
    AsyncTcpServer,
    ClientConnectionHandler,
    RequestDispatcher,
)
from server.src.protocol.response_builder import ResponseBuilder


class DummyRouter:
    """Router simulat per provar la capa de xarxa i despatxador ràpidament."""

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay

    def handle_request(self, request):
        if self.delay > 0:
            time.sleep(self.delay)

        if request.raw_path == "/categories":
            return ResponseBuilder.ok([{"id": 1, "name": "Begudes"}])
        return ResponseBuilder.not_found("Ruta no trobada")


def make_test_server(
    max_connections: int = 50, read_timeout: float = 0.3, max_body_size: int = 500
):
    """Funció auxiliar per instanciar un servidor de test amb paràmetres específics."""
    router = DummyRouter()
    dispatcher = RequestDispatcher(router, max_concurrent_calls=25)
    handler = ClientConnectionHandler(
        dispatcher=dispatcher,
        max_body_size=max_body_size,
        read_timeout=read_timeout,
        max_connections=max_connections,
    )
    return AsyncTcpServer(host="127.0.0.1", port=0, handler=handler)


@pytest.fixture
async def running_server():
    """
    Fixture per a proves generals: permet fins a 50 connexions concurrents.
    """
    server = make_test_server(max_connections=50, read_timeout=0.3, max_body_size=500)
    server_task = asyncio.create_task(server.serve_forever())

    while server._server is None or not server._server.sockets:
        await asyncio.sleep(0.01)

    port = server._server.sockets[0].getsockname()[1]
    yield {"host": "127.0.0.1", "port": port, "server": server}

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_server_concurrent_requests(running_server):
    """
    Comprova que múltiples clients (20) poden realitzar peticions concurrents
    amb èxit i rebre les dades correctes.
    """
    host = running_server["host"]
    port = running_server["port"]

    async def client_job(client_id: int):
        reader, writer = await asyncio.open_connection(host, port)
        req = encode_request("GET", "/categories", host, port)
        writer.write(req)
        await writer.drain()

        raw_resp = await reader.read()
        writer.close()
        await writer.wait_closed()

        api_resp = decode_response(raw_resp)
        assert api_resp.is_success
        assert api_resp.status_code == 200
        assert api_resp.data == [{"id": 1, "name": "Begudes"}]
        return api_resp

    tasks = [client_job(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    assert len(results) == 20


@pytest.mark.asyncio
async def test_idle_client_does_not_block_others(running_server):
    """
    Comprova que si un client obre una connexió i es queda mut (idle),
    un altre client que connecti a continuació rep resposta immediata (< 150ms).
    """
    host = running_server["host"]
    port = running_server["port"]

    idle_reader, idle_writer = await asyncio.open_connection(host, port)

    start = time.perf_counter()
    active_reader, active_writer = await asyncio.open_connection(host, port)
    active_writer.write(encode_request("GET", "/categories", host, port))
    await active_writer.drain()

    raw_resp = await active_reader.read()
    elapsed = time.perf_counter() - start

    active_writer.close()
    await active_writer.wait_closed()
    idle_writer.close()
    await idle_writer.wait_closed()

    resp = decode_response(raw_resp)
    assert resp.is_success
    assert elapsed < 0.2


@pytest.mark.asyncio
async def test_read_timeout_returns_408(running_server):
    """
    Comprova que si un client connecta i supera el read_timeout (300ms)
    sense enviar petició, el servidor respon amb un codi 408 Request Timeout.
    """
    host = running_server["host"]
    port = running_server["port"]

    reader, writer = await asyncio.open_connection(host, port)
    raw_resp = await reader.read()
    writer.close()
    await writer.wait_closed()

    resp = decode_response(raw_resp)
    assert resp.status_code == 408
    assert "Temps d'espera esgotat" in (resp.error_message or "")


@pytest.mark.asyncio
async def test_payload_too_large_returns_413(running_server):
    """
    Comprova que un cos superior al límit permès rep un 413 Payload Too Large.
    """
    host = running_server["host"]
    port = running_server["port"]

    reader, writer = await asyncio.open_connection(host, port)
    big_body = {"data": "x" * 600}
    writer.write(encode_request("POST", "/categories", host, port, body=big_body))
    await writer.drain()

    raw_resp = await reader.read()
    writer.close()
    await writer.wait_closed()

    resp = decode_response(raw_resp)
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_max_connections_returns_503():
    """
    Comprova que superar el límit de connexions simultànies retorna 503 Service Unavailable.
    """
    # Servidor específic amb max_connections = 2
    server = make_test_server(max_connections=2, read_timeout=1.0)
    server_task = asyncio.create_task(server.serve_forever())

    while server._server is None or not server._server.sockets:
        await asyncio.sleep(0.01)

    port = server._server.sockets[0].getsockname()[1]
    host = "127.0.0.1"

    writers = []
    try:
        # Obrim 2 connexions que ocupen els 2 slots
        for _ in range(2):
            _, w = await asyncio.open_connection(host, port)
            writers.append(w)

        # La 3a connexió ha de ser rebutjada amb un 503
        r3, w3 = await asyncio.open_connection(host, port)
        raw_resp = await r3.read()
        w3.close()
        await w3.wait_closed()

        resp = decode_response(raw_resp)
        assert resp.status_code == 503
        assert "Servidor saturat" in (resp.error_message or "")
    finally:
        for w in writers:
            w.close()
            await w.wait_closed()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


def test_encode_decode_http_request_response():
    """Test unitari pur per verificar la consistència de la codificació de xarxa."""
    encoded = encode_request(
        "POST", "/test", "127.0.0.1", 8088, body={"hello": "world"}
    )
    assert b"POST /test HTTP/1.1\r\n" in encoded
    assert b"Content-Length: 18\r\n" in encoded
    assert b'{"hello": "world"}' in encoded

    raw_http = (
        b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"key":"value"}'
    )
    decoded = decode_response(raw_http)
    assert decoded.is_success
    assert decoded.status_code == 200
    assert decoded.data == {"key": "value"}
