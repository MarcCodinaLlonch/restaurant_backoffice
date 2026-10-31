# Demostració multiclient: Restaurant BackOffice v3.0.0

Guia **reproduïble** per demostrar que el servidor atén diversos clients alhora, i quin benefici té respecte a la Pràctica 1.

Les comandes són per a **Linux/macOS** (bash). Quan a **Windows** canvia alguna cosa, la variant hi és al costat com a comentari. Les comandes `python ...` funcionen igual als dos sistemes.

## Preparació (un sol cop)

```bash
docker compose up -d                 # PostgreSQL
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Demo 1: P1 vs P2: un client "mut" bloqueja la P1 però no la P2 ⭐

És la demo més convincent: **el mateix client de càrrega** contra els dos servidors.

```bash
# Prepara una còpia del servidor de la P1 (tag v2.0.0) al costat del projecte
git worktree add ../p1_server v2.0.0
cp .env ../p1_server/.env            # Windows: copy .env ..\p1_server\.env
```

**a) Servidor P1** (terminal 1):
```bash
cd ../p1_server && python server/server.py      # Windows: cd ..\p1_server ; python server\server.py
```
Terminal 2 (des del projecte P2):
```bash
python client/load_test_client.py --clients 5 --idle-clients 1
```
→ **~3 s**: el servidor P1 queda bloquejat a `recv()` esperant el client inactiu, i els altres 5 fan cua.

**b) Servidor P2:** atura el P1 (Ctrl+C) i, al terminal 1, torna al projecte i executa `python server/server.py`. Repeteix la mateixa comanda al terminal 2.
→ **< 0,1 s**: cada client té la seva Task, i el client inactiu no molesta ningú.

Quan ja no necessitis la còpia de la P1: `git worktree remove ../p1_server`.

## Demo 2: Tres terminals alhora (clients interactius)

| Terminal | Comanda |
|---|---|
| 1 | `python server/server.py` |
| 2 | `python client/client.py` → Gestió de Plats → Llistar |
| 3 | `python client/client.py` → Gestió de Categories → Afegir |

Al log del terminal 1 es veuen les connexions de tots dos clients, amb adreces i ports diferents, i el comptador `active: N`.
Per veure-ho de manera més clara, mentre els clients treballen, obre un 4t terminal amb un client mut:
```bash
python -c "import socket,time; s=socket.create_connection(('127.0.0.1',8088)); time.sleep(10)"
```
Els clients interactius continuen funcionant. Al cap de 5 s, el log mostra `Read timeout` i el client mut rep un **408**.

## Demo 3: Llançador automàtic: concurrent vs seqüencial

```bash
python client/load_test_client.py --clients 30
python client/load_test_client.py --clients 30 --sequential
python client/load_test_client.py --clients 30 --idle-clients 3
```
Amb consultes ràpides en local, la diferència entre el mode concurrent i el seqüencial és petita. **El benefici de la concurrència apareix quan hi ha esperes** (clients lents o una BD lenta): ho demostren la demo 1 i la demo 4.

Mesures reals (`docs/evidence/04_load_concurrent_vs_sequential.txt`):

| BD | Concurrent | Seqüencial | Per què |
|---|---|---|---|
| PostgreSQL | ~0,45 s | ~0,69 s | Cada consulta espera la xarxa: mentre un fil espera, els altres avancen |
| SQLite | ~0,41 s | ~0,29-0,36 s | SQLite és dins del procés (CPU + GIL): no hi ha esperes per solapar i els fils només afegeixen cost |

## Demo 4: Impacte d'una BD bloquejant (no necessita Docker)

```bash
python experiments/03_blocking_vs_offloaded.py
```
10 clients, cada consulta tarda 0,2 s: **inline ≈ 2 s** (en fila) vs **to_thread ≈ 0,2-0,4 s** (solapades).

## Demo 5: Robustesa i aturada neta

- Petició mal formada → **400**, i el servidor continua:
  `python -c "import socket; s=socket.create_connection(('127.0.0.1',8088)); s.sendall(b'HOLA\r\n\r\n'); print(s.recv(200))"`
- **Ctrl+C** al servidor → `Server stopped, resources released`, sense *traceback*.

## Demo 6: Tests automàtics

```bash
pytest -v
```
`tests/test_async_server.py` arrenca un servidor real i hi connecta clients TCP reals: 20 clients alhora, un client mut, una BD lenta, una desconnexió a mitja petició, un error inesperat, i els codis 408/400/413/503.

## Proves desades

A `docs/evidence/` hi ha la sortida de cada demo (`*.txt`) i captures de pantalla (`*.png`).

Les proves de text s'han generat amb SQLite (no cal Docker), amb aquestes variables d'entorn:
```bash
ENVIRONMENT=test DB_URL_TESTS=sqlite:///demo.db SERVER_PORT=8099
```
