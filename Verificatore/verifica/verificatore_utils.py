from Classi_comuni.entita.modelli_dati import DatiPayload
from Classi_comuni.merkle_tree import MerkleTree, PathCompatto
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
import json
from typing import Dict

def carica_paths_da_json_string(json_string: str) -> Dict[int, PathCompatto]:
    """
    Converte una stringa JSON proveniente da IPFS in un dizionario di PathCompatto.
    Ogni PathCompatto rappresenta il Merkle Path compatto per una foglia,
    con:
      - key: id_misurazione (o 0 per il batch), convertito da stringa a int
      - value: PathCompatto con attributi 'direzione' e 'hash_fratelli'.

    La stringa JSON deve avere questa forma:
    {
      "0": { "dir": "00101", "hash": ["h1","h2",...] },
      "1": { "dir": "10",    "hash": ["ha","hb"] },
      ...
    }
    """
    try:
        # Caricamento della stringa JSON in un dict Python
        diz = json.loads(json_string)
        #dizionario vuoto
        paths: Dict[int, PathCompatto] = {}

        for key_string, values in diz.items():
            # Converti la stringa chiave in un intero (es. "0" → 0)
            id_foglia = int(key_string)
            # Crea un nuovo oggetto PathCompatto
            path = PathCompatto()
            # Imposta la direzione (es. "00101")
            path.set_direzione(values["dir"])
            # Imposta la lista di hash fratelli nell'esatto ordine
            path.set_hash_fratelli(values["hash"])
            # Aggiungi al dizionario finale
            paths[id_foglia] = path

        return paths

    except (ValueError, KeyError, TypeError) as e:
        # Genera errore dettagliato in caso di formato inaspettato
        raise ValueError(f"Errore nella deserializzazione dei Merkle Path da JSON: {e}")