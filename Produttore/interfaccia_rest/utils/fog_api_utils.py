import logging

import requests
from costruttore_payload import CostruttorePayload

from Classi_comuni.entita.modelli_dati import DatiPayload
from costanti_produttore import ERRORE_IPFS, ERRORE_BLOCKCHAIN, API_KEY_PRODUTTORE
from database.gestore_db import GestoreDatabase
from gestione_batch import costruisci_merkle_tree, carica_merkle_path_ipfs
from ipfs_client import ErroreCaricamentoIPFS, ErroreRecuperoCID

logger = logging.getLogger(__name__)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

def gestisci_batch_completo(id_batch: int, gestore_db: GestoreDatabase) -> bool:
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
    dati_query = gestore_db.estrai_dati_batch_misurazioni(id_batch)
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
        cid = carica_merkle_path_ipfs(merkle_path)
        #IPFS OK → aggiorna subito i metadata nel DB
        gestore_db.aggiorna_metadata_batch(id_batch, merkle_root, cid, payload_json)
        # (in futuro) Upload su blockchain
        try:
            # da implementare
            # _carica_dati_su_blockchain(...)
            pass
        except Exception as e:
            logger.error(f"Errore blockchain per batch {id_batch}: {e}")
            gestore_db.aggiorna_batch_errore_elaborazione(
                id_batch,
                messaggio_errore=str(e),
                tipo_errore=ERRORE_BLOCKCHAIN
            )
            return False
    except (ErroreCaricamentoIPFS, ErroreRecuperoCID) as e:
        logger.error(f"Errore IPFS per batch {id_batch}: {e}")
        gestore_db.aggiorna_batch_errore_elaborazione(
            id_batch,
            messaggio_errore=str(e),
            tipo_errore=ERRORE_IPFS
        )
        return False
    # Tutto ok nell'elaborazione
    return True


def invia_payload(payload_dict: dict, endpoint_cloud: str, gestore_db: GestoreDatabase) -> bool:
    """
    Invia un payload al cloud e gestisce la conferma di ricezione.
    Esegue la POST HTTP e, se la risposta è valida, richiama la funzione
    che elabora e registra la conferma nel database.
    """
    try:
        headers = {
            "X-API-Key": API_KEY_PRODUTTORE
        }
        response = requests.post(endpoint_cloud, json=payload_dict, headers=headers, timeout=10)
        response.raise_for_status()

        risposta_json = response.json()
        logger.debug(f"[HTTP] Risposta dal cloud: {risposta_json}")

        # Elabora la risposta ricevuta, aggiorna il DB e ritorna True/False
        return elabora_conferma_ricezione_cloud(risposta_json, gestore_db)

    except requests.exceptions.Timeout:
        logger.error("Timeout durante l'invio del payload al cloud.")
    except requests.exceptions.ConnectionError:
        logger.error("Connessione al cloud fallita.")
    except requests.RequestException as e:
        logger.error(f"Invio del payload fallito: {e}")
    except ValueError:
        logger.error("Risposta del cloud non è in formato JSON valido.")

    return False

def elabora_conferma_ricezione_cloud(risposta: dict, gestore_db: GestoreDatabase) -> bool:
    """
    Elabora la risposta ricevuta dal cloud e aggiorna la conferma nel database locale.
    Restituisce True se la conferma è valida e gestita correttamente.
    """
    if not risposta or not risposta.get("conferma_ricezione"):
        logger.warning(f"[CLOUD] Nessuna conferma ricevuta o struttura non valida: {risposta}")
        return False

    if "id_sensori" in risposta:
        for id_sensore in risposta["id_sensori"]:
            gestore_db.aggiorna_conferma_ricezione_sensore(id_sensore)
        return True

    elif "id_batch" in risposta:
        gestore_db.aggiorna_conferma_ricezione_batch(risposta["id_batch"])
        return True

    logger.warning(f"[CLOUD] Risposta ricevuta ma mancano ID riconoscibili: {risposta}")
    return False

