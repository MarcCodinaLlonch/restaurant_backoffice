"""
async_request_reader.py: Lector asíncron de peticions HTTP sobre asyncio.StreamReader.
"""

import asyncio

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
        head = await reader.readuntil(b"\r\n\r\n")
    except asyncio.IncompleteReadError as exc:
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

    if content_length > max_body_size:
        raise PayloadTooLargeError(
            f"El cos ({content_length} bytes) supera el límit permès ({max_body_size} bytes)."
        )

    if content_length > 0:
        try:
            raw_body = await reader.readexactly(content_length)
        except asyncio.IncompleteReadError as exc:
            raise ProtocolError(
                f"Connexió tancada abans de rebre tot el cos "
                f"({len(exc.partial)}/{content_length} bytes)."
            ) from exc

        content_type = request.headers.get("content-type", "")
        request.body = RequestParser.parse_body(raw_body, content_type)

    return request
