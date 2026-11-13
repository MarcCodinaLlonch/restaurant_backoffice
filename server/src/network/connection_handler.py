"""connection_handler.py: atén cada client connectat (una Task per client)."""

import asyncio
import contextlib
import logging

from server.src.protocol.async_request_reader import read_request
from server.src.protocol.errors import PayloadTooLargeError, ProtocolError
from server.src.protocol.response_builder import ResponseBuilder
from server.src.protocol.router import Router

logger = logging.getLogger(__name__)


class ClientConnectionHandler:
    """Atén cada client: llegeix, processa, respon i tanca SEMPRE la connexió."""

    def __init__(
        self,
        router: Router,
        read_timeout: float,
        max_body_size: int,
    ) -> None:
        self._router = router
        self._read_timeout = read_timeout
        self._max_body_size = max_body_size

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Punt d'entrada: asyncio l'executa en una Task nova per cada client."""
        # CLAU: reader ("l'orella") i writer ("la boca") per connexió; 1 connexió = 1 petició
        # (stateless).
        client_address = writer.get_extra_info("peername")
        logger.info("Client connected: %s", client_address)
        # CLAU (Pràctica 3): el handshake TLS fa un intercanvi de clau efímer (ECDHE,
        # Diffie-Hellman) i després xifra el trànsit amb una clau simètrica AES-GCM.
        ssl_object = writer.get_extra_info("ssl_object")
        if ssl_object is not None:
            cipher = ssl_object.cipher()
            logger.info(
                "TLS session with %s: %s, %s",
                client_address,
                ssl_object.version(),
                cipher[0] if cipher else "unknown",
            )
        try:
            # CLAU: mentre espera la resposta, la Task es pausa i l'event loop atén altres clients.
            response = await self._build_response(reader, client_address)
            if response is not None:
                # CLAU: write només prepara els bytes al buffer; drain espera que surtin
                # (backpressure).
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
            writer.close()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()
            logger.info("Connection closed: %s", client_address)

    async def _build_response(
        self, reader: asyncio.StreamReader, client_address: object
    ) -> bytes | None:
        """Decideix QUÈ hem de respondre. Retorna None si el client ja no espera res."""
        try:
            # Si el client no envia la petició sencera a temps -> 408.
            # CLAU: el cronòmetre engloba TOTA la lectura (capçaleres + cos)
            # per evitar bloquejos (408).
            async with asyncio.timeout(self._read_timeout):
                request = await read_request(reader, self._max_body_size)
        except TimeoutError:
            logger.warning("Read timeout with client %s", client_address)
            return ResponseBuilder.request_timeout()
        # CLAU: PayloadTooLargeError abans de ProtocolError perquè n'és filla (evita 400).
        # Retornem bytes d'error directament; la petició no arriba a la base de dades.
        except PayloadTooLargeError as error:
            return ResponseBuilder.payload_too_large(str(error))
        except ProtocolError as error:
            logger.warning("Protocol error with client %s: %s", client_address, error)
            return ResponseBuilder.bad_request(str(error))

        # CLAU: si request és None el client ha tancat la connexió neta (EOF); no es respon res.
        if request is None:
            logger.info("Client %s closed without sending a request", client_address)
            return None

        logger.info("%s %s from %s", request.method, request.raw_path, client_address)
        # CLAU: el Router (i la BD) és síncron i es crida directament, sense await.
        # Les consultes duren pocs ms: mentrestant les altres Tasks esperen el seu torn.
        return self._router.handle_request(request)
