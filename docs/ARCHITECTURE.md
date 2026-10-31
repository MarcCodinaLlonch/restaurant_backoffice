# Arquitectura del Servidor Asíncron (AsyncIO) — Versió 3.0.0

Aquest document detalla l'arquitectura del sistema Restaurant BackOffice refactoritzat a un model asíncron concurrent no bloquejant basat en la llibreria estàndard `asyncio` de Python.

---

## 1. Visió General i Comparativa (P1 vs P2)

### Pràctica 1 (Model Seqüencial Bloquejant):
- Socket TCP tradicional bloquejant amb `listen(1)` i bucle `accept()` seqüencial.
- Si un client trigava a enviar dades o quedava inactiu, el servidor es congelava a `recv()` i impedia l'entrada de qualsevol altre client.

### Pràctica 2 (Model Asíncron Basat en Tasques i Event Loop):
- Un únic procés i un únic fil principal que executa l'**Event Loop** d'AsyncIO.
- Ús de `asyncio.start_server`: cada client connectat genera automàticament una **Task** independent i concurrent.
- Entrada/Sortida no bloquejant mitjançant `asyncio.StreamReader` i `asyncio.StreamWriter`.
- Desacoblament de l'accés síncron a la Base de Dades mitjançant `RequestDispatcher` (`asyncio.to_thread` + `asyncio.Semaphore`).

---

## 2. Diagrama de Components per Capes

```mermaid
graph TD
    subgraph Clients
        C1["Client 1 (Interactiu Rich)"]
        C2["Client 2 (Interactiu Rich)"]
        CN["Client N (Load Test Client)"]
    end

    subgraph Capa de Xarxa (AsyncIO)
        ATS["AsyncTcpServer (start_server)"]
        CCH["ClientConnectionHandler (1 Task / Client)"]
        RD["RequestDispatcher (to_thread + Semaphore)"]
    end

    subgraph Capa de Protocol
        AR["read_request (StreamReader)"]
        RP["RequestParser (Pura)"]
        RB["ResponseBuilder (HTTP/1.1)"]
        RT["Router (Encaminament)"]
    end

    subgraph Capa de Negoci
        S_CAT["CategoryService"]
        S_DISH["DishService"]
        S_EMP["EmployeeService"]
        S_MENU["MenuService"]
        S_SALE["SaleService"]
    end

    subgraph Capa de Persistència
        UOW["UnitOfWorkFactory / SqlAlchemyUnitOfWork"]
        REPOS["Repositories (Category, Dish, Employee, ...)"]
        PG[("PostgreSQL / SQLite")]
    end

    C1 & C2 & CN -->|TCP Streams| ATS
    ATS -->|Assigna StreamReader / StreamWriter| CCH
    CCH -->|Llegeix de forma asíncrona| AR
    AR -->|Interpreta capçaleres i body| RP
    CCH -->|Delega petició HttpRequest| RD
    RD -->|Offload fora de l'Event Loop| RT
    RT -->|Invoca lògica de negoci| S_CAT & S_DISH & S_EMP & S_MENU & S_SALE
    S_CAT & S_DISH & S_EMP & S_MENU & S_SALE -->|Transaccions atòmiques| UOW
    UOW --> REPOS
    REPOS -->|Queries SQL síncrones| PG
    RT -->|Genera bytes HTTP| RB
    CCH -->|Escriu bytes i drain| C1 & C2 & CN
```

---

## 3. Diagrama de Seqüència Multiclient

El següent diagrama il·lustra el comportament quan dos clients interactuen simultàniament amb el servidor:

```mermaid
sequenceDiagram
    autonumber
    actor ClientA as Client A (GET /categories)
    actor ClientB as Client B (GET /dishes)
    participant Loop as Event Loop (Single Thread)
    participant HandlerA as Task Client A
    participant HandlerB as Task Client B
    participant Dispatcher as RequestDispatcher (to_thread)
    participant ThreadPool as ThreadPoolExecutor
    participant DB as PostgreSQL

    ClientA->>Loop: Connexió TCP
    Loop->>HandlerA: Crea Task Client A
    ClientB->>Loop: Connexió TCP
    Loop->>HandlerB: Crea Task Client B

    Note over HandlerA,HandlerB: Ambdós clients són atesos concurrentment

    ClientA->>HandlerA: Envia HTTP GET /categories
    ClientB->>HandlerB: Envia HTTP GET /dishes

    HandlerA->>Dispatcher: dispatch(req_A)
    Dispatcher->>ThreadPool: Executa router.handle_request en un fil
    ThreadPool->>DB: SELECT * FROM categories (Bloquejant)

    Note over Loop: L'Event Loop no es bloqueja i atén el Client B!

    HandlerB->>Dispatcher: dispatch(req_B)
    Dispatcher->>ThreadPool: Executa router.handle_request en un fil
    ThreadPool->>DB: SELECT * FROM dishes (Bloquejant)

    DB-->>ThreadPool: Retorna files de categories
    ThreadPool-->>Dispatcher: Retorna bytes HTTP 200 OK
    Dispatcher-->>HandlerA: Retorna resposta
    HandlerA->>ClientA: writer.write(response) + await drain()

    DB-->>ThreadPool: Retorna files de plats
    ThreadPool-->>Dispatcher: Retorna bytes HTTP 200 OK
    Dispatcher-->>HandlerB: Retorna resposta
    HandlerB->>ClientB: writer.write(response) + await drain()
```

---

## 4. Gestió del Cicle de Vida i Robustesa

1. **Timeouts de Lectura (`READ_TIMEOUT_SECONDS = 5.0`):**
   Si una connexió roman inactiva sense enviar una petició completa durant el lapse establert, el servidor llança `TimeoutError` i respon amb un codi **408 Request Timeout**, tancant el socket immediatament.

2. **Límit de Cos (`MAX_BODY_SIZE = 1 MB`):**
   Si la capçalera `Content-Length` supera el límit configurat, s'aborta la lectura abans de consumir memòria excessiva i es retorna un codi **413 Payload Too Large**.

3. **Límit Màxim de Connexions Concurrents (`MAX_CONNECTIONS = 50`):**
   Si el nombre de tasques de client actives supera la capacitat configurada, es rebutja l'admissió enviant un codi **503 Service Unavailable**.

4. **Tancament Net (*Graceful Shutdown*):**
   En prémer `Ctrl+C`, el mètode `shutdown()` tanca primer el socket servidor perquè no entrin més clients i atorga un marge de fins a 5 segons perquè les tasques pendents puguin acabar netament.
