"""
Experiment 01: Sequential await vs Concurrent Tasks (asyncio.gather)
Compara el temps d'execució entre cridar dues coroutines seqüencialment
(esperant una darrere l'altra) vs programar-les concurrentment a l'Event Loop.
"""
import asyncio
import time


async def fetch_data(source_name: str, delay_seconds: float) -> str:
    print(f"[{time.strftime('%X')}] Iniciant descàrrega de {source_name}...")
    await asyncio.sleep(delay_seconds)
    print(f"[{time.strftime('%X')}] Finalitzada descàrrega de {source_name} ({delay_seconds}s)")
    return f"Dades de {source_name}"


async def run_sequential() -> None:
    print("\n--- 1. Execució Seqüencial (dos awaits consecutius) ---")
    start = time.perf_counter()
    # Trampa típica: cridar await l'un darrere l'altre NO és concurrent
    result1 = await fetch_data("Font A", 2.0)
    result2 = await fetch_data("Font B", 2.0)
    elapsed = time.perf_counter() - start
    print(f"Resultats: {result1}, {result2}")
    print(f"Temps total seqüencial: {elapsed:.2f} segons (esperat: ~4.0s)")


async def run_concurrent() -> None:
    print("\n--- 2. Execució Concurrent (asyncio.gather) ---")
    start = time.perf_counter()
    # asyncio.gather programa ambdues coroutines com a Tasks dins el mateix loop
    result1, result2 = await asyncio.gather(
        fetch_data("Font A", 2.0),
        fetch_data("Font B", 2.0),
    )
    elapsed = time.perf_counter() - start
    print(f"Resultats: {result1}, {result2}")
    print(f"Temps total concurrent: {elapsed:.2f} segons (esperat: ~2.0s)")


async def main() -> None:
    await run_sequential()
    await run_concurrent()


if __name__ == "__main__":
    asyncio.run(main())