from typing import Dict

import requests
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiBatch, DatiMisurazione, MetaDatiMisurazione
from Verificatore.config.costanti_verificatore import API_KEY_VERIFICATORE, \
    ENDPOINT_MAPPA_ID_HASH
from costanti_verificatore import ENDPOINT_METADATA_MISURAZIONI, ENDPOINT_METADATA_BATCH
from modelli_dati import MetaDatiBatch

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

def richiedi_metadata_misurazioni(lista_id: list[int]) -> list[MetaDatiMisurazione]:
    url = ENDPOINT_METADATA_MISURAZIONI
    response = requests.post(url, json=lista_id, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    return [MetaDatiMisurazione(**item) for item in response.json()]


def richiedi_metadata_batch(id_batch: int) -> MetaDatiBatch:
    url = f"{ENDPOINT_METADATA_BATCH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    response.raise_for_status()
    batch : Dict = response.json()
    return MetaDatiBatch(**batch)
