import json


def serializza_dict(d: dict) -> str:
    # 1. Serializza il dizionario in una stringa JSON ordinata
    string_json = json.dumps(
        d,
        #indent=2,
        sort_keys=True,  # Ordina le chiavi alfabeticamente
        separators=(",", ":")  # Rimuove gli spazi tra chiavi e valori → output compatto
    )

    return string_json

def canonizza_dict(d: dict) -> dict:
    """
    Canonizza un dizionario JSON:
    - Ordina le chiavi in modo prevedibile
    - Rimuove ambiguità di formattazione
    - Restituisce un dizionario Python normalizzato
    """
    # 1. Serializza il dizionario in una stringa JSON ordinata
    json_string = serializza_dict(d)

    # 2. Deserializza la stringa JSON in un nuovo dizionario canonico
    canonico = json.loads(json_string)

    return canonico

