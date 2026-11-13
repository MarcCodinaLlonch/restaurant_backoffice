"""digest.py: càlcul i verificació del digest SHA-256 (Content-Hash) per a cossos HTTP."""

import hashlib
import hmac

DIGEST_HEADER = "Content-Hash"


def compute_digest(body: bytes) -> str:
    """Calcula el digest SHA-256 en hexadecimal d'un cos de missatge HTTP."""
    # CLAU (Pràctica 3): resum criptogràfic SHA-256 (64 caràcters hex) dels bytes del cos.
    return hashlib.sha256(body).hexdigest()


def verify_digest(body: bytes, received: str | None) -> bool:
    """
    Comprova que el digest SHA-256 rebut coincideixi amb el calculat sobre `body`.
    Retorna False si `received` és None o buit.
    """
    if not received or not received.strip():
        return False
    expected = compute_digest(body)
    # CLAU (Pràctica 3): fem servir hmac.compare_digest perquè fa una comparació en temps
    # constant i evita atacs de temps (timing attacks) en comparar resums criptogràfics.
    return hmac.compare_digest(expected, received.strip().lower())
