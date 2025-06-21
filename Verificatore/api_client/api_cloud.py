import requests
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiBatch, DatiMisurazione
from Verificatore.config.costanti_verificatore import ENDPOINT_CLOUD_PROVIDER, API_KEY_VERIFICATORE

def richiedi_mappa_id_hash_batch(id_batch: int) -> dict[int, str]:
    """
    Richiede al Cloud Provider la mappa ID → hash delle foglie di un batch.
    """
    headers = {"X-API-Key": API_KEY_VERIFICATORE}
    params = {"id": id_batch}

    response = requests.get(ENDPOINT_CLOUD_PROVIDER, headers=headers, params=params)

    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    # Conversione: FastAPI restituisce chiavi stringa → convertiamole in intero
    mappa_str = response.json()
    return {int(k): v for k, v in mappa_str.items()}

