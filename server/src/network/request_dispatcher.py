"""
request_dispatcher.py: Executa el Router síncron fora de l'Event Loop
mitjançant asyncio.to_thread i controla la concurrència amb un Semaphore.
"""

import asyncio

from server.src.protocol.request_parser import HttpRequest
from server.src.protocol.router import Router


class RequestDispatcher:
    """
    Intermediari entre el ConnectionHandler asíncron i el Router síncron.
    Assegura que les consultes a la BD no bloquegin l'Event Loop.
    """

    def __init__(self, router: Router, max_concurrent_calls: int = 10) -> None:
        self._router = router
        self._db_slots = asyncio.Semaphore(max_concurrent_calls)

    async def dispatch(self, request: HttpRequest) -> bytes:
        """
        Adquireix un slot del semàfor i executa handle_request en un fil separat.
        """
        async with self._db_slots:
            return await asyncio.to_thread(self._router.handle_request, request)
