import logging
from typing import Dict
import requests
from Verificatore.config.costanti_verificatore import API_KEY_VERIFICATORE, \
    ENDPOINT_MAPPA_ID_HASH, ENDPOINT_METADATA_MISURAZIONE_SENSORE
from costanti_verificatore import ENDPOINT_METADATA_BATCH
from modelli_metadati import MetaDatiMisurazioneSensore, MetaDatiBatch

headers = {"X-API-Key": API_KEY_VERIFICATORE}
#disattivo il logger della libreria usata da request
logging.getLogger("urllib3").setLevel(logging.WARNING)


def richiedi_mappa_id_hash_batch(id_batch: int) -> dict[int, str]:
    """
    Richiede al Cloud Provider la mappa ID → hash delle foglie (batch + misurazioni)
    per un determinato batch. Questa mappa viene usata dal nodo verificatore per
    verificare l'integrità tramite i Merkle Path.

    Args:
        id_batch: ID del batch da verificare.

    Returns:
        Dizionario con ID (int) come chiavi e hash foglia (str) come valori.

    Raises:
        ValueError: in caso di errore nella risposta del server.
    """
    url = f"{ENDPOINT_MAPPA_ID_HASH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    # Conversione: FastAPI restituisce chiavi stringa → convertiamole in intero
    mappa_str = response.json()
    return {int(k): v for k, v in mappa_str.items()}

def richiedi_metadata_misurazione_sensore(lista_id: list[int]) -> list[MetaDatiMisurazioneSensore]:
    """
    Richiede al Cloud Provider i metadati, dati non sensibili, delle misurazioni associate
    agli ID specificati. Questo metodo viene utilizzato dal verificatore dopo aver
    rilevato anomalie nella struttura (es. manomissioni) per ottenere informazioni
    contestuali senza accedere ai dati sensibili.

    Args:
        lista_id: Lista di ID delle misurazioni anomale.

    Returns:
        Lista di oggetti `MetaDatiMisurazioneSensore`.

    Raises:
        ValueError: in caso di errore nella risposta del server.
    """
    response = requests.post(ENDPOINT_METADATA_MISURAZIONE_SENSORE, json=lista_id, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    return [MetaDatiMisurazioneSensore(**item) for item in response.json()]


def richiedi_metadata_batch(id_batch: int) -> MetaDatiBatch:
    """
    Richiede al Cloud Provider i metadati non sensibili del batch specificato.
    Utilizzato per ottenere informazioni generali (timestamp, id, ecc.) senza
    accedere ai contenuti completi del batch.

    Args:
        id_batch: ID del batch da interrogare.

    Returns:
        Oggetto `MetaDatiBatch` corrispondente.

    Raises:
        ValueError: in caso di errore nella risposta del server.
    """
    url = f"{ENDPOINT_METADATA_BATCH}/{id_batch}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    response.raise_for_status()
    batch : Dict = response.json()
    return MetaDatiBatch(**batch)

def richiedi_tutti_metadata_batch() -> list[MetaDatiBatch]:
    """
    Richiede al Cloud Provider la lista completa dei metadati dei batch memorizzati.
    Utile per mostrare lo storico dei batch disponibili, senza accedere ai contenuti
    sensibili.

    Returns:
        Lista di oggetti `MetaDatiBatch`.

    Raises:
        ValueError: in caso di errore nella risposta del server.
    """
    url = ENDPOINT_METADATA_BATCH  # Senza /{id_batch} come parametro query
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise ValueError(f"Errore nella richiesta: {response.status_code} - {response.text}")

    lista_batch = response.json()
    return [MetaDatiBatch(**batch) for batch in lista_batch]