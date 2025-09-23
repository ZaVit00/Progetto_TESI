import logging
from typing import List
import requests
from Produttore_verificatore.config.costanti import ENDPOINT_DATI_BATCH, API_KEY_VERIFICATORE_ESTESO
from costanti import ENDPOINT_DATI_MISURAZIONE_SENSORE
from modelli_dati import DatiBatch, DatiMisurazioneSensorePayload

logger = logging.getLogger(__name__)

headers = {"X-API-Key": API_KEY_VERIFICATORE_ESTESO}

def richiedi_dati_cloud_batch(id_batch: int) -> DatiBatch:
    """
    Richiede i dati di uno specifico batch con ID specificato al cloud provider,
    utilizzando una chiamata HTTP GET autenticata con API key.
    """
    url = f"{ENDPOINT_DATI_BATCH}/{id_batch}"
    try:
        # Effettua la richiesta GET al cloud
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Solleva eccezione se la risposta ha codice errore
        dati = response.json()       # Converte la risposta in dizionario
        return DatiBatch(**dati)     # Costruisce oggetto DatiBatch
    except requests.exceptions.RequestException as e:
        # Errore di rete o risposta HTTP non valida
        logger.error(f"[ERRORE HTTP - BATCH] Richiesta fallita: {e}")
        raise
    except Exception as e:
        # Errore nella conversione della risposta in oggetto DatiBatch
        logger.error(f"[ERRORE PARSING - BATCH] Risposta non valida per DatiBatch: {e}")
        raise RuntimeError


def richiedi_dati_cloud_completi_misurazioni(lista_id: List[int]) -> List[DatiMisurazioneSensorePayload]:
    """
    Richiede al cloud provider le misurazioni alterate (con sensore associato)
    corrispondenti alla lista di ID fornita, tramite POST.
    """
    endpoint = ENDPOINT_DATI_MISURAZIONE_SENSORE
    logger.info(f"Invio richiesta POST al cloud per {len(lista_id)} ID misurazione")
    logger.debug(f"Endpoint: {endpoint}, Payload: {lista_id}")

    try:
        # Invia la lista di ID misurazione come payload JSON
        response = requests.post(endpoint, json=lista_id, headers=headers)
        response.raise_for_status()  # Solleva eccezione se lo status code è di errore
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore nella richiesta al cloud: {e}")
        raise

    try:
        # Converte la risposta in lista di dizionari
        lista_dati_dict = response.json()
        logger.debug(f"Risposta ricevuta: {lista_dati_dict}")
        # Converte ogni elemento della lista in un oggetto DatiMisurazioneSensorePayload
        return [DatiMisurazioneSensorePayload(**elem) for elem in lista_dati_dict]
    except (ValueError, TypeError) as e:
        logger.error(f"Errore nel parsing della risposta JSON: {e}")
        raise
