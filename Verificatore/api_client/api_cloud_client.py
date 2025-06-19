import requests
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiBatch, DatiMisurazione
from Verificatore.config.costanti_verificatore import ENDPOINT_CLOUD_PROVIDER, API_KEY_VERIFICATORE

def richiedi_payload_batch(id_batch: int) -> DatiPayload:
    """
    Scarica dal Cloud Provider il payload (batch + misurazioni) corrispondente a un certo id_batch.
    Il cloud restituisce un dizionario compatibile con il modello DatiPayload.
    """
    # Costruisce l'URL per l'endpoint GET /batch
    url = ENDPOINT_CLOUD_PROVIDER
    # Inserisce l'API Key del verificatore nell header per l'autenticazione
    headers = {"X-API-Key": API_KEY_VERIFICATORE}
    # Imposta i parametri della richiesta GET (id del batch da scaricare)
    params = {"id": id_batch}
    # Esegue la richiesta HTTP GET verso il cloud provider
    response = requests.get(url, headers=headers, params=params)

    # Se la risposta non è 200 OK, solleva un errore con messaggio dettagliato
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    # Converte il dizionario JSON ricevuto in un oggetto DatiPayload (classe Pydantic)
    return DatiPayload(**response.json())
