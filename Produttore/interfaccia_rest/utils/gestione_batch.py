import json
import logging
from typing import Tuple

from costruttore_payload import CostruttorePayload
from merkle_tree import MerkleTree, PathCompatto

from costanti_produttore import BUCKET_MERKLE_PATH
from  ipfs_client import IpfsClient

# Logger del modulo
logger = logging.getLogger(__name__)


def debug_stampa_paths_json(paths: dict[int, PathCompatto], verbose: bool = False) -> None:
    """
    SERVE?
    METODO [DEBUG]
    Stampa compatta delle Merkle Proofs in formato JSON leggibile.
    """
    if not verbose:
        return
    json_serializzabile = {
        str(k) if k != 0 else "batch": {
            "d": p.get_direzione(),
            "h": p.get_hash_fratelli()
        }
        for k, p in paths.items()
    }
    logger.info("📦 MERKLE PROOFS (Formato JSON)")
    separator = "-" * 80
    json_str = json.dumps(json_serializzabile, indent=2)
    logger.debug(f"\n{separator}\n{json_str}\n{separator}")


def costruisci_merkle_tree(payload: CostruttorePayload) -> Tuple[str, str]:
    """
    Costruisce il Merkle Tree a partire da un CostruttorePayload.
    Utilizza la mappa ID → hash (con ID 0 per il batch) già ordinata,
    e restituisce:
      - la Merkle Root
      - i Merkle Path in formato JSON (stringa)
    """
    # Estrazione della mappa id → hash (ordinata all'interno del metodo stesso)
    mappa_id_hash = payload.ottieni_mappa_id_foglie()

    # Estrazione ordinata delle chiavi (ID foglie) e degli hash
    lista_id = list(mappa_id_hash.keys())
    lista_hash = list(mappa_id_hash.values())

    # Costruzione del Merkle Tree
    merkle_tree = MerkleTree(lista_hash, lista_id)
    merkle_root = merkle_tree.costruisci_albero()

    logger.debug(f"Merkle Root calcolata: {merkle_root}")
    # Esportazione dei Merkle Path in formato JSON
    merkle_path_json = merkle_tree.ottieni_merkle_paths_JSON()
    return merkle_root, merkle_path_json



def carica_merkle_path_ipfs(merkle_path: str):
    client = IpfsClient()
    #carica l'oggetto stringa su IPFS e restituisce il nome del file generato internamente
    # dalla classe IPFS in modo che sia univoco in IPFS
    nome_file: str = client.upload_json_string(BUCKET_MERKLE_PATH, merkle_path, comprimi_dimensione=True)
    #recupera il CID a partire dai metadata del file caricato nel bucket dell'utente
    cid = client.recupera_cid_file_bucket(BUCKET_MERKLE_PATH, nome_file)
    return cid
