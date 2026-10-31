"""
async_server.py: Servidor TCP basat en asyncio.start_server amb registre de connexions
i procediment d'aturada controlada (Graceful Shutdown).
"""

import asyncio
import logging

from .connection_handler import ClientConnectionHandler

logger = logging.getLogger(__name__)


class AsyncTcpServer:
    """
    Servidor TCP asíncron que accepta connexions concurrents,
    manté un registre de tasques actives i suporta graceful shutdown.
    """

    def __init__(self, host: str, port: int, handler: ClientConnectionHandler) -> None:
        self.host = host
        self.port = port
        self.handler = handler
        self._server: asyncio.Server | None = None
        self._active_tasks: set[asyncio.Task] = set()
        self.handler.set_active_tasks_registry(self._active_tasks)

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

        try:
            async with self._server:
                await self._server.serve_forever()
        except asyncio.CancelledError:
            logger.info("Rebuda petició d'aturada. Iniciant Graceful Shutdown...")
        finally:
            await self.shutdown()

    async def shutdown(self, timeout: float = 5.0) -> None:
        """
        Atura l'admissió de noves connexions i dóna un marge de temps
        perquè les tasques actives finalitzin de forma neta.
        """
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("Socket del servidor tancat per a noves connexions.")

        if self._active_tasks:
            logger.info(
                "Esperant que finalitzin %d connexions actives (timeout: %.1fs)...",
                len(self._active_tasks),
                timeout,
            )
            done, pending = await asyncio.wait(self._active_tasks, timeout=timeout)
            if pending:
                logger.warning(
                    "Forçant cancel·lació de %d tasques que no han respost a temps.",
                    len(pending),
                )
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)

        logger.info(
            "Graceful shutdown completat. Tots els recursos han estat alliberats."
        )
