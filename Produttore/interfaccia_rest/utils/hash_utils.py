import hashlib

def calcola_hash(dato: str) -> str:
    """
    Calcola l'hash SHA-256 del dato passato.
    """
    return hashlib.sha256(dato.encode("utf-8")).hexdigest()

