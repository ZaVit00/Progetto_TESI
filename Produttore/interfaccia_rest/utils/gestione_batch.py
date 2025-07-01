import logging
from typing import Tuple

from api_cloud import logger
from costanti_produttore import BUCKET_MERKLE_PATH, ERRORE_BLOCKCHAIN, ERRORE_IPFS
from costruttore_payload import CostruttorePayload
from ipfs_client import IpfsClient, ErroreCaricamentoIPFS, ErroreRecuperoCID
from istanze_globali import gestore_db
from istanze_globali import scrittore_blockchain
from merkle_tree import MerkleTree
from modelli_dati import PacchettoBatchMisurazioni

# Logger del modulo
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

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


def gestisci_batch_completo(id_batch: int) -> bool:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae i dati del batch dal DB.
    2. Costruisce il payload (modelli Pydantic).
    3. Serializza il payload in JSON.
    4. Costruisce Merkle Tree e Merkle Path.
    5. Salva Merkle Path su IPFS.
    6. Aggiorna DB con metadata del batch.
    7. (Prossimamente) Salva su blockchain.
    """
    dati_query = gestore_db.ottieni_dati_batch_misurazioni_sensori(id_batch)
    if not dati_query:
        logger.error(f"Nessun dato trovato per il batch {id_batch}")
        return False

    # === Costruzione del payload ===
    payload = CostruttorePayload()
    payload.estrai_dati_da_query(dati_query)
    payload_da_inviare: PacchettoBatchMisurazioni = payload.costruisci_payload()
    payload_json = payload_da_inviare.to_json()
    # === Costruzione Merkle Tree e Path ===
    merkle_root, merkle_path = costruisci_merkle_tree(payload)
    # === Upload su IPFS ===
    try:
        cid = carica_merkle_path_ipfs(merkle_path)
        #IPFS OK → aggiorna subito i metadata nel DB
        gestore_db.aggiorna_metadata_batch(id_batch, merkle_root, cid, payload_json)
        # Upload su blockchain
        try:
            logger.debug(f"Merkle Root calcolata: {merkle_root}")
            logger.debug(f"CID Merkle Path: {cid}")
            transaction_hash : str = scrittore_blockchain.scrivi_valore(id_batch, merkle_root, cid)
            gestore_db.aggiorna_transazione_hash_batch(id_batch, transaction_hash)
        except Exception as e:
            logger.exception(f"Errore blockchain per batch {id_batch}")
            gestore_db.aggiorna_batch_errore_elaborazione(
                id_batch,
                messaggio_errore=str(e),
                tipo_errore=ERRORE_BLOCKCHAIN
            )
            return False
    except (ErroreCaricamentoIPFS, ErroreRecuperoCID) as e:
        logger.exception(f"Errore IPFS per batch {id_batch}")
        gestore_db.aggiorna_batch_errore_elaborazione(
            id_batch,
            messaggio_errore=str(e),
            tipo_errore=ERRORE_IPFS
        )
        return False
    # Tutto ok nell'elaborazione
    return True
