import hashlib
import json

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



import json

def canonizza_dict(d: dict) -> dict:
    """
    Canonizza un dizionario JSON:
    - Ordina le chiavi in modo prevedibile
    - Rimuove ambiguità di formattazione
    - Restituisce un dizionario Python normalizzato
    """
    # 1. Serializza il dizionario in una stringa JSON ordinata
    json_string = json.dumps(
        d,
        sort_keys=True,           # Ordina le chiavi alfabeticamente
        separators=(",", ":")     # Rimuove gli spazi tra chiavi e valori → output compatto
    )

    # 2. Deserializza la stringa JSON in un nuovo dizionario canonico
    canonico = json.loads(json_string)

    return canonico

def differenze_dizionari(base: dict, modificato: dict) -> dict:
    """
    Confronta due dizionari JSON.
    - `base`: dizionario originale (trusted, lato produttore)
    - `modificato`: dizionario ricevuto (es. dal cloud)

    Ritorna un dizionario con tutte le differenze:
    - chiavi con valori diversi
    - chiavi mancanti nel modificato
    - chiavi aggiunte nel modificato
    """
    differenze = {}

    # Insieme unificato di tutte le chiavi
    tutte_le_chiavi = set(base.keys()) | set(modificato.keys())

    for chiave in tutte_le_chiavi:
        val_base = base.get(chiave)
        val_mod = modificato.get(chiave)

        if chiave not in modificato:
            # Chiave mancante nel cloud
            differenze[chiave] = {"locale": val_base, "cloud": None}
        elif chiave not in base:
            # Chiave aggiunta dal cloud
            differenze[chiave] = {"locale": None, "cloud": val_mod}
        elif val_base != val_mod:
            # Chiave presente in entrambi ma con valori diversi
            differenze[chiave] = {"locale": val_base, "cloud": val_mod}

    return differenze

