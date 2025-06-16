import logging
import requests
from costanti_produttore import ERRORE_IPFS, ERRORE_BLOCKCHAIN
from database.gestore_db import GestoreDatabase
from Classi_comuni.entita.modelli_dati import DatiPayload
from gestione_batch import costruisci_merkle_tree, carica_merkle_path_su_ipfs_mamt
from ipfs_client import ErroreCaricamentoIPFS, ErroreRecuperoCID
from costruttore_payload import CostruttorePayload
from misurazioni_in_ingresso import MisurazioneInIngresso

# Logger del modulo
logger = logging.getLogger(__name__)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

def gestisci_batch_completo(id_batch: int, db: GestoreDatabase) -> bool:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae i dati del batch dal DB.
    2. Costruisce il payload (modelli Pydantic).
    3. Serializza il payload in JSON.
    4. Costruisce Merkle Tree e Merkle Path.
    5. Salva Merkle Path su IPFS.
    6. (Prossimamente) Salva su blockchain.
    7. Aggiorna DB con metadata del batch.
    """
    dati_query = db.estrai_dati_batch_misurazioni(id_batch)
    if not dati_query:
        logger.error(f"Nessun dato trovato per il batch {id_batch}")
        return False

    # === Costruzione del payload ===
    payload = CostruttorePayload()
    payload.estrai_dati_da_query(dati_query)
    payload_da_inviare: DatiPayload = payload.costruisci_payload()
    payload_json = payload_da_inviare.to_json()

    # === Costruzione Merkle Tree e Path ===
    merkle_root, merkle_path = costruisci_merkle_tree(payload)

    # === Upload su IPFS ===
    try:
        cid = carica_merkle_path_su_ipfs_mamt(merkle_path)
        # ✅ IPFS OK → aggiorna subito i metadata nel DB
        db.aggiorna_metadata_batch(id_batch, merkle_root, cid, payload_json)
        # (in futuro) Upload su blockchain
        try:
            # _carica_dati_su_blockchain(...)  # da implementare
            pass
        except Exception as e:
            logger.error(f"Errore blockchain per batch {id_batch}: {e}")
            db.aggiorna_batch_errore_elaborazione(
                id_batch,
                messaggio_errore=str(e),
                tipo_errore=ERRORE_BLOCKCHAIN
            )
            return False


    except (ErroreCaricamentoIPFS, ErroreRecuperoCID) as e:
        logger.error(f"Errore IPFS per batch {id_batch}: {e}")
        db.aggiorna_batch_errore_elaborazione(
            id_batch,
            messaggio_errore=str(e),
            tipo_errore=ERRORE_IPFS
        )
        return False

    # Tutto ok nell'elaborazione
    return True



def invia_payload(payload_dict: dict, endpoint_cloud: str) -> bool:
    """
    Invia il payload (dizionario) al servizio cloud tramite HTTP POST.
    Ritorna True se la richiesta ha esito positivo (status code 2xx), altrimenti False.
    L'errore HTTP non viene trattato come un errore di elaborazione grave.
    Viene semplicemente ritentato l'invio al cloud del payload successivamente
    """
    try:
        response = requests.post(endpoint_cloud, json=payload_dict, timeout=10)
        response.raise_for_status()
        logger.info("Invio del payload al cloud riuscito.")
        return True
    except requests.exceptions.Timeout:
        logger.error("Timeout durante l'invio del payload al cloud.")
    except requests.exceptions.ConnectionError:
        logger.error("Connessione al cloud fallita.")
    except requests.RequestException as e:
        logger.error(f"Invio del payload fallito: {e}")
    return False
