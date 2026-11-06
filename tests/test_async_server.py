"""
test_async_server.py: Proves del servidor asíncron amb clients TCP REALS.

Cada test arrenca un servidor amb asyncio.start_server (com a server.py) en un
port lliure (port 0) i hi connecta clients reals amb asyncio.open_connection.
El Router és simulat (FakeRouter) per no dependre de PostgreSQL.
"""

import asyncio
import time

import pytest

from client.src.protocol.http_client import HttpClient, decode_response, encode_request
from server.src.network import ClientConnectionHandler, RequestDispatcher
from server.src.protocol.response_builder import ResponseBuilder

HOST = "127.0.0.1"


class FakeRouter:
    """Substitueix el Router real. `delay` simula una consulta lenta (bloquejant) a la BD."""

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay

    def handle_request(self, request) -> bytes:
        time.sleep(self.delay)  # Bloquejant a propòsit, com psycopg2.
        if request.raw_path == "/categories":
            return ResponseBuilder.ok([{"id": 1, "category_name": "Begudes"}])
        if request.raw_path == "/crash":
            raise RuntimeError("Simulated unexpected failure")
        return ResponseBuilder.not_found("Route not found")


async def start_test_server(
    delay: float = 0.0, max_connections: int = 50, read_timeout: float = 0.5
) -> tuple[asyncio.Server, int]:
    """Arrenca un servidor de prova i retorna (servidor, port)."""
    dispatcher = RequestDispatcher(FakeRouter(delay), max_concurrent_calls=10)
    handler = ClientConnectionHandler(
        dispatcher=dispatcher,
        read_timeout=read_timeout,
        max_body_size=500,
        max_connections=max_connections,
    )
    server = await asyncio.start_server(handler.handle_client, HOST, 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


async def send_raw(port: int, data: bytes) -> bytes:
    """Client mínim: envia bytes, llegeix fins que el servidor tanca, i tanca."""
    reader, writer = await asyncio.open_connection(HOST, port)
    try:
        writer.write(data)
        await writer.drain()
        return await reader.read()
    finally:
        writer.close()
        await writer.wait_closed()


async def get(port: int, path: str) -> int:
    """Fa un GET i retorna el codi d'estat HTTP."""
    raw = await send_raw(port, encode_request("GET", path, HOST, port))
    return decode_response(raw).status_code


@pytest.fixture
async def server_port():
    server, port = await start_test_server()
    async with server:
        yield port


async def test_twenty_clients_are_served_concurrently(server_port: int):
    statuses = await asyncio.gather(*(get(server_port, "/categories") for _ in range(20)))
    assert statuses == [200] * 20


async def test_idle_client_does_not_block_others(server_port: int):
    _, idle_writer = await asyncio.open_connection(HOST, server_port)  # no envia res
    start = time.perf_counter()
    assert await get(server_port, "/categories") == 200
    assert time.perf_counter() - start < 0.2
    idle_writer.close()
    await idle_writer.wait_closed()


async def test_blocking_database_does_not_freeze_the_server():
    """5 peticions de 0,3 s: si la BD bloquegés el loop trigarien 1,5 s; amb to_thread ~0,3 s."""
    server, port = await start_test_server(delay=0.3)
    async with server:
        start = time.perf_counter()
        statuses = await asyncio.gather(*(get(port, "/categories") for _ in range(5)))
        elapsed = time.perf_counter() - start
    assert statuses == [200] * 5
    assert elapsed < 0.8


async def test_client_disconnecting_mid_request_does_not_stop_server(server_port: int):
    _, writer = await asyncio.open_connection(HOST, server_port)
    writer.write(b'POST /categories HTTP/1.1\r\nContent-Length: 50\r\n\r\n{"incompl')
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    assert await get(server_port, "/categories") == 200


async def test_unexpected_error_only_affects_that_client(server_port: int):
    """Si atendre un client llança una excepció inesperada, només falla la seva Task."""
    await send_raw(server_port, encode_request("GET", "/crash", HOST, server_port))
    assert await get(server_port, "/categories") == 200  # el servidor continua viu


async def test_read_timeout_returns_408(server_port: int):
    reader, writer = await asyncio.open_connection(HOST, server_port)
    response = decode_response(await reader.read())  # no enviem res i esperem
    writer.close()
    await writer.wait_closed()
    assert response.status_code == 408


async def test_malformed_request_returns_400(server_port: int):
    response = decode_response(await send_raw(server_port, b"HELLO\r\n\r\n"))
    assert response.status_code == 400


async def test_body_too_large_returns_413(server_port: int):
    request = encode_request("POST", "/categories", HOST, server_port, {"x": "a" * 600})
    assert decode_response(await send_raw(server_port, request)).status_code == 413


async def test_too_many_connections_returns_503():
    server, port = await start_test_server(max_connections=2, read_timeout=1.0)
    async with server:
        idle_writers = [(await asyncio.open_connection(HOST, port))[1] for _ in range(2)]
        reader, writer = await asyncio.open_connection(HOST, port)
        response = decode_response(await reader.read())
        for w in [*idle_writers, writer]:
            w.close()
            await w.wait_closed()
    assert response.status_code == 503


async def test_interactive_sync_client_works_unchanged(server_port: int):
    """El HttpClient de la P1 (sockets bloquejants) funciona igual: el protocol no ha canviat.
    El cridem amb to_thread perquè és bloquejant i no volem aturar l'event loop del test."""
    client = HttpClient(host=HOST, port=server_port, timeout=2.0)
    response = await asyncio.to_thread(client.get, "/categories")
    assert response.is_success
    assert response.data == [{"id": 1, "category_name": "Begudes"}]


def test_encode_and_decode_are_consistent():
    encoded = encode_request("POST", "/test", HOST, 8088, body={"hello": "world"})
    assert encoded.startswith(b"POST /test HTTP/1.1\r\n")
    assert b"Content-Length: 18\r\n" in encoded
    decoded = decode_response(b'HTTP/1.1 200 OK\r\nContent-Length: 15\r\n\r\n{"key":"value"}')
    assert decoded.status_code == 200
    assert decoded.data == {"key": "value"}
