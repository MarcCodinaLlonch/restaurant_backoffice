"""
errors.py: Excepcions de domini del protocol HTTP.
"""


class ProtocolError(Exception):
    """Llançada quan una petició HTTP no compleix el format esperat."""


# CLAU: PayloadTooLargeError hereta de ProtocolError: cas concret d'error de protocol (413 vs 400).
class PayloadTooLargeError(ProtocolError):
    """Llançada quan el cos de la petició supera el límit permès (per seguretat)."""
