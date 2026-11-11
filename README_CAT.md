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
- **BD síncrona, impacte analitzat**: SQLAlchemy + psycopg2 es criden directament des de l'event loop (consultes de pocs ms). L'impacte està mesurat a docs/DB_ACCESS_ANALYSIS_CAT.md.
- **Robustesa**: timeout de lectura (408), mida màxima del cos (413), gestió neta de desconnexions sobtades i aturada neta amb Ctrl+C.
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
| **Arquitectura asíncrona (diagrames)** | [docs/ARCHITECTURE_ENG.md](docs/ARCHITECTURE_ENG.md) | [docs/ARCHITECTURE_CAT.md](docs/ARCHITECTURE_CAT.md) |
| **Anàlisi de la BD bloquejant** | [docs/DB_ACCESS_ANALYSIS_ENG.md](docs/DB_ACCESS_ANALYSIS_ENG.md) | [docs/DB_ACCESS_ANALYSIS_CAT.md](docs/DB_ACCESS_ANALYSIS_CAT.md) |
| **Demostració multiclient** | [docs/DEMO_ENG.md](docs/DEMO_ENG.md) | [docs/DEMO_CAT.md](docs/DEMO_CAT.md) |

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

6. **Generar els certificats TLS del servidor a mà amb OpenSSL (Pràctica 3):**
   ```bash
   mkdir -p certs
   # 1. Generar certificat autosignat (cert.pem) i clau privada (key.pem)
   openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

   # 2. (Opcional) Empaquetar en format PKCS#12 (.p12)
   openssl pkcs12 -export -out certs/server.p12 -inkey certs/key.pem -in certs/cert.pem -passout pass:1234
   ```

---

## 💻 Com executar l'aplicació

### 1. Iniciar el servidor asíncron amb TLS
```bash
python server/server.py
```
El servidor carrega el certificat (`certs/cert.pem` + `certs/key.pem`) amb `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` i escolta a `https://0.0.0.0:8088`. S'atura amb **Ctrl+C**: es tanca de manera neta i mostra `Server stopped, resources released`.

### 2. Iniciar el client interactiu (un o més terminals)
```bash
python client/client.py
```
El client es connecta sobre TLS utilitzant `ssl._create_unverified_context()` per acceptar el certificat autosignat del servidor i verifica la integritat de cada missatge amb la capçalera `Content-Hash` (SHA-256). Obre'l en diversos terminals alhora: tots els clients s'atenen concurrentment.

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
python experiments/03_blocking_db_impact.py  # impacte de la BD síncrona: consultes de 2 ms vs 200 ms (no cal PostgreSQL)
```

---

## 🧪 Execució de Tests

```bash
pytest -v
```
Passen els **50 tests** (no necessiten PostgreSQL):

| Àrea | Fitxers de tests |
|---|---|
| Serveis | `test_services.py` |
| Router | `test_router.py` |
| Serialització / deserialització del protocol | `test_request_parser.py`, `test_response_builder.py`, `test_async_request_reader.py` |
| Multiclient i robustesa | `test_async_server.py` (20 clients alhora, client inactiu, desconnexió, error inesperat, 408, 400, 413, client de la P1) |
| Seguretat TLS i `Content-Hash` | `test_security_tls.py` (certificat autosignat amb OpenSSL, `ssl._create_unverified_context()`, integritat SHA-256) |

Comprovació de PEP 8:
```bash
ruff check .
```
