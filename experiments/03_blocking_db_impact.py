"""
Experiment 03: Impacte de la BD SÍNCRONA sobre l'event loop.

Arrenca el servidor real (ClientConnectionHandler) amb un Router fals que tarda
un temps fix per petició (time.sleep, com una consulta amb psycopg2) i hi llança
10 clients alhora. El Router es crida directament, igual que al servidor real.

  - Consulta ràpida (2 ms, com les nostres en local): el bloqueig no es nota.
  - Consulta lenta (200 ms): les peticions van en fila i el temps es multiplica per 10.

Execució:  python experiments/03_blocking_db_impact.py
No necessita PostgreSQL.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.src.protocol.http_client import encode_request  # noqa: E402
from server.src.network import ClientConnectionHandler  # noqa: E402
from server.src.protocol.response_builder import ResponseBuilder  # noqa: E402

CLIENTS = 10


class FixedDelayRouter:
    """Simula una consulta a la BD que BLOQUEJA el fil durant `query_seconds`."""

    def __init__(self, query_seconds: float) -> None:
        self.query_seconds = query_seconds

    def handle_request(self, request) -> bytes:
        time.sleep(self.query_seconds)
        return ResponseBuilder.ok({"ok": True})


async def one_client(port: int) -> None:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(encode_request("GET", "/dishes", "127.0.0.1", port))
    await writer.drain()
    await reader.read()
    writer.close()
    await writer.wait_closed()


async def measure(query_seconds: float) -> float:
    handler = ClientConnectionHandler(
        FixedDelayRouter(query_seconds), read_timeout=5.0, max_body_size=1024
    )
    server = await asyncio.start_server(handler.handle_client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    async with server:
        start = time.perf_counter()
        await asyncio.gather(*(one_client(port) for _ in range(CLIENTS)))
        return time.perf_counter() - start


async def main() -> None:
    print(f"{CLIENTS} clients simultanis, BD síncrona cridada directament\n")
    for query_seconds in (0.002, 0.2):
        elapsed = await measure(query_seconds)
        print(f"  consulta de {query_seconds * 1000:>3.0f} ms -> total {elapsed:.2f} s")
    print("\n  Total ≈ clients x durada: mentre una consulta s'executa, el loop no atén ningú.")


if __name__ == "__main__":
    asyncio.run(main())
