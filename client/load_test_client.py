"""
load_test_client.py: Llançador automàtic de clients per DEMOSTRAR la concurrència.

Ús:
    python client/load_test_client.py --clients 20                 # 20 clients alhora
    python client/load_test_client.py --clients 20 --sequential    # un darrere l'altre
    python client/load_test_client.py --clients 20 --idle-clients 3

CONCEPTES (diapositives d'asyncio):
- asyncio.open_connection(): client TCP asíncron (StreamReader + StreamWriter).
- asyncio.gather(): llança N coroutines alhora i espera que acabin totes.
- Mode --sequential: "dos await seguits NO són concurrents" -> serveix per comparar temps.
- asyncio.create_task(): els clients inactius s'executen en segon pla mentre fem la prova.
"""

import argparse
import asyncio
import os
import sys
import time

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from client.src.protocol.http_client import decode_response, encode_request  # noqa: E402

console = Console()


async def send_request(host: str, port: int, path: str) -> tuple[int, float]:
    """Un client: connecta, envia un GET, llegeix la resposta. Retorna (codi HTTP, segons)."""
    start = time.perf_counter()
    try:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(encode_request("GET", path, host, port))
        await writer.drain()
        raw_response = await reader.read()  # el servidor tanca en acabar (Connection: close)
        writer.close()
        await writer.wait_closed()
        status_code = decode_response(raw_response).status_code
    except OSError:
        status_code = 0  # no s'ha pogut connectar
    return status_code, time.perf_counter() - start


async def idle_client(host: str, port: int, seconds: float) -> None:
    """Client "mut": connecta i no envia res. Demostra que no bloqueja els altres."""
    _, writer = await asyncio.open_connection(host, port)
    await asyncio.sleep(seconds)
    writer.close()
    await writer.wait_closed()


async def run_load_test(args: argparse.Namespace) -> None:
    # 1. Clients inactius en segon pla (create_task: s'executen mentre continuem).
    idle_tasks = [
        asyncio.create_task(idle_client(args.host, args.port, seconds=3.0))
        for _ in range(args.idle_clients)
    ]
    await asyncio.sleep(0.1)  # ens assegurem que ja estan connectats

    # 2. Clients actius: tots alhora (gather) o un darrere l'altre (await en bucle).
    start = time.perf_counter()
    if args.sequential:
        results = [
            await send_request(args.host, args.port, args.path) for _ in range(args.clients)
        ]
    else:
        results = await asyncio.gather(
            *(send_request(args.host, args.port, args.path) for _ in range(args.clients))
        )
    total_time = time.perf_counter() - start

    await asyncio.gather(*idle_tasks)
    show_results(args, results, total_time)


def show_results(
    args: argparse.Namespace, results: list[tuple[int, float]], total_time: float
) -> None:
    """Mostra un resum en una taula Rich."""
    successes = sum(1 for status, _ in results if 200 <= status < 300)
    latencies = [latency for _, latency in results]
    mode = "SEQÜENCIAL (un darrere l'altre)" if args.sequential else "CONCURRENT (gather)"

    table = Table(title=f"Prova de càrrega — {mode}")
    table.add_column("Mètrica")
    table.add_column("Valor", style="cyan")
    table.add_row("Petició", f"GET {args.path}")
    table.add_row("Clients actius / inactius", f"{args.clients} / {args.idle_clients}")
    table.add_row("Respostes correctes (2xx)", f"{successes} / {len(results)}")
    table.add_row("Temps total", f"{total_time:.3f} s")
    table.add_row("Latència mitjana", f"{sum(latencies) / len(latencies) * 1000:.1f} ms")
    table.add_row("Latència màxima", f"{max(latencies) * 1000:.1f} ms")
    console.print(table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Llançador de clients concurrents.")
    parser.add_argument("--host", default=os.getenv("SERVER_HOST_CLIENT", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", "8088")))
    parser.add_argument("--clients", type=int, default=20)
    parser.add_argument("--path", default="/dishes")
    parser.add_argument("--idle-clients", type=int, default=0)
    parser.add_argument("--sequential", action="store_true")
    asyncio.run(run_load_test(parser.parse_args()))


if __name__ == "__main__":
    main()
