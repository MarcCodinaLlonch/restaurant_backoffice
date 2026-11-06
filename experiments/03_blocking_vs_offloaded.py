"""
Experiment 03: Impacte d'una BD BLOQUEJANT sobre l'event loop.

Arrenca el servidor real (ClientConnectionHandler) amb un Router fals que tarda
0,2 s per petició (time.sleep, com una consulta psycopg2) i hi llança 10 clients alhora.

  - Mode "inline":    el Router s'executa DINS l'event loop  -> les peticions van en fila.
  - Mode "to_thread": el Router s'executa en un fil (RequestDispatcher) -> es solapen.

Execució:  python experiments/03_blocking_vs_offloaded.py
No necessita PostgreSQL.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.src.protocol.http_client import encode_request  # noqa: E402
from server.src.network import ClientConnectionHandler, RequestDispatcher  # noqa: E402
from server.src.protocol.response_builder import ResponseBuilder  # noqa: E402

QUERY_SECONDS = 0.2
CLIENTS = 10


class SlowRouter:
    """Simula una consulta a la BD que BLOQUEJA el fil durant QUERY_SECONDS."""

    def handle_request(self, request) -> bytes:
        time.sleep(QUERY_SECONDS)
        return ResponseBuilder.ok({"ok": True})


class InlineDispatcher:
    """Versió INCORRECTA a propòsit: crida el Router directament dins l'event loop."""

    def __init__(self, router: SlowRouter) -> None:
        self._router = router

    async def dispatch(self, request) -> bytes:
        return self._router.handle_request(request)  # bloqueja tot el loop!


async def one_client(port: int) -> None:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(encode_request("GET", "/dishes", "127.0.0.1", port))
    await writer.drain()
    await reader.read()
    writer.close()
    await writer.wait_closed()


async def measure(dispatcher) -> float:
    handler = ClientConnectionHandler(
        dispatcher, read_timeout=5.0, max_body_size=1024, max_connections=100
    )
    server = await asyncio.start_server(handler.handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        start = time.perf_counter()
        await asyncio.gather(*(one_client(port) for _ in range(CLIENTS)))
        return time.perf_counter() - start


async def main() -> None:
    router = SlowRouter()
    inline_time = await measure(InlineDispatcher(router))
    thread_time = await measure(RequestDispatcher(router, max_concurrent_calls=CLIENTS))

    print(f"{CLIENTS} clients simultanis, cada consulta tarda {QUERY_SECONDS} s\n")
    print(f"  inline    (BD dins l'event loop): {inline_time:.2f} s")
    print(f"  to_thread (BD en un fil):         {thread_time:.2f} s")
    print(f"\n  to_thread és {inline_time / thread_time:.1f} vegades més ràpid")


if __name__ == "__main__":
    asyncio.run(main())
