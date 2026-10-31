"""
server.py: Punt d'entrada del servidor TCP asíncron per a Restaurant BackOffice.
"""
import asyncio
import logging
import os
import sys

# Assegurem que l'arrel del projecte és la primera ruta de sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.src import bootstrap
from server.src.network import AsyncTcpServer, ClientConnectionHandler, RequestDispatcher
from server.src.persistence.config import (
    DB_URL,
    SERVER_HOST,
    SERVER_PORT,
    READ_TIMEOUT_SECONDS,
    MAX_BODY_SIZE,
    MAX_CONNECTIONS,
    DB_MAX_CONCURRENCY,
)

# Configuració de logging professional (reemplaça els antics print)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")


async def main() -> None:
    banner = r"""
  ==============================================================
   RESTAURANT BACKOFFICE — SERVIDOR ASÍNCRON TCP (AsyncIO)
   Arquitectura: Una Task concurrent per client (Non-blocking I/O)
  ==============================================================
    """
    print(banner)

    # 1. Inicialitzem la base de dades
    bootstrap.init_database(DB_URL)

    # 2. Creem l'enrutador amb tots els serveis i el despatxador fora de l'Event Loop
    router = bootstrap.create_router(DB_URL)
    dispatcher = RequestDispatcher(router, max_concurrent_calls=DB_MAX_CONCURRENCY)

    # 3. Creem el controlador de connexions amb límits i timeouts de seguretat
    handler = ClientConnectionHandler(
        dispatcher=dispatcher,
        max_body_size=MAX_BODY_SIZE,
        read_timeout=READ_TIMEOUT_SECONDS,
        max_connections=MAX_CONNECTIONS,
    )

    # 4. Instanciem el servidor asíncron amb suport per a Graceful Shutdown
    server = AsyncTcpServer(SERVER_HOST, SERVER_PORT, handler)

    # 5. Comencem a escoltar peticions indefinidament
    await server.serve_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Servidor aturat per l'usuari (Ctrl+C).")
