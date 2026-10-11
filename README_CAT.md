# 🍽️ Restaurant BackOffice — v2.0 (Arquitectura Client/Servidor)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![SQLAlchemy](https://img.shields.io/badge/ORM-SQLAlchemy-red.svg)](https://www.sqlalchemy.org/)
[![Sockets](https://img.shields.io/badge/Network-TCP%20Sockets-orange.svg)](https://docs.python.org/3/library/socket.html)
[![Rich](https://img.shields.io/badge/CLI-Rich-blueviolet.svg)](https://rich.readthedocs.io/)
[![Tests](https://img.shields.io/badge/Tests-Pytest%20Passing-brightgreen.svg)](https://docs.pytest.org/)

> 🌐 **Idioma:** [English (README.md)](README.md) | **Català (README_CAT.md)**

---

## 📖 Descripció del Projecte

**Restaurant BackOffice v2.0** és una aplicació completa de gestió interna per a restaurants reestructurada en una **arquitectura Client/Servidor sobre sockets TCP bloquejants**.

Aquesta versió implementa:
- **Separació de responsabilitats**: El Servidor és l'únic que accedeix a la base de dades (PostgreSQL) mitjançant SQLAlchemy. El Client és completament independent i no té cap dependència d'ORM.
- **Protocol de comunicació REST-inspired**: Peticions i respostes de tipus text basades en l'estàndard HTTP/1.1 amb càrrega útil en format **JSON** codificat en **UTF-8**.
- **Capa de Domini Net (Clean Domain)**: Entitats de negoci pures (`@dataclass`) a `common/` que no depenen de tecnologies de persistència.
- **Capa de Serveis (Service Layer) i Router**: Enrutament de peticions i validació de regles de negoci al servidor.
- **Unit of Work i Repositoris**: Persistència atòmica de transaccions i aïllament de consultes SQL.
- **Bateria de Tests**: Cobertura del 100% per a la capa de serveis, validació de peticions, enrutador i comunicació TCP real.

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

---

## ⚙️ Requisits del Sistema

| Requisit | Detall |
|---|---|
| Sistema Operatiu | Linux, Windows o macOS |
| Python | 3.10 o superior (provat amb 3.14) |
| Base de dades | PostgreSQL (gestionada amb Docker Compose) |

---

## 🚀 Instal·lació i Configuració

1. **Clonar el repositori:**
   ```bash
   git clone <URL_DEL_REPOSITORI>
   cd restaurant_backoffice
   ```

2. **Crear i activar l'entorn virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instal·lar les dependències:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Arrencar la base de dades amb Docker:**
   ```bash
   docker-compose up -d
   ```

---

## 💻 Com executar l'aplicació

### 1. Iniciar el Servidor TCP
En una terminal:
```bash
python server/server.py
```
El servidor quedarà escoltant connexions a `0.0.0.0:8080`.

### 2. Iniciar el Client
En una segona terminal:
```bash
python client/client.py
```
S'iniciarà la interfície interactiva de terminal amb suport per a totes les operacions de gestió:
- Gestió d'Empleats (amb credencials xifrades en SHA-256)
- Gestió de Categories
- Gestió de Plats (amb al·lèrgens associats)
- Gestió d'Al·lèrgens
- Gestió de Menús (amb plats associats)
- Gestió de Vendes (clau primària composta)

---

## 🧪 Execució de Tests

Per executar la suite completa de proves unitàries i d'integració sobre TCP:
```bash
pytest -v
```
Totes les 21 proves passaran amb èxit verificant:
- Parsing i framing de peticions HTTP
- Construcció de respostes i serialització JSON
- Enrutament de rutes i control d'errors (400, 404, 500)
- Lògica de negoci als Serveis mitjançant Mocks
- Comunicació Client/Servidor TCP real
