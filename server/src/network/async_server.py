"""
async_server.py: Servidor TCP basat en asyncio.start_server.
"""
import asyncio
import logging
from typing import Optional

from .connection_handler import ClientConnectionHandler

logger = logging.getLogger(__name__)


class AsyncTcpServer:
    """
    Servidor TCP asíncron que accepta connexions concurrents
    i delega cada client a una Task independent de ClientConnectionHandler.
    """

    def __init__(self, host: str, port: int, handler: ClientConnectionHandler) -> None:
        self.host = host
        self.port = port
        self.handler = handler
        self._server: Optional[asyncio.Server] = None

    async def serve_forever(self) -> None:
        """Inicia el servidor d'AsyncIO i roman escoltant peticions."""
        self._server = await asyncio.start_server(
            self.handler.handle,
            self.host,
            self.port,
        )

        sockets = self._server.sockets or []
        addresses = ", ".join(str(sock.getsockname()) for sock in sockets)
        logger.info("Servidor TCP Asíncron escoltant a %s", addresses)
        logger.info("Model: Una Task per client sobre un únic Event Loop")

        async with self._server:
            await self._server.serve_forever()