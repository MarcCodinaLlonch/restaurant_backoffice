# Analysis of Blocking Database Operations on the AsyncIO Event Loop

> **Language:** [English](DB_ACCESS_ANALYSIS_ENG.md) | [Català](DB_ACCESS_ANALYSIS_CAT.md)

This document presents the technical analysis on the coexistence of the AsyncIO Event Loop and synchronous database queries (SQLAlchemy + `psycopg2`), as required by the assignment specification.

---

## 1. The Theoretical Problem

The **AsyncIO** architecture is built on cooperative multitasking over a **single execution thread**.
- Every time a coroutine invokes `await`, it yields control back to the **Event Loop** so that other tasks can execute CPU or I/O work.
- When a traditional synchronous blocking call is made (such as `session.query(Dish).all()` via SQLAlchemy and the `psycopg2` driver), the C-level TCP socket driver waits for PostgreSQL's response at the operating system socket level without yielding control to the Event Loop.
- **Consequence:** The entire Event Loop becomes completely frozen. If a database query takes 200 ms, during that whole interval **no other client can connect, send requests, or receive responses**.

---

## 2. Experimental Evidence (Measured Results)

The experiment script `experiments/03_blocking_vs_offloaded.py` runs the real server (`ClientConnectionHandler`) with a mock Router that blocks the thread for 0.2 s per request (`time.sleep`, simulating a `psycopg2` query) and launches **10 concurrent clients**. It does not require PostgreSQL:

```bash
python experiments/03_blocking_vs_offloaded.py
```

Measured benchmark results (3 runs, 8-core CPU, Python 3.14):

| Execution Mode | Total Duration (10 requests) | Event Loop Behavior |
|---|---|---|
| **inline** (Router called directly inside event loop) | **2.01 s** | Blocked: requests are processed sequentially (10 × 0.2 s) |
| **to_thread** (`RequestDispatcher`) | **0.21 s** | Free: all 10 queries run overlapped across worker threads |

**Observed Speedup:** `to_thread` is approximately **9.5× faster**.

**Thread limits:** `asyncio.to_thread` relies on the loop's default *ThreadPoolExecutor*, which defaults to `min(32, cpu_cores + 4)` threads (12 on an 8-core host). For 10 clients, all requests run fully in parallel (~0.2 s). On a machine with fewer cores (e.g., 4 cores → 8 threads), requests would run in two batches taking ~0.4 s.

---

## 3. Implemented Solution: `RequestDispatcher`

To decouple the asynchronous server from the pre-existing synchronous persistence layer, the **RequestDispatcher** pattern was introduced:

```python
class RequestDispatcher:
    def __init__(self, router: Router, max_concurrent_calls: int) -> None:
        self._router = router
        self._db_slots = asyncio.Semaphore(max_concurrent_calls)

    async def dispatch(self, request: HttpRequest) -> bytes:
        async with self._db_slots:
            return await asyncio.to_thread(self._router.handle_request, request)
```

### Why does it work with Python's GIL?
Python employs a **Global Interpreter Lock (GIL)**, preventing multiple threads from executing Python bytecode simultaneously. However, when an I/O library (such as `psycopg2` issuing network calls to PostgreSQL) awaits an external response, **it explicitly releases the GIL**. This allows multiple worker threads to await database I/O concurrently while AsyncIO's main thread continues serving other network clients.

### Why use an `asyncio.Semaphore`?
The database connection pool has a finite size: SQLAlchemy defaults to `pool_size=5` and `max_overflow=10`, hence `DB_MAX_CONCURRENCY=5`. If 100 clients requested data simultaneously without limits:
1. 100 worker threads would be spawned, contending for the 5 DB connections and causing pool starvation (*ConnectionPoolTimeout*).
2. Memory consumption would spike unnecessarily.
With the semaphore, we enforce a safe concurrency ceiling (`DB_MAX_CONCURRENCY=5`). Additional requests wait their turn **asynchronously and cooperatively** within the Event Loop without wasting system resources.

---

## 4. Comparison of Alternative Approaches

| Criterion | `asyncio.to_thread` + Semaphore (Our Solution) | Pure Async Driver (`asyncpg` + Async SQLAlchemy) |
|---|---|---|
| **Impact on existing codebase** | Minimal (entire domain, services, and repositories remain 100% intact). | Very high (all code must be converted to `async def`, `async with`, `selectinload`). |
| **Thread usage** | Uses an internal worker thread pool (`ThreadPoolExecutor`). | Zero worker threads (pure async event-driven I/O). |
| **Query cancellation** | Not cancellable once the worker thread has started the query. | Native cancellation via coroutine cancellation. |
| **Error risk** | Very low and safe (each transaction owns an isolated session). | Risk of `MissingGreenlet` exceptions due to lazy loading. |

**Conclusion:** The `asyncio.to_thread` pattern combined with a concurrency-limiting semaphore represents the optimal engineering balance for this assignment, delivering performance on par with fully async drivers while strictly maintaining separation of concerns and preserving existing business logic.

---

## 5. Optional Challenge: Researched, Intentionally Not Implemented

### Overview
SQLAlchemy 2.0 provides an asynchronous API: `create_async_engine` + `AsyncSession`, paired with an async driver like `asyncpg` (URL `postgresql+asyncpg://...`). Queries are awaited without worker threads:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine(
    "postgresql+asyncpg://postgres:secret@localhost:5433/restaurant_db_dev"
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async with session_factory() as session:
    result = await session.execute(select(Dish))
```

### Why it was NOT implemented
- **"Async is contagious":** Making repositories `async` forces Unit of Work, all 6 services, and the Router to become `async`. This would require a full rewrite of Practice 1's domain layer.
- **Lazy loading issues:** Accessing relational attributes like `dish.allergens` outside an awaited context triggers `MissingGreenlet`. Every relational query would require explicit `selectinload(...)` options.
- **High complexity, negligible gain:** In this application, database queries are short and the connection pool is sized at 5. `to_thread` delivers virtually identical latency (see Section 2).

### Conclusion
Using `asyncio.to_thread` + `asyncio.Semaphore` ensures the event loop is never blocked, satisfies the requirement to *"maintain the existing service layer"*, and keeps the codebase readable and maintainable.
