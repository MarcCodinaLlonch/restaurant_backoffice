"""server.py: punt d'entrada del servidor asíncron. Munta les capes i escolta al port 8088."""

import asyncio
import logging
import os
import sys

# Afegim l'arrel del projecte al sys.path per poder importar el paquet 'server'.
# CLAU: afegim l'arrel a sys.path perquè 'import server...' funcioni
# executant 'python server/server.py'.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if current_dir in sys.path:
    sys.path.remove(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from server.src.bootstrap import create_router, create_uow_factory  # noqa: E402
from server.src.network import ClientConnectionHandler  # noqa: E402
from server.src.persistence.config import (  # noqa: E402
    DB_URL,
    MAX_BODY_SIZE,
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
    handler = ClientConnectionHandler(
        router=router,
        read_timeout=READ_TIMEOUT_SECONDS,
        max_body_size=MAX_BODY_SIZE,
    )
    # CLAU: handle_client va sense parèntesis; asyncio la crida en una Task nova per client.
    server = await asyncio.start_server(handler.handle_client, SERVER_HOST, SERVER_PORT)
    logger.info("Listening on %s:%s (Ctrl+C to stop)", SERVER_HOST, SERVER_PORT)

    try:
        # 'async with' garanteix que el socket d'escolta es tanca en sortir.
        async with server:
            # CLAU: el servidor queda escoltant; si no arriba ningú, l'event loop no gasta CPU.
            await server.serve_forever()
    finally:
        # Graceful shutdown: tanquem les connexions del pool de la BD.
        uow_factory.engine.dispose()
        logger.info("Server stopped, resources released")


if __name__ == "__main__":
    if not DB_URL:
        sys.exit("Error: no database URL configured (check the .env file).")
    try:
        # CLAU: crea l'event loop d'un sol fil compartit per a tots els clients.
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Ctrl+C: el 'finally' de main() ja ha fet la neteja.
