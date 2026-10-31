"""
request_dispatcher.py: Executa el Router (síncron) FORA de l'event loop.

CONCEPTE: el Router crida els serveis, i els serveis criden SQLAlchemy + psycopg2,
que són BLOQUEJANTS. Si els cridéssim directament dins una coroutine, l'event loop
es quedaria aturat esperant PostgreSQL i cap altre client avançaria.

Solució:
- asyncio.to_thread() executa la funció en un fil del ThreadPoolExecutor.
  La coroutine fa `await` i, mentrestant, l'event loop atén altres clients.
- asyncio.Semaphore limita quantes consultes es fan alhora, perquè el pool
  de connexions de SQLAlchemy només en té unes poques (5 per defecte).
"""

import asyncio

from server.src.protocol.request_parser import HttpRequest
from server.src.protocol.router import Router


class RequestDispatcher:
    """Pont entre el món asíncron (xarxa) i el món síncron (Router + BD)."""

    def __init__(self, router: Router, max_concurrent_calls: int) -> None:
        self._router = router
        self._db_slots = asyncio.Semaphore(max_concurrent_calls)

    async def dispatch(self, request: HttpRequest) -> bytes:
        """Espera un lloc lliure i executa el Router en un fil secundari."""
        async with self._db_slots:
            return await asyncio.to_thread(self._router.handle_request, request)
