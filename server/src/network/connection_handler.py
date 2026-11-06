"""
connection_handler.py: Gestiona la vida d'UNA connexió de client.

CONCEPTE: asyncio.start_server() crea una Task nova per cada client i hi executa
handle_client(reader, writer). Cada client té la seva Task, i totes comparteixen
un sol fil (l'event loop). Quan una Task fa `await`, cedeix el torn a les altres.

Cicle de vida d'una connexió (protocol stateless: 1 connexió = 1 petició):
    connecta -> llegim la petició -> la processem -> responem -> tanquem
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
    """Atén cada client: llegeix, processa, respon i tanca SEMPRE la connexió."""

    def __init__(
        self,
        dispatcher: RequestDispatcher,
        read_timeout: float,
        max_body_size: int,
        max_connections: int,
    ) -> None:
        self._dispatcher = dispatcher
        self._read_timeout = read_timeout
        self._max_body_size = max_body_size
        self._max_connections = max_connections
        # Comptador simple. No cal Lock: només el toca el fil de l'event loop.
        self._active_connections = 0

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Punt d'entrada: asyncio l'executa en una Task nova per cada client."""
        client_address = writer.get_extra_info("peername")
        self._active_connections += 1
        logger.info("Client connected: %s (active: %d)", client_address, self._active_connections)
        try:
            response = await self._build_response(reader, client_address)
            if response is not None:
                writer.write(response)
                await writer.drain()  # CONCEPTE: backpressure
        except ConnectionError:
            # Inclou ConnectionResetError i BrokenPipeError: el client ha marxat de cop.
            logger.warning("Client %s disconnected abruptly", client_address)
        except Exception:
            # Error inesperat: només falla AQUESTA Task, el servidor continua.
            logger.exception("Unexpected error with client %s", client_address)
        finally:
            # Passi el que passi, alliberem el socket (evitem fuites de recursos).
            self._active_connections -= 1
            writer.close()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()
            logger.info(
                "Connection closed: %s (active: %d)",
                client_address,
                self._active_connections,
            )

    async def _build_response(
        self, reader: asyncio.StreamReader, client_address: object
    ) -> bytes | None:
        """Decideix QUÈ hem de respondre. Retorna None si el client ja no espera res."""
        if self._active_connections > self._max_connections:
            return ResponseBuilder.service_unavailable("Server busy, try again later.")

        try:
            # Si el client no envia la petició sencera a temps -> 408.
            async with asyncio.timeout(self._read_timeout):
                request = await read_request(reader, self._max_body_size)
        except TimeoutError:
            logger.warning("Read timeout with client %s", client_address)
            return ResponseBuilder.request_timeout()
        except PayloadTooLargeError as error:
            return ResponseBuilder.payload_too_large(str(error))
        except ProtocolError as error:
            logger.warning("Protocol error with client %s: %s", client_address, error)
            return ResponseBuilder.bad_request(str(error))

        if request is None:
            logger.info("Client %s closed without sending a request", client_address)
            return None

        logger.info("%s %s from %s", request.method, request.raw_path, client_address)
        return await self._dispatcher.dispatch(request)
