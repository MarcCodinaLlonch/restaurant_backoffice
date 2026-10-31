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

Mitjançant l'experiment `experiments/blocking_vs_offloaded.py`, es va simular l'arribada simultània de **10 peticions concurrents** que realitzaven una operació de lectura de BD estimada en 200 ms:

| Mètode d'Execució | Temps Total (10 peticions) | Comportament de l'Event Loop | Latència per Client |
|---|---|---|---|
| **Inline (Síncron directe al loop)** | **~2.012 s** | Congelat (Execució seqüencial en fila índia) | Entre 200 ms i 2.000 ms |
| **Offloaded (`asyncio.to_thread`)** | **~0.208 s** | Lliure (Execució solapada en fils del sistema) | ~200 ms per a tots |

**Guany observat:** Una acceleració de **gairebé 10x** en temps de resposta global.

---

## 3. La Solució Implementada: `RequestDispatcher`

Per desacoblar el servidor asíncron de la capa de persistència síncrona existent, es va introduir el patró **RequestDispatcher**:

```python
class RequestDispatcher:
    def __init__(self, router: Router, max_concurrent_calls: int = 10) -> None:
        self._router = router
        self._db_slots = asyncio.Semaphore(max_concurrent_calls)

    async def dispatch(self, request: HttpRequest) -> bytes:
        async with self._db_slots:
            return await asyncio.to_thread(self._router.handle_request, request)
```

### Per què funciona amb el GIL de Python?
Python utilitza el **Global Interpreter Lock (GIL)**, que impedeix que dos fils executin instruccions bytecode de Python alhora. No obstant això, quan una llibreria d'I/O (com `psycopg2` fent consultes a la xarxa cap a PostgreSQL) espera una resposta de la base de dades, **allibera explícitament el GIL**. Això permet que múltiples fils esperin dades de la BD de manera realment simultània mentre el fil principal d'AsyncIO continua servint altres clients.

### Per què fem servir un `asyncio.Semaphore`?
El pool de connexions de la base de dades té una capacitat finita (per defecte entre 5 i 10 connexions simultànies). Si 100 clients sol·licitessin dades alhora sense control:
1. Es crearien 100 fils que competirien per les 5 connexions de la base de dades, provocant bloquejos per esgotament del pool (*ConnectionPoolTimeout*).
2. El consum de memòria RAM augmentaria innecessàriament.
Amb el semàfor, limitem a un màxim segur (p. ex. 10) les tasques que poden consultar la BD a la vegada. Les peticions addicionals esperen el seu torn de manera **asíncrona i cooperativa** dins l'Event Loop sense consumir recursos del sistema.

---

## 4. Comparativa de Solucions Alternatives

| Criteri | `asyncio.to_thread` + Semaphore (Nostra Solució) | Driver Asíncron Pur (`asyncpg` + Async SQLAlchemy) |
|---|---|---|
| **Impacte en l'arquitectura existent** | Mínim (tot el domini, serveis i repositoris es mantenen 100% intactes). | Molt elevat (tot el codi ha de convertir-se a `async def`, `async with`, `selectinload`). |
| **Ús de fils** | Utilitza un pool intern de fils (`ThreadPoolExecutor`). | Zero fils addicionals (I/O purament asíncron). |
| **Cancel·lació de consultes** | No és cancel·lable una vegada el fil ha iniciat la query. | Cancel·lació nativa mitjançant cancel·lació de la coroutine. |
| **Risc d'errors** | Molt baix i segur (cada transacció té la seva pròpia sessió aïllada). | Risc d'errors `MissingGreenlet` per càrrega mandrosa (*lazy loading*). |

**Conclusió:** L'enfocament `asyncio.to_thread` acompanyat del semàfor de control de concurrència és la solució òptima per a aquest escenari, ja que proporciona un rendiment pràcticament idèntic al model completament asíncron mantenint una estricta separació de responsabilitats i preservant la integritat de la capa de negoci.
