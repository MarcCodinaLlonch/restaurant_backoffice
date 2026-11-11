"""
async_request_reader.py: Lector asíncron de peticions HTTP sobre asyncio.StreamReader.
"""

import asyncio
import hashlib

from .errors import PayloadTooLargeError, ProtocolError
from .request_parser import HttpRequest, RequestParser


async def read_request(
    reader: asyncio.StreamReader,
    max_body_size: int = 1_048_576,  # 1 MB per defecte
) -> HttpRequest | None:
    """
    Llegeix una petició HTTP/1.1 completa d'un StreamReader.

    Retorna:
        - HttpRequest si la petició s'ha llegit i analitzat correctament.
        - None si el client ha tancat la connexió de manera neta (EOF) sense enviar dades.

    Llança:
        - ProtocolError: Si les capçaleres estan mal formades, incompletes o superen el límit.
        - PayloadTooLargeError: Si el Content-Length supera max_body_size.
    """
    try:
        # CLAU: lectura en dos temps (framing TCP): la línia buida marca el final de capçaleres.
        # readuntil és de StreamReader; només cedeix el torn si les dades encara no han arribat.
        head = await reader.readuntil(b"\r\n\r\n")
    except asyncio.IncompleteReadError as exc:
        # CLAU: exc.partial buit vol dir tancament net (EOF) -> None; si porta dades -> error.
        if not exc.partial:
            # EOF net: el client s'ha desconnectat sense demanar res
            return None
        raise ProtocolError("Capçaleres HTTP incompletes.") from exc
    except asyncio.LimitOverrunError as exc:
        raise ProtocolError("Capçaleres HTTP massa grans.") from exc

    request = RequestParser.parse_head(head)

    raw_content_length = request.headers.get("content-length", "0")
    try:
        content_length = int(raw_content_length)
        if content_length < 0:
            raise ValueError()
    except ValueError:
        raise ProtocolError(f"Content-Length invàlid: {raw_content_length}")

    # CLAU: comprovem max_body_size ABANS de llegir el cos del socket per seguretat (413).
    if content_length > max_body_size:
        raise PayloadTooLargeError(
            f"El cos ({content_length} bytes) supera el límit permès ({max_body_size} bytes)."
        )

    # CLAU: readexactly llegeix N bytes de cos; a GET i DELETE (content_length 0) no s'executa.
    if content_length > 0:
        try:
            raw_body = await reader.readexactly(content_length)
        except asyncio.IncompleteReadError as exc:
            raise ProtocolError(
                f"Connexió tancada abans de rebre tot el cos "
                f"({len(exc.partial)}/{content_length} bytes)."
            ) from exc

        # CLAU (Pràctica 3): si la petició inclou Content-Hash, verifiquem la integritat SHA-256
        # del cos rebut abans de fer el json.loads.
        expected_hash = request.headers.get("content-hash")
        if expected_hash is not None:
            actual_hash = hashlib.sha256(raw_body).hexdigest()
            if actual_hash != expected_hash:
                raise ProtocolError(
                    "Integritat fallida: el Content-Hash no coincideix amb el cos rebut."
                )

        content_type = request.headers.get("content-type", "")
        request.body = RequestParser.parse_body(raw_body, content_type)

    return request
