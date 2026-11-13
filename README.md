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
- **Synchronous database, impact analysed**: SQLAlchemy + psycopg2 are called directly from the event loop (queries of a few ms). The impact is measured in docs/DB_ACCESS_ANALYSIS_ENG.md.
- **Robustness:** read timeout (408), maximum body size (413), clean handling of abrupt disconnections and graceful shutdown with Ctrl+C.
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
| **Asynchronous Architecture (diagrams)** | [docs/ARCHITECTURE_ENG.md](docs/ARCHITECTURE_ENG.md) | [docs/ARCHITECTURE_CAT.md](docs/ARCHITECTURE_CAT.md) |
| **Blocking DB vs event loop analysis** | [docs/DB_ACCESS_ANALYSIS_ENG.md](docs/DB_ACCESS_ANALYSIS_ENG.md) | [docs/DB_ACCESS_ANALYSIS_CAT.md](docs/DB_ACCESS_ANALYSIS_CAT.md) |
| **Multi-client demonstration** | [docs/DEMO_ENG.md](docs/DEMO_ENG.md) | [docs/DEMO_CAT.md](docs/DEMO_CAT.md) |

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

6. **Generate the server TLS certificates manually with OpenSSL (Practice 3):**
   ```bash
   mkdir -p certs
   # 1. Generate self-signed certificate with SAN (cert.pem) and private key (key.pem)
   MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
     -keyout certs/key.pem -out certs/cert.pem -subj "/CN=localhost" \
     -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

   # 2. (Optional) Bundle into PKCS#12 (.p12) format
   openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
   ```

---

## 💻 Running the Application

### 1. Start the asyncio TLS server
```bash
python server/server.py
```
The server loads the certificate (`certs/cert.pem` + `certs/key.pem`) using `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` and listens on `https://0.0.0.0:8088`. Stop it with **Ctrl+C**: it closes cleanly and prints `Server stopped, resources released`.

### 2. Start the interactive client (one or more terminals)
```bash
python client/client.py
```
The client connects over TLS using `ssl.create_default_context(cafile="certs/cert.pem")` to verify the server's certificate and SAN, and checks payload integrity via the `Content-Hash` (SHA-256) header. Open it in several terminals at the same time: every client is served concurrently.

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
python experiments/03_blocking_db_impact.py  # impact of the synchronous DB: 2 ms vs 200 ms queries (no PostgreSQL needed)
```

---

## 🧪 Running Automated Tests

```bash
pytest -v
```
All **58 tests** pass (they do not need PostgreSQL):

| Area | Test files |
|---|---|
| Services | `test_services.py` |
| Router | `test_router.py` |
| Protocol serialization / deserialization | `test_request_parser.py`, `test_response_builder.py`, `test_async_request_reader.py` |
| Multi-client and robustness | `test_async_server.py` (20 concurrent clients, idle client, disconnection, unexpected error, 408, 400, 413, Practice 1 client) |
| TLS Security & `Content-Hash` | `test_security_tls.py` (server certificate & SAN verification with `cafile`, TLS 1.3 + AES-GCM, untrusted cert rejection, SHA-256 integrity) |

PEP 8 check:
```bash
ruff check .
```
