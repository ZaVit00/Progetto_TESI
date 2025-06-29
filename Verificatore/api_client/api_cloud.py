from typing import Dict

import requests

from Verificatore.config.costanti_verificatore import API_KEY_VERIFICATORE, \
    ENDPOINT_MAPPA_ID_HASH, ENDPOINT_METADATA_MISURAZIONE_SENSORE
from costanti_verificatore import ENDPOINT_METADATA_BATCH
from modelli_metadati import MetaDatiMisurazioneSensore, MetaDatiBatch

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

def richiedi_metadata_misurazione_sensore(lista_id: list[int]) -> list[MetaDatiMisurazioneSensore]:
    response = requests.post(ENDPOINT_METADATA_MISURAZIONE_SENSORE, json=lista_id, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    return [MetaDatiMisurazioneSensore(**item) for item in response.json()]


def richiedi_metadata_batch(id_batch: int) -> MetaDatiBatch:
    url = f"{ENDPOINT_METADATA_BATCH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    response.raise_for_status()
    batch : Dict = response.json()
    return MetaDatiBatch(**batch)
