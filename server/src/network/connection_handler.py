"""
connection_handler.py: Gestiona el cicle de vida d'una connexió de client individual.
Inclou detecció de desconnexions, timeouts, límits de concurrència i tancament net.
"""

import asyncio
import contextlib
import logging

from server.src.protocol.async_request_reader import read_request
from server.src.protocol.errors import PayloadTooLargeError, ProtocolError
from server.src.protocol.response_builder import ResponseBuilder

from .request_dispatcher import RequestDispatcher

logger = logging.getLogger(__name__)


class ClientConnectionHandler:
    """
    Atén una connexió de client utilitzant StreamReader i StreamWriter.
    Gestiona timeouts de lectura, límits de mida i concurrència màxima.
    """

    def __init__(
        self,
        dispatcher: RequestDispatcher,
        max_body_size: int = 1_048_576,
        read_timeout: float = 5.0,
        max_connections: int = 50,
        active_tasks: set[asyncio.Task] | None = None,
    ) -> None:
        self._dispatcher = dispatcher
        self._max_body_size = max_body_size
        self._read_timeout = read_timeout
        self._max_connections = max_connections
        self._active_tasks: set[asyncio.Task] = (
            active_tasks if active_tasks is not None else set()
        )

    def set_active_tasks_registry(self, registry: set[asyncio.Task]) -> None:
        """Assigna el registre compartit de tasques actives."""
        self._active_tasks = registry

    async def _send(self, writer: asyncio.StreamWriter, data: bytes) -> None:
        """Escriu dades al socket i buida el buffer (backpressure)."""
        writer.write(data)
        await writer.drain()

    async def _send_safely(self, writer: asyncio.StreamWriter, data: bytes) -> None:
        """Envia dades ignorant silenciosament si el client ja s'havia desconnectat."""
        try:
            await self._send(writer, data)
        except (ConnectionError, BrokenPipeError, ConnectionResetError):
            pass

    async def handle(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Executat automàticament en una Task nova per cada client que es connecta.
        """
        current_task = asyncio.current_task()
        if current_task:
            self._active_tasks.add(current_task)

        peer = writer.get_extra_info("peername")
        logger.info(
            "Connexió acceptada des de %s (Clients actius: %d)",
            peer,
            len(self._active_tasks),
        )

        try:
            # 1. Comprovació de límit màxim de connexions (503 Service Unavailable)
            if len(self._active_tasks) > self._max_connections:
                logger.warning(
                    "Límit màxim de connexions assolit (%d). Rebutjant %s",
                    self._max_connections,
                    peer,
                )
                await self._send_safely(
                    writer,
                    ResponseBuilder.service_unavailable(
                        "Servidor saturat. Torna a intentar-ho."
                    ),
                )
                return

            # 2. Lectura amb timeout de seguretat (evita bloquejos per clients inactius)
            try:
                async with asyncio.timeout(self._read_timeout):
                    request = await read_request(reader, self._max_body_size)
            except TimeoutError:
                logger.warning("Timeout de lectura esgotat amb el client %s", peer)
                await self._send_safely(writer, ResponseBuilder.request_timeout())
                return

            if request is None:
                logger.info(
                    "El client %s ha tancat la connexió de manera neta (EOF).", peer
                )
                return

            logger.info(
                "Petició rebuda de %s: %s %s", peer, request.method, request.raw_path
            )

            # 3. Execució de la consulta fora del loop via RequestDispatcher
            response_bytes = await self._dispatcher.dispatch(request)
            await self._send(writer, response_bytes)

        except PayloadTooLargeError as exc:
            logger.warning("El client %s ha superat la mida de cos: %s", peer, exc)
            await self._send_safely(writer, ResponseBuilder.payload_too_large(str(exc)))
        except ProtocolError as exc:
            logger.warning("Error de protocol amb el client %s: %s", peer, exc)
            await self._send_safely(writer, ResponseBuilder.bad_request(str(exc)))
        except (ConnectionResetError, BrokenPipeError, asyncio.IncompleteReadError):
            logger.warning("El client %s s'ha desconnectat abruptament.", peer)
        except asyncio.CancelledError:
            # Permet la cancel·lació cooperativa en cas de graceful shutdown
            raise
        except Exception:
            logger.exception("Error inesperat atenent el client %s", peer)
            await self._send_safely(writer, ResponseBuilder.internal_error())
        finally:
            if current_task:
                self._active_tasks.discard(current_task)
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            logger.info("Connexió amb %s tancada correctament.", peer)
