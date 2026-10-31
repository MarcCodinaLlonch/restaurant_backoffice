# 🍽️ Restaurant BackOffice — v3.0 (Servidor multiclient amb AsyncIO)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![asyncio](https://img.shields.io/badge/Network-asyncio-orange.svg)](https://docs.python.org/3/library/asyncio.html)
[![Rich](https://img.shields.io/badge/CLI-Rich-blueviolet.svg)](https://rich.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-47%20passing-brightgreen.svg)](https://docs.pytest.org/)
[![Ruff](https://img.shields.io/badge/PEP%208-ruff-black.svg)](https://docs.astral.sh/ruff/)

> 🌐 **Idioma:** [English (README.md)](README.md) | **Català (README_CAT.md)**

---

## 📖 Descripció del Projecte

**Restaurant BackOffice v3.0** és una aplicació de gestió interna per a restaurants amb **arquitectura Client/Servidor**. En aquesta versió (Pràctica 2) el servidor ha passat de sockets bloquejants a **`asyncio`**, i ara atén **molts clients alhora**.

Aquesta versió implementa:
- **Servidor asíncron multiclient**: `asyncio.start_server` crea **una Task per client**, i totes s'executen en un sol fil (l'event loop). Un client lent o inactiu no bloqueja mai els altres.
- **La BD bloquejant, fora de l'event loop**: SQLAlchemy + psycopg2 s'executen en fils (`asyncio.to_thread`), limitats per un `asyncio.Semaphore`.
- **Robustesa**: timeout de lectura (408), mida màxima del cos (413), màxim de connexions (503), gestió neta de desconnexions sobtades i aturada neta amb Ctrl+C.
- **Protocol i capa de negoci sense canvis**: el protocol HTTP/1.1 + JSON, els serveis, el Router i la persistència de la Pràctica 1 es reutilitzen tal com eren.
- **Tests automàtics**: serveis, router, serialització/deserialització del protocol i escenaris multiclient reals sobre TCP.

---

## 👤 Autoria

- **Autor:** Marc Codina Llonch
- **Cicle:** Desenvolupament d'Aplicacions Multiplataforma (DAM 2n curs)
- **Mòduls:** M0486 (Accés a Dades) i M0487 (Programació de Serveis i Processos)

---

## 📚 Documents de Referència

| Document | Versió en Anglès (ENG) | Versió en Català (CAT) |
|---|---|---|
| **Protocol de Comunicació** | [PROTOCOL_ENG.md](PROTOCOL_ENG.md) | [PROTOCOL_CAT.md](PROTOCOL_CAT.md) |
| **Documentació del Projecte i Estudi** | [PROJECT_DOCUMENTATION_ENG.md](PROJECT_DOCUMENTATION_ENG.md) | [PROJECT_DOCUMENTATION_CAT.md](PROJECT_DOCUMENTATION_CAT.md) |
| **Guia d'Execució i Proves** | [EXECUTION_GUIDE_ENG.md](EXECUTION_GUIDE_ENG.md) | [EXECUTION_GUIDE_CAT.md](EXECUTION_GUIDE_CAT.md) |
| **Arquitectura asíncrona (diagrames)** | — | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| **Anàlisi de la BD bloquejant** | — | [docs/DB_ACCESS_ANALYSIS.md](docs/DB_ACCESS_ANALYSIS.md) |
| **Demostració multiclient** | — | [docs/DEMO.md](docs/DEMO.md) |

---

## ⚙️ Requisits del Sistema

| Requisit | Detall |
|---|---|
| Sistema Operatiu | Linux, Windows o macOS |
| Python | **3.11 o superior** (fa servir `asyncio.timeout`; provat amb 3.14) |
| Base de dades | PostgreSQL (gestionada amb Docker Compose) |

---

## 🚀 Instal·lació i Configuració

1. **Clonar el repositori i canviar a la versió v3.0.0:**
   ```bash
   git clone https://github.com/MarcCodinaLlonch/restaurant_backoffice.git
   cd restaurant_backoffice
   git checkout v3.0.0
   ```

2. **Crear i activar l'entorn virtual:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Linux / macOS
   ```

3. **Instal·lar les dependències:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar les variables d'entorn (opcional, hi ha valors per defecte):**
   ```bash
   copy .env.example .env          # Windows
   cp .env.example .env            # Linux / macOS
   ```

5. **Engegar PostgreSQL amb Docker:**
   ```bash
   docker compose up -d
   ```

---

## 💻 Com executar l'aplicació

### 1. Iniciar el servidor asíncron
```bash
python server/server.py
```
El servidor escolta a `0.0.0.0:8088`. S'atura amb **Ctrl+C**: es tanca de manera neta i mostra `Server stopped, resources released`.

### 2. Iniciar el client interactiu (un o més terminals)
```bash
python client/client.py
```
Obre'l en diversos terminals alhora: tots els clients s'atenen concurrentment. El menú permet gestionar empleats (amb credencials 1:1), categories, plats (amb al·lèrgens), al·lèrgens, menús (amb plats) i vendes (clau primària composta).

### 3. Llançador automàtic de clients (prova de càrrega)
```bash
python client/load_test_client.py --clients 20                    # 20 clients alhora (gather)
python client/load_test_client.py --clients 20 --sequential       # un darrere l'altre (per comparar)
python client/load_test_client.py --clients 20 --idle-clients 3   # més 3 clients inactius que no envien res
```

### 4. Experiments (fonaments d'asyncio)
```bash
python experiments/01_await_vs_task.py          # dos await seguits NO són concurrents; gather sí
python experiments/02_blocking_call.py          # una crida bloquejant congela l'event loop
python experiments/03_blocking_vs_offloaded.py  # BD bloquejant inline vs to_thread (no cal PostgreSQL)
```

---

## 🧪 Execució de Tests

```bash
pytest -v
```
Passen els **47 tests** (no necessiten PostgreSQL):

| Àrea | Fitxers de tests |
|---|---|
| Serveis | `test_services.py` |
| Router | `test_router.py` |
| Serialització / deserialització del protocol | `test_request_parser.py`, `test_response_builder.py`, `test_async_request_reader.py` |
| Multiclient i robustesa | `test_async_server.py` (20 clients alhora, client inactiu, BD lenta, desconnexió, error inesperat, 408, 400, 413, 503, client de la P1) |

Comprovació de PEP 8:
```bash
ruff check .
```
