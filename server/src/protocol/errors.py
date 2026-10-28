"""
errors.py: Excepcions de domini del protocol HTTP.
"""


class ProtocolError(Exception):
    """Llançada quan una petició HTTP no compleix el format esperat."""
    pass


class PayloadTooLargeError(ProtocolError):
    """Llançada quan el cos de la petició supera el límit permès (per seguretat)."""
    pass