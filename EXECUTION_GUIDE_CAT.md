# Guia Pas a Pas: Com Executar i Provar Restaurant BackOffice v3.0

> 🌐 **Idioma:** [English (EXECUTION_GUIDE_ENG.md)](EXECUTION_GUIDE_ENG.md) | **Català (EXECUTION_GUIDE_CAT.md)**  
> Tutorial complet per provar l'aplicació Client/Servidor, els tests automatitzats i comprovar el funcionament de totes les opcions.  
> Arquitectura del servidor asyncio (v3.0): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 📋 Requisits Previs

Assegura't de tenir el projecte descarregat i una terminal oberta a la carpeta arrel:
```bash
cd restaurant_backoffice
```

---

## PAS 1: Activar l'Entorn Virtual i Comprovar la Base de Dades

1. **Activa l'entorn virtual de Python:**
   ```bash
   .venv\Scripts\activate          # Windows
   source .venv/bin/activate       # Linux / macOS
   ```

2. **Comprova que el contenidor Docker de PostgreSQL està en marxa:**
   ```bash
   docker ps
   ```
   Hauries de veure el contenidor `restaurant_db_container` actiu al port `5433`.  
   *(Si no estigués engegat, executa: `docker-compose up -d`)*

---

## PAS 2: Executar la Bateria de Tests Automatitzats

Abans d'engegar els programes manuals, comprova que tota la lògica, el router i el protocol funcionen al 100%:

```bash
pytest -v
```

**Què veuràs:**
Un llistat verd amb **47 tests superats (100% PASSED)** en un segon aproximadament:
- Escenaris multiclient reals contra el servidor asyncio (20 clients alhora, client inactiu, BD lenta, 408/400/413/503).
- Parsing i construcció de peticions/respostes HTTP.
- Lògica de negoci de tots els serveis amb Mocks.
- Control d'errors i rutes 404 del Router.

---

## PAS 3: Arrencar el Servidor asyncio (Terminal 1)

Obre la **primera terminal** (pots anomenar-la "Terminal Servidor"):

```bash
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
python server/server.py
```

**Sortida esperada per pantalla:**
```text
HH:MM:SS [INFO] server.src.bootstrap: Database ready
HH:MM:SS [INFO] server: Listening on 0.0.0.0:8088 (Ctrl+C to stop)
```
> ⏸️ **Deixa aquesta terminal oberta.** El servidor està esperant connexions i n'atén moltes alhora (una Task d'asyncio per client).

---

## PAS 4: Arrencar el Client Interactiu (Terminal 2)

Obre una **segona terminal** (al VS Code pots prémer la icona de dividir terminal `Split Terminal` o `Ctrl + Shift + 5`):

```bash
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
python client/client.py
```

**Sortida esperada per pantalla:**
Apareixerà el bàner ASCII i el menú interactiu Rich:

```text
       __...--~~~~~-._   _.-~~~~~--...__
     //               `V'               \\ 
    //                 |                 \\ 
   //__...--~~~~~~-._  |  _.-~~~~~~--...__\\ 
  //__.....----.....__\|/__.....----.....__\\

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Restaurant BackOffice (Client TCP) — Servidor: 127.0.0.1:8088                   ┃
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

## PAS 5: Prova Guiada de les Funcionalitats (Demostració)

Pots seguir aquest guió per comprovar que tot el cicle de vida de les dades funciona per xarxa:

### 1. Comprovar la lectura (READ)
- Tria l'opció **`2`** (*Gestió de Categories*).
- Tria l'opció **`1`** (*Llistar Categories*).
- **Resultat:** Es demanarà al servidor la llista i es dibuixarà una taula de color magenta amb les categories existents (`Entrants`, `Primers Plats`...).
- Prem `Enter` per continuar.

### 2. Comprovar la creació (CREATE)
- Dins del mateix submenú de categories, tria l'opció **`2`** (*Afegir Categoria*).
- Escriu: `Pizzes Artesanes` i prem `Enter`.
- **Resultat:** Veuràs el missatge verd `✓ Categoria 'Pizzes Artesanes' creada amb èxit al servidor!`.
- Torna a prémer `1` per llistar categories i comprova que ara té un nou ID assignat per la base de dades.

### 3. Comprovar la modificació (UPDATE)
- Tria l'opció **`3`** (*Modificar Categoria*).
- Introdueix l'ID de la categoria que acabes de crear.
- Posa el nou nom: `Pizzes al Forn de Llenya`.
- **Resultat:** Veuràs `✓ Categoria actualitzada correctament`.

### 4. Comprovar l'eliminació (DELETE)
- Tria l'opció **`4`** (*Eliminar Categoria*).
- Posa el mateix ID i confirma amb `s`.
- **Resultat:** Veuràs `✓ Categoria eliminada correctament!`.
- Prem `0` per tornar al menú principal.

### 5. Prova d'Empleats amb Credencials (Relació 1:1 i xifrat SHA-256)
- Tria l'opció **`1`** (*Gestió d'Empleats*).
- Tria l'opció **`2`** (*Afegir nou empleat*).
- Omple les dades:
  - Nom: `Pol`
  - Cognom: `Rovira`
  - DNI: `77889900X`
  - Rol: `Cambrer`
  - Vols afegir credencials? `s`
  - Email: `pol.rovira@restaurant.com`
  - Contrasenya: `SuperPassword123`
- Veuràs que es crea correctament.
- Tria l'opció **`3`** (*Veure detall d'un empleat*) i posa l'ID d'en Pol:
  - Veuràs que té credencials amb el seu email, però la contrasenya diu `*** (xifrat SHA256 al servidor) ***` protegint les dades.
- Prem `0` per tornar.

---

## PAS 6: Prova "Bonus" (Provar el teu servidor amb `curl` o navegador)

Com que el teu servidor parla el protocol estàndard HTTP/1.1 sobre TCP, pots obrir una **tercera terminal** i provar-ho sense fer servir el client de Python:

```bash
curl -i http://localhost:8088/categories
```

**Què respon el teu servidor:**
```http
HTTP/1.1 200 OK
Connection: close
Content-Type: application/json; charset=utf-8
Content-Length: 182

[{"id": 1, "category_name": "Entrants"}, {"id": 2, "category_name": "Primers Plats"}, ...]
```

---

## PAS 7: Com Aturar el Sistema

1. **A la Terminal del Client:** Prem `0` al menú principal. Sortirà dient `Fins aviat!`.
2. **A la Terminal del Servidor:** Prem `Ctrl + C`. El servidor s'atura de manera neta (sense *traceback*) i mostrarà:
   ```text
   HH:MM:SS [INFO] server: Server stopped, resources released
   ```
