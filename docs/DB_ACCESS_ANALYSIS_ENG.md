# Analysis of the Impact of Synchronous DB Operations on the Event Loop

> **Language:** [English](DB_ACCESS_ANALYSIS_ENG.md) | [Català](DB_ACCESS_ANALYSIS_CAT.md)

The assignment states that database access may remain synchronous, but students must analyse the impact of blocking database operations on the event loop. This document presents that analysis and justifies the design decision taken.

---

## 1. The problem

asyncio uses **a single thread** (the event loop) for all clients.
- When a Task executes `await` (for example, `await reader.readuntil(...)`), it yields control and the loop serves another Task.
- A query with SQLAlchemy + `psycopg2` is **synchronous**: the thread waits for the response from PostgreSQL **without yielding control**.
- **Consequence:** while the query runs, no other client makes progress. If a query took 200 ms, during those 200 ms the server would be stalled for everyone.

---

## 2. The decision: calling the DB directly

```python
# connection_handler.py
logger.info("%s %s from %s", request.method, request.raw_path, client_address)
# KEY: the Router (and the DB) is synchronous and is called directly, without await.
return self._router.handle_request(request)
```

Why this is a good decision for this application:
- **What is truly slow is the network, not the DB.** A client that takes time to send a request, or sends nothing at all, is the case that blocked Practice 1. Network I/O is done with `await` (`readuntil`, `readexactly`, `drain`), so a slow client never stalls the others.
- **Queries are short**, taking only a few milliseconds locally. The blocking exists, but it is imperceptible (see Section 3).
- **The business layer and persistence from Practice 1 remain completely unchanged.** This directly satisfies *"maintain the existing business rules and service layer"*.
- **Two requests never touch the DB at the same time**: the Router runs to completion without any `await`. There are no threads, no race conditions, and nothing to synchronize.
- **It is the simplest code:** there is no intermediate layer between the network handler and the Router.

---

## 3. Experimental evidence

The experiment `experiments/03_blocking_db_impact.py` starts the real server (`ClientConnectionHandler`) with a fake Router that blocks the thread for a fixed duration (`time.sleep`, just like a `psycopg2` query), and launches **10 clients at once**. It does not require PostgreSQL:

```bash
python experiments/03_blocking_db_impact.py
```

| Query duration | Total time (10 clients) | Meaning |
|---|---|---|
| **2 ms** (like our local queries) | **~0.03 s** | The blocking is not noticeable. |
| **200 ms** (slow or remote DB) | **~2.01 s** | Requests run one after another: 10 × 0.2 s. |

**Conclusion:** total time is approximately *clients × query duration*. With short queries, this is negligible. If the database were slow, it would become a bottleneck.

The experiment `experiments/02_blocking_call.py` shows this from another angle: a *heartbeat* coroutine that stops ticking while a blocking call is running.

---

## 4. Alternatives (if the DB were slow)

| Option | How it works | Cost |
|---|---|---|
| **1. Synchronous DB called directly (ours)** | The Router runs inside the event loop | The loop blocks during each query (a few ms) |
| 2. `asyncio.to_thread(router.handle_request, request)` | The query runs in a *ThreadPool* worker thread | Introduces threads, the GIL, and a concurrency limit |
| 3. Asynchronous SQLAlchemy + `asyncpg` (optional challenge) | Every query is an `await` (`AsyncSession`) | "Async is contagious": Repositories, Unit of Work, Services, and Router must become `async def`. Relationships must be eagerly loaded (`lazy="selectin"`) to avoid `MissingGreenlet` errors. |

For this application, with short local queries, Option 1 produces the same practical result as the other two with much less code. **If the DB were remote or slow, the next step would be Option 3**, as it eliminates blocking without using threads.
