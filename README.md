# 🍽️ Restaurant BackOffice — v2.0 (Client/Server Architecture)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Sockets](https://img.shields.io/badge/Network-TCP%20Sockets-orange.svg)](https://docs.python.org/3/library/socket.html)
[![Rich](https://img.shields.io/badge/CLI-Rich-blueviolet.svg)](https://rich.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)](https://docs.pytest.org/)

> 🌐 **Language:** **English (README.md)** | [Català (README_CAT.md)](README_CAT.md)

---

## 📖 Project Description

**Restaurant BackOffice v2.0** is a comprehensive internal management application for restaurants refactored into a **Client/Server Architecture using blocking TCP sockets**.

This version implements:
- **Separation of Concerns:** The Server is the sole component accessing the database (PostgreSQL) through SQLAlchemy. The Client is completely independent and has zero ORM dependencies.
- **REST-Inspired Communication Protocol:** Plain text request and response formatting based on the HTTP/1.1 standard, exchanging payloads serialized as **JSON** encoded in **UTF-8**.
- **Clean Domain Layer:** Pure business entities (`@dataclass`) in `common/` decoupled from persistence technologies.
- **Service Layer & Router:** Request routing, parameter extraction, and business logic validation on the server.
- **Unit of Work & Repositories:** Atomic transaction management and isolated SQL queries.
- **Automated Test Suite:** 100% test coverage for the service layer, request validation, routing, protocol serialization/deserialization, and real socket communication.

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

---

## ⚙️ System Requirements

| Requirement | Detail |
|---|---|
| Operating System | Linux, Windows, or macOS |
| Python Runtime | 3.10 or higher (tested with 3.14) |
| Database Engine | PostgreSQL (managed with Docker Compose) |

---

## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <REPOSITORY_URL>
   cd restaurant_backoffice
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install project dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the PostgreSQL database with Docker:**
   ```bash
   docker-compose up -d
   ```

---

## 💻 Running the Application

### 1. Start the TCP Server
In your first terminal:
```bash
python server/server.py
```
The server will start listening for TCP connections on `0.0.0.0:8088`.

### 2. Start the Interactive Client
In a second terminal:
```bash
python client/client.py
```
This launches the rich command-line user interface supporting all business operations:
- Employee Management (including 1:1 credentials with SHA-256 password hashing)
- Category Management
- Dish Management (with associated allergens)
- Allergen Management
- Menu Management (with associated dishes)
- Sales Management (with composite primary keys)

---

## 🧪 Running Automated Tests

To execute the full suite of unit and integration tests over TCP:
```bash
pytest -v
```
All 21 tests will pass, validating:
- HTTP request parsing and stream framing
- Response building and JSON serialization
- URL routing and error handling (400, 404, 500)
- Business logic in the service layer using Mocks
- End-to-end TCP client/server socket communication