import json
import logging
from typing import Tuple

from costruttore_payload import CostruttorePayload
from merkle_tree import MerkleTree, PathCompatto

from costanti_produttore import BUCKET_MERKLE_PATH
from ipfs_client import IpfsClient

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
    # ----Creazione del Merkle Tree, Merkle Root, Merkle Path----#
    # A partire dall'oggetto da inviare al cloud estraggo una lista di hash
    # di cui n-1 sono tuple della tab. Misurazione e l'ultima è la tupla della tabella Batch
    # di riferimento contenuta nel database
    foglie_hash = payload.get_foglie_hash()
    merkle_tree = MerkleTree(foglie_hash)
    # mappa degli id utilizzata per la costruzione dei merkle path
    mappa_id = payload.get_id_misurazioni()
    # radice dell'albero
    merkle_root = merkle_tree.costruisci_albero(mappa_id=mappa_id)
    logger.debug(f" Merkle Root calcolata {merkle_root}")
    # merkle path come stringa JSON strutturata
    merkle_path = merkle_tree.get_paths_JSON()
    #logger.debug(f"Merkle path calcolati {merkle_path}")
    return merkle_root, merkle_path


def carica_merkle_path_ipfs(merkle_path: str):
    #funzione privata utilizzata solo internamente alla classe
    client = IpfsClient()
    #carica l'oggetto stringa su IPFS e restituisce il nome del file generato internamente
    # dalla classe IPFS in modo che sia univoco in IPFS
    nome_file: str = client.upload_json_string(BUCKET_MERKLE_PATH, merkle_path, comprimi_dimensione=False)
    #recupera il CID a partire dai metadata del file caricato nel bucket dell'utente
    cid = client.recupera_cid_file_bucket(BUCKET_MERKLE_PATH, nome_file)
    return cid
