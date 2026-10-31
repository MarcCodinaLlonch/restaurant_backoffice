"""
load_test_client.py: Client de càrrega asíncron per demostrar la concurrència del servidor.
Simula múltiples clients concurrents realitzant peticions simultànies amb asyncio.gather.
"""

import argparse
import asyncio
import os
import sys
import time

# Assegurem la ruta de project_root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from rich.console import Console
from rich.table import Table

from client.src.protocol.http_client import ApiResponse, decode_response, encode_request

console = Console()


async def send_async_request(
    client_id: int,
    host: str,
    port: int,
    method: str,
    path: str,
    body: any = None,
) -> tuple[int, ApiResponse, float]:
    """
    Executa una petició HTTP/1.1 asíncrona utilitzant asyncio.open_connection
    i mesura la latència individual en segons.
    """
    start_time = time.perf_counter()
    try:
        reader, writer = await asyncio.open_connection(host, port)
        request_bytes = encode_request(method, path, host, port, body)
        writer.write(request_bytes)
        await writer.drain()

        # Llegim la resposta completa fins a EOF
        raw_response = await reader.read()
        writer.close()
        await writer.wait_closed()

        latency = time.perf_counter() - start_time
        response = decode_response(raw_response)
        return client_id, response, latency

    except Exception as exc:
        latency = time.perf_counter() - start_time
        return (
            client_id,
            ApiResponse(status_code=500, data=None, error_message=str(exc)),
            latency,
        )


async def idle_client(
    client_id: int, host: str, port: int, hold_seconds: float
) -> None:
    """Simula un client connectat que no envia res per comprovar que no bloqueja els altres."""
    try:
        reader, writer = await asyncio.open_connection(host, port)
        await asyncio.sleep(hold_seconds)
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


async def run_load_test(
    host: str,
    port: int,
    num_clients: int,
    method: str,
    path: str,
    idle_clients: int = 0,
) -> None:
    console.print(
        "\n[bold cyan]==============================================================[/bold cyan]"
    )
    console.print("[bold white] PROVA DE CÀRREGA ASÍNCRONA (AsyncIO)[/bold white]")
    console.print(
        f" Servidor: [yellow]{host}:{port}[/yellow] | Ruta: [green]{method} {path}[/green]"
    )
    console.print(
        f" Clients concurrents: [bold green]{num_clients}[/bold green] | Clients inactius: [bold red]{idle_clients}[/bold red]"
    )
    console.print(
        "[bold cyan]==============================================================[/bold cyan]\n"
    )

    overall_start = time.perf_counter()

    # Tasques concurrents de càrrega
    tasks = [
        send_async_request(i + 1, host, port, method, path) for i in range(num_clients)
    ]

    # Si hi ha clients inactius simultanis
    idle_tasks = [
        idle_client(1000 + i, host, port, hold_seconds=2.0) for i in range(idle_clients)
    ]

    # Llançament concurrent simultani amb asyncio.gather
    results = await asyncio.gather(*(tasks + idle_tasks))
    overall_elapsed = time.perf_counter() - overall_start

    # Filtrem només els resultats dels clients normals
    client_results: list[tuple[int, ApiResponse, float]] = [
        r for r in results if r is not None
    ]

    # Càlcul d'estadístiques
    success_count = sum(1 for _, resp, _ in client_results if resp.is_success)
    failed_count = len(client_results) - success_count
    latencies = [lat for _, _, lat in client_results]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    min_latency = min(latencies) if latencies else 0.0
    max_latency = max(latencies) if latencies else 0.0

    # Taula resum amb Rich
    table = Table(
        title="Resultats de la Prova de Concurrència",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Mètrica", style="bold white", width=30)
    table.add_column("Valor", style="cyan", width=25)

    table.add_row("Clients simultanis sol·licitats", str(num_clients))
    table.add_row(
        "Peticions satisfetes amb èxit (2xx)",
        f"[bold green]{success_count}[/bold green]",
    )
    table.add_row(
        "Peticions fallades",
        f"[bold red]{failed_count}[/bold red]" if failed_count > 0 else "0",
    )
    table.add_row("Temps total transcorregut", f"{overall_elapsed:.3f} s")
    table.add_row("Latència mitjana per client", f"{avg_latency * 1000:.1f} ms")
    table.add_row("Latència mínima", f"{min_latency * 1000:.1f} ms")
    table.add_row("Latència màxima", f"{max_latency * 1000:.1f} ms")
    table.add_row("Throughput estimat", f"{num_clients / overall_elapsed:.1f} req/s")

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="Client de prova de càrrega asíncron.")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host del servidor (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8088, help="Port del servidor (default: 8088)"
    )
    parser.add_argument(
        "--clients",
        type=int,
        default=20,
        help="Nombre de clients concurrents (default: 20)",
    )
    parser.add_argument("--method", default="GET", help="Mètode HTTP (default: GET)")
    parser.add_argument(
        "--path",
        default="/categories",
        help="Ruta de l'endpoint (default: /categories)",
    )
    parser.add_argument(
        "--idle-clients",
        type=int,
        default=2,
        help="Nombre de clients inactius simultanis (default: 2)",
    )

    args = parser.parse_args()

    asyncio.run(
        run_load_test(
            host=args.host,
            port=args.port,
            num_clients=args.clients,
            method=args.method,
            path=args.path,
            idle_clients=args.idle_clients,
        )
    )


if __name__ == "__main__":
    main()
