# Anàlisi de l'Impacte de les Operacions Bloquejants de BD a l'Event Loop

Aquest document presenta l'estudi tècnic sobre la convivència entre l'Event Loop d'AsyncIO i les consultes síncrones a base de dades (SQLAlchemy + `psycopg2`), tal com requereix l'enunciat de la pràctica.

---

## 1. El Problema Teòric

L'arquitectura d'**AsyncIO** es basa en la concurrència cooperativa sobre un **únic fil d'execució** (single thread).
- Cada vegada que una coroutine fa `await`, cedeix el control al bucle d'esdeveniments (*Event Loop*) perquè una altra tasca pugui aprofitar la CPU o la xarxa.
- Quan s'executa una crida tradicional síncrona (com una consulta `session.query(Dish).all()` mitjançant SQLAlchemy i el driver `psycopg2`), el codi en C del driver TCP espera la resposta de PostgreSQL a nivell de socket de sistema operatiu sense cedir el control a l'Event Loop.
- **Conseqüència:** Tot l'Event Loop queda bloquejat. Si una consulta triga 200 ms, durant aquest interval **cap altre client no pot connectar-se, enviar peticions ni rebre respostes**.

---

## 2. Evidència Experimental (Resultats Mesurats)

L'experiment `experiments/03_blocking_vs_offloaded.py` arrenca el servidor real (`ClientConnectionHandler`) amb un Router fals que bloqueja el fil 0,2 s per petició (`time.sleep`, com una consulta `psycopg2`) i hi llança **10 clients alhora**. No necessita PostgreSQL:

```
python experiments/03_blocking_vs_offloaded.py
```

Resultats mesurats (3 execucions, ordinador de 8 nuclis, Python 3.14):

| Mode | Temps total (10 peticions) | Comportament de l'event loop |
|---|---|---|
| **inline** (Router cridat directament dins l'event loop) | **2,01 s** | Bloquejat: les peticions s'atenen una darrere l'altra (10 × 0,2 s) |
| **to_thread** (`RequestDispatcher`) | **0,21 s** | Lliure: les 10 consultes s'executen solapades en fils |

**Guany observat:** `to_thread` és unes **9,5 vegades** més ràpid.

**Límit de fils:** `asyncio.to_thread` fa servir el *ThreadPoolExecutor* per defecte del loop, que té `min(32, nuclis + 4)` fils (aquí 12). Amb 10 clients n'hi ha prou i tot es solapa (~0,2 s). En un ordinador amb pocs nuclis (p. ex. 4 nuclis → 8 fils) les peticions anirien en dues tandes i el temps seria d'uns 0,4 s.

---

## 3. La Solució Implementada: `RequestDispatcher`

Per desacoblar el servidor asíncron de la capa de persistència síncrona existent, es va introduir el patró **RequestDispatcher**:

```python
class RequestDispatcher:
    def __init__(self, router: Router, max_concurrent_calls: int) -> None:
        self._router = router
        self._db_slots = asyncio.Semaphore(max_concurrent_calls)

    async def dispatch(self, request: HttpRequest) -> bytes:
        async with self._db_slots:
            return await asyncio.to_thread(self._router.handle_request, request)
```

### Per què funciona amb el GIL de Python?
Python utilitza el **Global Interpreter Lock (GIL)**, que impedeix que dos fils executin instruccions bytecode de Python alhora. No obstant això, quan una llibreria d'I/O (com `psycopg2` fent consultes a la xarxa cap a PostgreSQL) espera una resposta de la base de dades, **allibera explícitament el GIL**. Això permet que múltiples fils esperin dades de la BD de manera realment simultània mentre el fil principal d'AsyncIO continua servint altres clients.

### Per què fem servir un `asyncio.Semaphore`?
El pool de connexions de la base de dades té una capacitat finita: SQLAlchemy té per defecte `pool_size=5` i `max_overflow=10`; per això `DB_MAX_CONCURRENCY=5`. Si 100 clients sol·licitessin dades alhora sense control:
1. Es crearien 100 fils que competirien per les 5 connexions de la base de dades, provocant bloquejos per esgotament del pool (*ConnectionPoolTimeout*).
2. El consum de memòria RAM augmentaria innecessàriament.
Amb el semàfor, limitem a un màxim segur (`DB_MAX_CONCURRENCY=5`) les tasques que poden consultar la BD a la vegada. Les peticions addicionals esperen el seu torn de manera **asíncrona i cooperativa** dins l'Event Loop sense consumir recursos del sistema.

---

## 4. Comparativa de Solucions Alternatives

| Criteri | `asyncio.to_thread` + Semaphore (Nostra Solució) | Driver Asíncron Pur (`asyncpg` + Async SQLAlchemy) |
|---|---|---|
| **Impacte en l'arquitectura existent** | Mínim (tot el domini, serveis i repositoris es mantenen 100% intactes). | Molt elevat (tot el codi ha de convertir-se a `async def`, `async with`, `selectinload`). |
| **Ús de fils** | Utilitza un pool intern de fils (`ThreadPoolExecutor`). | Zero fils addicionals (I/O purament asíncron). |
| **Cancel·lació de consultes** | No és cancel·lable una vegada el fil ha iniciat la query. | Cancel·lació nativa mitjançant cancel·lació de la coroutine. |
| **Risc d'errors** | Molt baix i segur (cada transacció té la seva pròpia sessió aïllada). | Risc d'errors `MissingGreenlet` per càrrega mandrosa (*lazy loading*). |

**Conclusió:** L'enfocament `asyncio.to_thread` acompanyat del semàfor de control de concurrència és la solució òptima per a aquest escenari, ja que proporciona un rendiment pràcticament idèntic al model completament asíncron mantenint una estricta separació de responsabilitats i preservant la integritat de la capa de negoci.

---

## 5. Repte opcional: investigat, no implementat

### Què és
SQLAlchemy 2.0 té una API asíncrona: `create_async_engine` + `AsyncSession`, amb un driver asíncron com `asyncpg` (URL `postgresql+asyncpg://...`). Les consultes es fan amb `await` i no calen fils:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

engine = create_async_engine("postgresql+asyncpg://postgres:secret@localhost:5433/restaurant_db_dev")
session_factory = async_sessionmaker(engine, expire_on_commit=False)

async with session_factory() as session:
    result = await session.execute(select(Dish))
```

### Per què NO s'ha implementat
- **"L'async és contagiós":** si el repositori és `async`, també ho han de ser la Unit of Work, els 6 serveis i el Router. Caldria reescriure tota la capa de negoci de la P1.
- **Càrrega mandrosa de relacions:** accedir a `dish.allergens` fora d'un `await` falla amb `MissingGreenlet`. Caldria afegir `selectinload(...)` a totes les consultes que fan servir relacions.
- **Molta complexitat per a poc benefici:** en aquesta aplicació les consultes són curtes i el pool té 5 connexions. `to_thread` ja dona un rendiment pràcticament igual (vegeu la secció 2).

### Conclusió
Amb `asyncio.to_thread` + `asyncio.Semaphore` l'event loop no es bloqueja mai, la capa de negoci de la P1 queda **intacta** (requisit *"maintain the existing service layer"*) i el codi és més fàcil d'entendre i de mantenir.
