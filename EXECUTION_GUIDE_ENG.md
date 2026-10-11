# Step-by-Step Guide: How to Run and Test Restaurant BackOffice v2.0

> 🌐 **Language:** **English (EXECUTION_GUIDE_ENG.md)** | [Català (EXECUTION_GUIDE_CAT.md)](EXECUTION_GUIDE_CAT.md)  
> Complete tutorial to run the Client/Server application, execute automated tests, and verify all features.

---

## 📋 Prerequisites

Ensure your terminal is located at the repository root:
```bash
cd /home/marcc/Projectes/restaurant_backoffice
```

---

## STEP 1: Activate Virtual Environment & Check PostgreSQL

1. **Activate the Python virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

2. **Verify the PostgreSQL Docker container is running:**
   ```bash
   docker ps
   ```
   You should see `restaurant_db_container` active on port `5433`.  
   *(If not running, execute: `docker-compose up -d`)*

---

## STEP 2: Execute Automated Test Suite

Before manually launching the applications, run the complete test suite to ensure all services, router, and sockets pass:

```bash
pytest -v
```

**Expected Output:**
A green list confirming **21 tests passed (100% PASSED)** in less than a second:
- Real TCP client-server socket communication.
- HTTP stream parsing and response framing.
- Business logic across all domain services using Mocks.
- Router dispatching and 404 error handling.

---

## STEP 3: Start the TCP Server (Terminal 1)

Open your **first terminal window** (e.g., "Server Terminal"):

```bash
source .venv/bin/activate
python server/server.py
```

**Expected Console Output:**
```text
[*] Inicialitzant serveis i connexió a la BD (localhost:5433/restaurant_db_dev)...
============================================================
 RESTAURANT BACKOFFICE — SERVIDOR TCP EN EXECUCIÓ
 Escoltant a: http://0.0.0.0:8080/
 Protocol: HTTP/1.1 REST sobre TCP (Sockets bloquejants)
 Prem Ctrl+C per aturar el servidor.
============================================================
```
> ⏸️ **Leave this terminal open.** The server is actively waiting for client connections on port `8080`.

---

## STEP 4: Start the Interactive Client (Terminal 2)

Open a **second terminal window** (or split your VS Code terminal with `Ctrl + Shift + 5`):

```bash
source .venv/bin/activate
python client/client.py
```

**Expected Console Output:**
The ASCII banner and the interactive Rich menu will render:

```text
       __...--~~~~~-._   _.-~~~~~--...__
     //               `V'               \\ 
    //                 |                 \\ 
   //__...--~~~~~~-._  |  _.-~~~~~~--...__\\ 
  //__.....----.....__\|/__.....----.....__\\

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Restaurant BackOffice (Client TCP) — Servidor: 127.0.0.1:8080                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
1. Gestió d'Empleats
2. Gestió de Categories
3. Gestió de Plats
4. Gestió d'Al·lèrgens
5. Gestió de Menús
6. Gestió de Vendes
0. Sortir

Selecciona una opció: 
```

---

## STEP 5: Guided Testing of Business Operations (Demo Walkthrough)

Follow this walkthrough to verify that full data lifecycles operate over the network:

### 1. Test Read Operations (READ)
- Choose option **`2`** (*Category Management*).
- Choose option **`1`** (*List Categories*).
- **Result:** The client requests `/categories` over TCP and renders a magenta table displaying existing categories (`Entrants`, `Primers Plats`...).
- Press `Enter` to return to the menu.

### 2. Test Create Operations (CREATE)
- Inside the categories menu, choose option **`2`** (*Add Category*).
- Enter: `Pizzes Artesanes` and press `Enter`.
- **Result:** You will see the green success message `✓ Categoria 'Pizzes Artesanes' creada amb èxit al servidor!`.
- Choose `1` to list categories again and verify the database assigned an autoincrement ID to it.

### 3. Test Update Operations (UPDATE)
- Choose option **`3`** (*Update Category*).
- Enter the ID of the category you just created.
- Type the new name: `Pizzes al Forn de Llenya`.
- **Result:** You will see `✓ Categoria actualitzada correctament`.

### 4. Test Delete Operations (DELETE)
- Choose option **`4`** (*Delete Category*).
- Enter the same ID and confirm with `s`.
- **Result:** The category is deleted from PostgreSQL.
- Press `0` to return to the main menu.

### 5. Test Employees with Credentials (1:1 & SHA-256 Hashing)
- Choose option **`1`** (*Employee Management*).
- Choose option **`2`** (*Add New Employee*).
- Fill in:
  - Name: `Pol`
  - Surname: `Rovira`
  - National ID: `77889900X`
  - Role: `Cambrer`
  - Add login credentials? `s`
  - Email: `pol.rovira@restaurant.com`
  - Password: `SuperPassword123`
- After creation, select option **`3`** (*View Employee Detail*) and input Pol's ID:
  - You will see his email, while the password displays `*** (xifrat SHA256 al servidor) ***` proving credentials are secure.
- Press `0` to return.

---

## STEP 6: Bonus Verification (Testing the Server with `curl`)

Because the server implements standard HTTP/1.1 over TCP, you can open a **third terminal** and query the backend directly:

```bash
curl -i http://localhost:8080/categories
```

**Server Response:**
```http
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 182

[{"id": 1, "category_name": "Entrants"}, {"id": 2, "category_name": "Primers Plats"}, ...]
```

---

## STEP 7: Gracefully Stopping the System

1. **In Client Terminal (Terminal 2):** Press `0` at the main menu. The client prints `Fins aviat!` and exits.
2. **In Server Terminal (Terminal 1):** Press `Ctrl + C`. The server cleanly shuts down and releases the socket:
   ```text
   [*] Aturant el servidor per petició de l'usuari...
   [*] Servidor aturat correctament.
   ```
