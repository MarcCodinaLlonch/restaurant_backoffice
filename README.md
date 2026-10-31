# 🍽️ Restaurant BackOffice — v3.0 (AsyncIO Multi-Client Server)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![asyncio](https://img.shields.io/badge/Network-asyncio-orange.svg)](https://docs.python.org/3/library/asyncio.html)
[![Rich](https://img.shields.io/badge/CLI-Rich-blueviolet.svg)](https://rich.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-47%20passing-brightgreen.svg)](https://docs.pytest.org/)
[![Ruff](https://img.shields.io/badge/PEP%208-ruff-black.svg)](https://docs.astral.sh/ruff/)

> 🌐 **Language:** **English (README.md)** | [Català (README_CAT.md)](README_CAT.md)

---

## 📖 Project Description

**Restaurant BackOffice v3.0** is an internal management application for restaurants with a **Client/Server architecture**. In this version (Practice 2) the server has been refactored from blocking sockets to **`asyncio`**, so it serves **many clients concurrently**.

This version implements:
- **Asynchronous multi-client server:** `asyncio.start_server` creates **one Task per client**, all running on a single thread (the event loop). An idle or slow client never blocks the others.
- **Blocking database kept off the event loop:** SQLAlchemy + psycopg2 run in worker threads (`asyncio.to_thread`), limited by an `asyncio.Semaphore`.
- **Robustness:** read timeout (408), maximum body size (413), maximum connections (503), clean handling of abrupt disconnections and graceful shutdown with Ctrl+C.
- **Unchanged protocol and business layer:** the REST-inspired HTTP/1.1 + JSON protocol, the services, the Router and the persistence layer from Practice 1 are reused as they were.
- **Automated tests:** services, router, protocol serialization/deserialization and real multi-client scenarios over TCP.

---

## 👤 Authorship

- **Author:** Marc Codina Llonch
- **Vocational Program:** Multiplatform Application Development (DAM - 2nd year)
- **Course Modules:** M0486 (Data Access) & M0487 (Network Services and Processes)

---

## 📚 Reference Documentation

| Document | English Version (ENG) | Catalan Version (CAT) |
|---|---|---|
| **Communication Protocol** | [PROTOCOL_ENG.md](PROTOCOL_ENG.md) | [PROTOCOL_CAT.md](PROTOCOL_CAT.md) |
| **Project & Study Guide** | [PROJECT_DOCUMENTATION_ENG.md](PROJECT_DOCUMENTATION_ENG.md) | [PROJECT_DOCUMENTATION_CAT.md](PROJECT_DOCUMENTATION_CAT.md) |
| **Execution & Testing Guide** | [EXECUTION_GUIDE_ENG.md](EXECUTION_GUIDE_ENG.md) | [EXECUTION_GUIDE_CAT.md](EXECUTION_GUIDE_CAT.md) |
| **Asynchronous Architecture (diagrams)** | — | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Blocking DB vs event loop analysis** | — | [docs/DB_ACCESS_ANALYSIS.md](docs/DB_ACCESS_ANALYSIS.md) |
| **Multi-client demonstration** | — | [docs/DEMO.md](docs/DEMO.md) |

---

## ⚙️ System Requirements

| Requirement | Detail |
|---|---|
| Operating System | Linux, Windows, or macOS |
| Python Runtime | **3.11 or higher** (uses `asyncio.timeout`; tested with 3.14) |
| Database Engine | PostgreSQL (managed with Docker Compose) |

---

## 🚀 Installation & Setup

1. **Clone the repository and checkout v3.0.0:**
   ```bash
   git clone https://github.com/MarcCodinaLlonch/restaurant_backoffice.git
   cd restaurant_backoffice
   git checkout v3.0.0
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Linux / macOS
   ```

3. **Install project dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional, defaults provided):**
   ```bash
   copy .env.example .env          # Windows
   cp .env.example .env            # Linux / macOS
   ```

5. **Start the PostgreSQL database with Docker:**
   ```bash
   docker compose up -d
   ```

---

## 💻 Running the Application

### 1. Start the asyncio server
```bash
python server/server.py
```
The server listens on `0.0.0.0:8088`. Stop it with **Ctrl+C**: it closes cleanly and prints `Server stopped, resources released`.

### 2. Start the interactive client (one or more terminals)
```bash
python client/client.py
```
Open it in several terminals at the same time: every client is served concurrently. The menu covers employees (with 1:1 credentials), categories, dishes (with allergens), allergens, menus (with dishes) and sales (composite primary key).

### 3. Automated client launcher (load test)
```bash
python client/load_test_client.py --clients 20                    # 20 clients at the same time (gather)
python client/load_test_client.py --clients 20 --sequential       # one after another (to compare)
python client/load_test_client.py --clients 20 --idle-clients 3   # plus 3 idle clients that send nothing
```

### 4. Experiments (asyncio fundamentals)
```bash
python experiments/01_await_vs_task.py          # two awaits in a row are NOT concurrent; gather is
python experiments/02_blocking_call.py          # a blocking call freezes the event loop
python experiments/03_blocking_vs_offloaded.py  # blocking DB inline vs to_thread (no PostgreSQL needed)
```

---

## 🧪 Running Automated Tests

```bash
pytest -v
```
All **47 tests** pass (they do not need PostgreSQL):

| Area | Test files |
|---|---|
| Services | `test_services.py` |
| Router | `test_router.py` |
| Protocol serialization / deserialization | `test_request_parser.py`, `test_response_builder.py`, `test_async_request_reader.py` |
| Multi-client and robustness | `test_async_server.py` (20 concurrent clients, idle client, slow DB, disconnection, unexpected error, 408, 400, 413, 503, Practice 1 client) |

PEP 8 check:
```bash
ruff check .
```
