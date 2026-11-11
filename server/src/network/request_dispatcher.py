"""request_dispatcher.py: executa el Router en un fil secundari
perquè la BD no bloquegi l'event loop."""

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
        # CLAU: Semaphore(5) = mida del pool de SQLAlchemy; async with allibera el lloc
        # fins i tot amb error.
        async with self._db_slots:
            # CLAU: SQLAlchemy+psycopg2 bloquegen; to_thread rep la funció sense parèntesis
            # i l'executa en un fil secundari (repte investigat no implementat: asyncpg).
            return await asyncio.to_thread(self._router.handle_request, request)
