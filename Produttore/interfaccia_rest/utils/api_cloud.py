import logging

import requests

from costanti_produttore import API_KEY_PRODUTTORE
from database.gestore_db import GestoreDatabase

logger = logging.getLogger(__name__)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)


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

