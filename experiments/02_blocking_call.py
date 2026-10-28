"""
Experiment 02: Non-blocking (asyncio.sleep) vs Blocking Call (time.sleep)
Demostra visualment amb un 'heartbeat' com una crida bloquejant tradicional
atura completament l'Event Loop i impedeix l'execució de qualsevol altra tasca.
"""
import asyncio
import time


async def heartbeat(stop_event: asyncio.Event) -> None:
    """Tasca que batega cada 0.2 segons per demostrar si el loop està viu."""
    while not stop_event.is_set():
        print(f"  [Heartbeat {time.strftime('%X')}] L'Event Loop està lliure i actiu...")
        await asyncio.sleep(0.2)


async def async_worker(worker_id: int) -> None:
    print(f"Worker {worker_id} iniciant feina asíncrona (cedeix el control amb await)...")
    await asyncio.sleep(1.0)
    print(f"Worker {worker_id} ha finalitzat!")


def blocking_worker(worker_id: int) -> None:
    print(f"Worker {worker_id} iniciant feina BLOQUEJANT (time.sleep)... ATENCIÓ!")
    time.sleep(1.0)  # Simula una operació síncrona com una consulta SQL a PostgreSQL
    print(f"Worker {worker_id} ha desbloquejat el fil!")


async def run_non_blocking_demo() -> None:
    print("\n--- 1. Prova NO BLOQUEJANT (Cooperativa) ---")
    stop_heartbeat = asyncio.Event()
    heartbeat_task = asyncio.create_task(heartbeat(stop_heartbeat))

    # Tres tasques asíncrones que cedeixen el torn amistosament
    await asyncio.gather(
        async_worker(1),
        async_worker(2),
        async_worker(3),
    )

    stop_heartbeat.set()
    await heartbeat_task


async def run_blocking_demo() -> None:
    print("\n--- 2. Prova BLOQUEJANT (Congelació del Loop) ---")
    stop_heartbeat = asyncio.Event()
    heartbeat_task = asyncio.create_task(heartbeat(stop_heartbeat))

    # Tasca 1 és asíncrona, però Tasca 2 crida codi bloquejant directament al loop
    async def bad_coroutine():
        blocking_worker(2)

    await asyncio.gather(
        async_worker(1),
        bad_coroutine(),
        async_worker(3),
    )

    stop_heartbeat.set()
    await heartbeat_task


async def main() -> None:
    await run_non_blocking_demo()
    await run_blocking_demo()


if __name__ == "__main__":
    asyncio.run(main())