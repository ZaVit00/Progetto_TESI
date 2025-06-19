import requests
import gzip
from io import BytesIO

def ottieni_file_da_ipfs(cid: str) -> str:
    """
    Scarica un file da IPFS tramite Filebase.
    Se il file è compresso (application/gzip), lo decomprime.
    Restituisce una stringa JSON.
    """
    url = f"https://ipfs.filebase.io/ipfs/{cid}"

    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Errore durante il download da IPFS: {response.status_code} - {response.text}")

    content_type = response.headers.get("Content-Type", "").lower()

    if "application/gzip" in content_type:
        # Decompressione GZIP
        compressed_stream = BytesIO(response.content)
        with gzip.GzipFile(fileobj=compressed_stream, mode='rb') as f:
            return f.read().decode("utf-8")

    elif "application/json" in content_type:
        # File JSON non compresso
        return response.text

    else:
        raise ValueError(f"Tipo di contenuto sconosciuto o non gestito: {content_type}")
