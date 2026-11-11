# Asynchronous Server Architecture (asyncio): Restaurant BackOffice v3.0

> **Language:** [English](ARCHITECTURE_ENG.md) | [Català](ARCHITECTURE_CAT.md)

## 1. Summary

- **Practice 1:** TCP server with blocking sockets. Handled **one client at a time**: while waiting for `recv()`, other clients queued up.
- **Practice 2:** Server with `asyncio.start_server`. Each client has **its own Task** and all share **a single thread** (the event loop). When a Task executes `await`, it yields control to the others.
- The database (SQLAlchemy + psycopg2) is **synchronous** and the Router is called **directly** from the event loop: queries take a few milliseconds. The impact is analysed in [DB_ACCESS_ANALYSIS_ENG.md](DB_ACCESS_ANALYSIS_ENG.md).
- The protocol, business logic, and persistence layers from Practice 1 are reused **without changes**.

## 2. Layer Diagram

![Layer Diagram](img/architecture.png)

```mermaid
flowchart TD
    subgraph CLIENTS["Clients (N at once)"]
        C1["client.py (interactive menu)"]
        C2["load_test_client.py (N clients with gather)"]
    end

    subgraph NET["Network layer - asyncio (NEW in P2)"]
        SS["asyncio.start_server (server.py)"]
        CH["ClientConnectionHandler.handle_client (1 Task per client)"]
        RR["read_request (StreamReader)"]
    end

    subgraph PROTO["Protocol layer (P1)"]
        RP["RequestParser"]
        RT["Router"]
        RB["ResponseBuilder"]
    end

    subgraph BUS["Business layer (P1)"]
        SV["Services (Category, Dish, Menu...)"]
    end

    subgraph PERS["Persistence layer (P1)"]
        UOW["UnitOfWork + Repositories"]
        DB[("PostgreSQL")]
    end

    C1 -- "TCP: HTTP/1.1 + JSON" --> SS
    C2 -- "TCP: HTTP/1.1 + JSON" --> SS
    SS -- "creates a Task" --> CH
    CH -- "await" --> RR
    RR --> RP
    CH -- "direct call (synchronous)" --> RT
    RT --> SV
    SV --> UOW
    UOW -- "synchronous SQL (a few ms)" --> DB
    RT --> RB
```

## 3. Sequence Diagram: 2 Concurrent Clients

![Sequence Diagram](img/sequence.png)

```mermaid
sequenceDiagram
    autonumber
    participant A as Client A
    participant B as Client B
    participant EL as Event loop (1 thread)
    participant DB as PostgreSQL

    A->>EL: connects (start_server creates Task A)
    B->>EL: connects (start_server creates Task B)
    Note over EL: Task A: await read_request() (waits for the network, the loop is free)
    B->>EL: GET /categories
    Note over EL: Task B: request complete
    EL->>DB: Task B: router.handle_request() (synchronous, a few ms)
    DB-->>EL: category rows
    EL-->>B: write() + await drain(), close()
    A->>EL: GET /dishes (arrives later)
    EL->>DB: Task A: router.handle_request() (synchronous, a few ms)
    DB-->>EL: dish rows
    EL-->>A: write() + await drain(), close()
```

## 4. Before vs After

![Before vs After](img/before_after.png)

```mermaid
flowchart LR
    subgraph P1["P1: Blocking Socket"]
        direction TB
        X1["accept() client 1"] --> X2["recv() waiting... (blocked)"] --> X3["response, close()"] --> X4["accept() client 2"]
    end
    subgraph P2["P2: asyncio"]
        direction TB
        Y0["event loop"] --> Y1["Task client 1"]
        Y0 --> Y2["Task client 2"]
        Y0 --> Y3["Task client N"]
    end
```

## 5. File → Responsibility

| File | Responsibility |
|---|---|
| `server/server.py` | Assembles components and starts `asyncio.start_server` (`async with server` + `serve_forever`) |
| `server/src/network/connection_handler.py` | Lifecycle of ONE connection: read → process → reply → close |
| `server/src/protocol/async_request_reader.py` | `read_request()`: reads an HTTP request from `StreamReader` (headers + `Content-Length`) |
| `server/src/protocol/request_parser.py` | `RequestParser`: pure parsing functions, bytes → `HttpRequest` |
| `server/src/protocol/router.py` | `Router`: routes requests to matching services by method and path (P1 code) |
| `server/src/protocol/response_builder.py` | `ResponseBuilder`: constructs HTTP response bytes (200, 400, 404, 408, 413...) |
| `server/src/services/` | Business logic and validations (P1 code, unmodified) |
| `server/src/persistence/` | ORM models, repositories, Unit of Work, and the single SQLAlchemy engine |
| `server/src/bootstrap.py` | Layer wiring: persistence → services → router |

## 6. Connection Lifecycle

Stateless protocol: **1 connection = 1 request**.

1. The client connects and `asyncio.start_server` spawns a **new Task** running `handle_client(reader, writer)`.
2. `read_request()` reads the request bounded by `asyncio.timeout(READ_TIMEOUT_SECONDS)`.
3. `router.handle_request(request)` is called directly (synchronous): Router → Services → DB, a few milliseconds.
4. `writer.write(response)` + `await writer.drain()` (*backpressure*).
5. `finally`: `writer.close()` + `await writer.wait_closed()`. The socket is **always closed**, even upon errors.

An unhandled error only crashes that specific client Task; the server keeps running and serving other clients.

| Limit (`.env`) | Default Value | Consequence when Exceeded |
|---|---|---|
| `READ_TIMEOUT_SECONDS` | 5 s | **408** Request Timeout |
| `MAX_BODY_SIZE` | 1 MB | **413** Payload Too Large |

## 7. Graceful Shutdown

1. Ctrl+C causes `asyncio.run` to cancel the `main()` Task.
2. `serve_forever()` receives cancellation.
3. Exiting `async with server` triggers `server.close()` and `wait_closed()`: stops accepting new clients and closes the listening socket.
4. In `main()`'s `finally` block, `engine.dispose()` tears down DB connections.
5. `asyncio.run` re-raises `KeyboardInterrupt`, cleanly handled in `__main__`. The server exits printing `Server stopped, resources released` without tracebacks.

`CancelledError` is **not** swallowed: inheriting from `BaseException`, it bypasses `except Exception`, allowing clean cancellation semantics.
