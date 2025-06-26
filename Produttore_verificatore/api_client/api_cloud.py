from typing import List
import requests

from costanti import ENDPOINT_DATI_MISURAZIONE_SENSORE
from modelli_dati import DatiBatch, DatiMisurazioneSensore
from Produttore_verificatore.config.costanti import ENDPOINT_DATI_BATCH, API_KEY_VERIFICATORE_ESTESO
import logging

logger = logging.getLogger(__name__)

def richiedi_dato_cloud_batch(id_batch: int) -> DatiBatch:
    """
    Richiede al cloud provider i dati completi del batch corrispondente all'ID specificato.
    Utilizza una richiesta HTTP GET con autenticazione tramite API key.
    """
    url = f"{ENDPOINT_DATI_BATCH}/{id_batch}"
    headers = {"X-API-Key": API_KEY_VERIFICATORE_ESTESO}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        dati = response.json()
        return DatiBatch(**dati)
    except requests.exceptions.RequestException as e:
        logger.error(f"[ERRORE HTTP - BATCH] Richiesta fallita: {e}")
        raise
    except Exception as e:
        logger.error(f"[ERRORE PARSING - BATCH] Risposta non valida per DatiBatch: {e}")
        raise


def richiedi_dati_cloud_completi_misurazioni(lista_id: List[int]) -> List[DatiMisurazioneSensore]:
    """
    Richiede al cloud i dati completi (misurazione + sensore) per una lista di ID misurazione.
    Restituisce una lista di oggetti DatiMisurazioneSensore.
    """
    endpoint = ENDPOINT_DATI_MISURAZIONE_SENSORE
    headers = {"x-api-key": API_KEY_VERIFICATORE_ESTESO}

    logger.info(f"Invio richiesta POST al cloud per {len(lista_id)} ID misurazione")
    logger.debug(f"Endpoint: {endpoint}, Payload: {lista_id}")

    try:
        response = requests.post(endpoint, json=lista_id, headers=headers)
        response.raise_for_status()  # Solleva eccezione se status != 200
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nella richiesta al cloud: {e}")
        raise

    try:
        lista_dict = response.json()
        logger.debug(f"Risposta ricevuta: {lista_dict}")
        return [DatiMisurazioneSensore(**elem) for elem in lista_dict]
    except (ValueError, TypeError) as e:
        logger.error(f"Errore nel parsing della risposta JSON: {e}")
        raise
