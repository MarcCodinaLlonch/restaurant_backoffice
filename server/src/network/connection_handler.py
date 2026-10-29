"""
connection_handler.py: Gestiona el cicle de vida d'una connexió de client individual.
"""
import asyncio
import contextlib
import logging

from server.src.protocol.async_request_reader import read_request
from server.src.protocol.errors import ProtocolError, PayloadTooLargeError
from server.src.protocol.response_builder import ResponseBuilder
from server.src.protocol.router import Router

logger = logging.getLogger(__name__)


class ClientConnectionHandler:
    """
    Atén una connexió de client utilitzant StreamReader i StreamWriter.
    """

    def __init__(self, router: Router, max_body_size: int = 1_048_576) -> None:
        self._router = router
        self._max_body_size = max_body_size

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Executat automàticament en una Task nova per cada client que es connecta.
        """
        peer = writer.get_extra_info("peername")
        logger.info("Connexió acceptada des de %s", peer)

        try:
            request = await read_request(reader, self._max_body_size)
            if request is None:
                logger.info("El client %s ha tancat la connexió sense enviar dades.", peer)
                return

            logger.info("Petició rebuda de %s: %s %s", peer, request.method, request.raw_path)

            # Processament síncron de la petició mitjançant el Router
            response_bytes = self._router.handle_request(request)

            writer.write(response_bytes)
            await writer.drain()

        except PayloadTooLargeError as exc:
            logger.warning("El client %s ha superat la mida de cos: %s", peer, exc)
            writer.write(ResponseBuilder.payload_too_large(str(exc)))
            await writer.drain()
        except ProtocolError as exc:
            logger.warning("Error de protocol amb el client %s: %s", peer, exc)
            writer.write(ResponseBuilder.bad_request(str(exc)))
            await writer.drain()
        except Exception:
            logger.exception("Error inesperat atenent el client %s", peer)
            writer.write(ResponseBuilder.internal_error())
            await writer.drain()
        finally:
            writer.close()
            with contextlib.suppress(Exception):
                await writer.wait_closed()
            logger.info("Connexió amb %s tancada correctament.", peer)