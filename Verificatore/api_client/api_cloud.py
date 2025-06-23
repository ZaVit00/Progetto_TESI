import requests
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiBatch, DatiMisurazione
from Verificatore.config.costanti_verificatore import API_KEY_VERIFICATORE, \
    ENDPOINT_MAPPA_ID_HASH
from costanti_verificatore import ENDPOINT_METADATA_MISURAZIONE, ENDPOINT_METADATA_BATCH
from sensore_joystick import ENDPOINT_MISURAZIONE

headers = {"X-API-Key": API_KEY_VERIFICATORE}

def richiedi_mappa_id_hash_batch(id_batch: int) -> dict[int, str]:
    """
    Richiede al Cloud Provider la mappa ID → hash delle foglie di un batch.
    """
    url = f"{ENDPOINT_MAPPA_ID_HASH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    # Conversione: FastAPI restituisce chiavi stringa → convertiamole in intero
    mappa_str = response.json()
    return {int(k): v for k, v in mappa_str.items()}

def richiedi_metadata_misurazione(id_misurazione: int) -> dict:
    url = f"{ENDPOINT_METADATA_MISURAZIONE}/{id_misurazione}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    response.raise_for_status()
    return response.json()


def richiedi_metadata_batch(id_batch: int) -> dict:
    url = f"{ENDPOINT_METADATA_BATCH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    response.raise_for_status()
    return response.json()