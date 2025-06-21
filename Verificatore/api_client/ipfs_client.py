import requests
import gzip
from io import BytesIO

def ottieni_file_da_ipfs(cid: str) -> str:
    """
    Scarica un file da IPFS (tramite Filebase) e restituisce una stringa JSON.
    Supporta file compressi (gzip) o normali.
    """
    url = f"https://ipfs.filebase.io/ipfs/{cid}"
    response = requests.get(url)

    if response.status_code != 200:
        raise ValueError(f"Errore nel download: {response.status_code}")

    content_type = response.headers.get("Content-Type", "").lower()
    raw_bytes = response.content  # 🔥 Evita .text
    try:
        if "gzip" in content_type or cid.endswith(".gz"):
            with gzip.GzipFile(fileobj=BytesIO(raw_bytes)) as f:
                return f.read().decode("utf-8")  # 🔥 qui abbiamo il JSON completo
        else:
            return raw_bytes.decode("utf-8")  # JSON non compresso
    except Exception as e:
        raise ValueError(f"Errore nella lettura o decompressione del file: {e}")
