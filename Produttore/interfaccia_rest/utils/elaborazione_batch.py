import logging
from typing import Tuple
from costanti_comuni import TipoServizio
from costanti_produttore import BUCKET_MERKLE_PATH, ERRORE_BLOCKCHAIN, ERRORE_IPFS
from costruttore_payload import CostruttorePayload
from ipfs_client import IpfsClient, ErroreCaricamentoIPFS, ErroreRecuperoCID
from istanze_globali_produttore import gestore_db
from istanze_globali_produttore import scrittore_blockchain
from merkle_tree import MerkleTree
from modelli_dati import BatchPayload
from registro_log import setup_logger

logger = setup_logger(TipoServizio.PRODUTTORE, module = __name__, level=logging.DEBUG)

def elabora_batch_completo(id_batch: int) -> bool:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae i dati del batch dal DB (tupla batch inner join tuple misurazione inner join sensore)
    2. Costruisce il payload (modelli Pydantic).
    3. Serializza il payload in JSON.
    4. Costruisce Merkle Tree e Merkle Path.
    5. Salva Merkle Path su IPFS.
    6. Aggiorna DB con metadata (merkle root, cid ipfs).
    7. Salva su blockchain la tripla merkle root, cid ipfs, id batch.
    8. Salva hash della transazione blockchain nel DB per determinare
    la transazione corrispondente al salvataggio (id_batch, cid, merkle_root) un dato batch
    """
    dati_query = gestore_db.ottieni_dati_batch_misurazioni_sensori(id_batch)
    if not dati_query:
        logger.error(f"Nessun dato trovato per il batch {id_batch}")
        return False

    # === Costruzione del payload ===
    payload = CostruttorePayload()
    payload.estrai_dati_da_query(dati_query)
    #payload da inviare al cloud
    payload_da_inviare: BatchPayload = payload.costruisci_payload()
    payload_json : str = payload_da_inviare.to_json()

    # === Costruzione Merkle Tree e Path ===
    # Estrazione della mappa id → hash (ordinata all'interno del metodo stesso)
    merkle_root, merkle_path = costruisci_merkle_tree(payload.ottieni_mappa_id_foglie())
    try:
        # === Upload su IPFS ===
        # Cid ottenuto in seguito all'upload del file
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
    logger.debug(f"[elabora_batch_completo] Batch {id_batch} elaborato con successo")
    return True


def costruisci_merkle_tree(mappa_id_hash: dict[int, str]) -> Tuple[str, str]:
    """
    Costruisce il Merkle Tree a partire dalla mappa ID → hash (con ID 0 per il batch)
    già ordinata,
    e restituisce:
      - la Merkle Root
      - i Merkle Path in formato JSON (stringa)
    L'hash corrisponde alla foglia su cui si base l'albero di merkle
    """
    # Estrazione ordinata delle chiavi (ID foglie) e degli hash
    lista_id = list(mappa_id_hash.keys())
    lista_hash = list(mappa_id_hash.values())

    # Costruzione del Merkle Tree
    merkle_tree = MerkleTree(lista_hash, lista_id)
    merkle_root : str = merkle_tree.costruisci_albero()

    logger.debug(f"Merkle Root calcolata: {merkle_root}")

    # Esportazione dei Merkle Path in formato JSON
    merkle_path_json : str = merkle_tree.ottieni_merkle_paths_json()

    return merkle_root, merkle_path_json


def carica_merkle_path_ipfs(merkle_path: str) -> str:
    client = IpfsClient()
    #carica l'oggetto stringa su IPFS e restituisce il nome del file generato internamente
    # dalla classe IPFS in modo che sia univoco in IPFS
    nome_file_caricato: str = client.carica_stringa_json(BUCKET_MERKLE_PATH, merkle_path, comprimi_dimensione = False)
    #recupera il CID a partire dai metadata del file caricato nel bucket dell'utente
    cid = client.recupera_cid_file_bucket(BUCKET_MERKLE_PATH, nome_file_caricato)
    return cid