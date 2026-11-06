"""
server.py: Punt d'entrada del servidor asíncron (asyncio) de Restaurant BackOffice.

Mateixa estructura que l'exemple de classe:
    server = await asyncio.start_server(handle_client, host, port)
    async with server:
        await server.serve_forever()
"""

import asyncio
import logging
import os
import sys

# Afegim l'arrel del projecte al sys.path per poder importar el paquet 'server'.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.src.bootstrap import create_router, create_uow_factory  # noqa: E402
from server.src.network import ClientConnectionHandler, RequestDispatcher  # noqa: E402
from server.src.persistence.config import (  # noqa: E402
    DB_MAX_CONCURRENCY,
    DB_URL,
    MAX_BODY_SIZE,
    MAX_CONNECTIONS,
    READ_TIMEOUT_SECONDS,
    SERVER_HOST,
    SERVER_PORT,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("server")


async def main() -> None:
    # 1. Persistència i negoci (codi de la Pràctica 1, sense canvis).
    uow_factory = create_uow_factory(DB_URL)
    router = create_router(uow_factory)

    # 2. Capa de xarxa asíncrona (nou a la Pràctica 2).
    dispatcher = RequestDispatcher(router, max_concurrent_calls=DB_MAX_CONCURRENCY)
    handler = ClientConnectionHandler(
        dispatcher=dispatcher,
        read_timeout=READ_TIMEOUT_SECONDS,
        max_body_size=MAX_BODY_SIZE,
        max_connections=MAX_CONNECTIONS,
    )
    server = await asyncio.start_server(handler.handle_client, SERVER_HOST, SERVER_PORT)
    logger.info("Listening on %s:%s (Ctrl+C to stop)", SERVER_HOST, SERVER_PORT)

    try:
        # 'async with' garanteix que el socket d'escolta es tanca en sortir.
        async with server:
            await server.serve_forever()
    finally:
        # Graceful shutdown: tanquem les connexions del pool de la BD.
        uow_factory.engine.dispose()
        logger.info("Server stopped, resources released")


if __name__ == "__main__":
    if not DB_URL:
        sys.exit("Error: no database URL configured (check the .env file).")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Ctrl+C: el 'finally' de main() ja ha fet la neteja.
