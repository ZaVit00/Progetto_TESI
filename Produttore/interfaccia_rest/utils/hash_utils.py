import hashlib


class Hashing:
    @staticmethod
    def calcola_hash(dato: str) -> str:
        """
        Calcola l'hash SHA-256 del dato passato.
        """
        return hashlib.sha256(dato.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_concat(elem_sx: str, elem_dx: str) -> str:
        """
            Calcola l'hash SHA - 256 di una stringa ottenuta come
            la concatenazione di due stringhe
            """
        return Hashing.calcola_hash(elem_sx + elem_dx)

def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0