# Multi-Client Demonstration Guide: Restaurant BackOffice v3.0.0

> **Language:** [English](DEMO_ENG.md) | [Català](DEMO_CAT.md)

A **reproducible** step-by-step guide to verify that the server serves multiple clients concurrently, and to evaluate its performance gains over Practice 1.

Commands are written for **Linux/macOS** (bash), with **Windows** variants indicated alongside in comments. Commands using `python ...` run identically on both platforms.

## Preparation (one-time setup)

```bash
docker compose up -d                 # PostgreSQL
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Demo 1: P1 vs P2: Idle ("Silent") Client Blocks P1 but Not P2 ⭐

The most conclusive demonstration: running **the exact same load-test client** against both servers.

```bash
# Prepare a temporary worktree of the P1 server (tag v2.0.0) next to the project
git worktree add ../p1_server v2.0.0
cp .env ../p1_server/.env            # Windows: copy .env ..\p1_server\.env
```

**a) P1 Server** (Terminal 1):
```bash
cd ../p1_server && python server/server.py      # Windows: cd ..\p1_server ; python server\server.py
```
Terminal 2 (from the P2 repository directory):
```bash
python client/load_test_client.py --clients 5 --idle-clients 1
```
→ **~3 s**: The P1 server blocks at `recv()` waiting for the idle client, forcing the other 5 to wait in a queue.

**b) P2 Server:** Stop P1 (Ctrl+C). In Terminal 1, return to the P2 repository and run `python server/server.py`. Re-run the same client command in Terminal 2.
→ **< 0.1 s**: Each client is handled in its own Task, so the idle client does not impede anyone else.

When done with the P1 copy: `git worktree remove ../p1_server`.

## Demo 2: Three Concurrent Terminals (Interactive Clients)

| Terminal | Command |
|---|---|
| 1 | `python server/server.py` |
| 2 | `python client/client.py` → Dish Management → List All |
| 3 | `python client/client.py` → Category Management → Add New |

Terminal 1's server logs will display both connections simultaneously, with independent remote ports and the active counter `active: N`.
To see this even more clearly, while clients are working, open a 4th terminal with a silent client:
```bash
python -c "import socket,time; s=socket.create_connection(('127.0.0.1',8088)); time.sleep(10)"
```
Interactive clients keep working smoothly. After 5 s, the server logs a `Read timeout` and sends a **408** to the silent client.

## Demo 3: Automated Load Testing: Concurrent vs Sequential

```bash
python client/load_test_client.py --clients 30
python client/load_test_client.py --clients 30 --sequential
python client/load_test_client.py --clients 30 --idle-clients 3
```
With fast local queries, latency differences between concurrent and sequential modes are small. **The real benefit of concurrency emerges when wait times exist** (slow clients or slow DB I/O), as demonstrated by Demo 1 and Demo 4.

Measured benchmark data (`docs/evidence/04_load_concurrent_vs_sequential.txt`):

| Database | Concurrent | Sequential | Explanation |
|---|---|---|---|
| PostgreSQL | ~0.45 s | ~0.69 s | Each query waits on network I/O: while one worker thread waits, others proceed |
| SQLite | ~0.41 s | ~0.29–0.36 s | SQLite runs in-process (CPU + GIL): no I/O wait to overlap, threads add overhead |

## Demo 4: Impact of Blocking Database I/O (No Docker Needed)

```bash
python experiments/03_blocking_vs_offloaded.py
```
10 clients, each query simulating a 0.2 s delay: **inline ≈ 2 s** (queued sequentially) vs **to_thread ≈ 0.2–0.4 s** (overlapped in worker threads).

## Demo 5: Server Robustness and Graceful Shutdown

- Malformed request → **400 Bad Request**, server keeps running without crashing:
  `python -c "import socket; s=socket.create_connection(('127.0.0.1',8088)); s.sendall(b'HELLO\r\n\r\n'); print(s.recv(200))"`
- **Ctrl+C** on the server → `Server stopped, resources released` without tracebacks.

## Demo 6: Automated Test Suite

```bash
pytest -v
```
`tests/test_async_server.py` spins up a real server and connects real TCP clients: 20 concurrent clients, an idle client, a slow database, mid-request disconnection, unexpected exceptions, and status codes 408/400/413/503. `tests/test_persistence.py` verifies database persistence using SQLite.

## Saved Benchmark Evidence

The raw output for each demo run is preserved in `docs/evidence/` (`*.txt`), alongside screenshots (`*.png`).

Text evidence files were generated using SQLite (no Docker container required) with these environment variables:
```bash
ENVIRONMENT=test DB_URL_TESTS=sqlite:///demo.db SERVER_PORT=8099
```
