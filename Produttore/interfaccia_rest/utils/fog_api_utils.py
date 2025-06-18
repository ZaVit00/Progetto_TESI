import logging
import requests
from costanti_produttore import ERRORE_IPFS, ERRORE_BLOCKCHAIN, API_KEY_PRODUTTORE
from database.gestore_db import GestoreDatabase
from Classi_comuni.entita.modelli_dati import DatiPayload
from gestione_batch import costruisci_merkle_tree, carica_merkle_path_ipfs
from ipfs_client import ErroreCaricamentoIPFS, ErroreRecuperoCID
from costruttore_payload import CostruttorePayload
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


def invia_payload(payload_dict: dict, endpoint_cloud: str, gestore_db : GestoreDatabase) -> bool:
    """
    Invia il payload (dizionario) al servizio cloud tramite HTTP POST.

    La funzione si aspetta una risposta JSON strutturata dal cloud, contenente almeno:
    - "success": True/False
    - "id_sensore" oppure "id_batch" a seconda del tipo di operazione
    Ritorna True solo se la risposta HTTP ha status 2xx e se il campo "success" è True.
    Eventuali errori di rete o risposte errate vengono loggati sul logger
    """
    try:
        # Header con chiave API
        headers = {
            "X-API-Key": API_KEY_PRODUTTORE
        }

        # Invia il payload con header e timeout
        response = requests.post(endpoint_cloud, json=payload_dict, headers=headers, timeout=10)
        response.raise_for_status()  # genera eccezione se non 2xx
        # Tenta di effettuare il parsing della risposta come JSON (in realtà il payload è un dizionario)
        payload_dict = response.json()
        logger.debug(payload_dict)
        # Verifica che il campo "conferma_ricezione" sia presente e valga True
        if payload_dict.get("conferma_ricezione") is True:
            # Messaggio di log personalizzato in base al contenuto della risposta
            if "id_sensore" in payload_dict:
                logger.debug(f"Registrazione id Sensore confermata: {payload_dict['id_sensore']}")
                gestore_db.aggiorna_conferma_ricezione_sensore(payload_dict['id_sensore'])
            elif "id_batch" in payload_dict:
                logger.debug(f"Registrazione id Batch confermato: {payload_dict['id_batch']}")
                gestore_db.aggiorna_conferma_ricezione_batch(payload_dict['id_batch'])
            return True
        else:
            #fallita la registrazione del sensore o del batch
            logger.warning(f"Risposta dal cloud provider ricevuta ma non conferma"
                           f"la ricezione del sensore o del batch: {payload_dict}")

    except requests.exceptions.Timeout:
        logger.error("Timeout durante l'invio del payload al cloud.")
    except requests.exceptions.ConnectionError:
        logger.error("Connessione al cloud fallita.")
    except requests.RequestException as e:
        logger.error(f"Invio del payload fallito: {e}")
    except ValueError:
        logger.error("Risposta del cloud non è in formato JSON valido.")
    # In tutti i casi d’errore ritorna False per ritentare in seguito
    return False

