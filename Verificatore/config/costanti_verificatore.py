import os

from dotenv import load_dotenv

DIR_CORRENTE = os.path.dirname(__file__)
PERCORSO_ENV_KEY = os.path.join(DIR_CORRENTE, '.env.key')

# === Carica env ===
load_dotenv(PERCORSO_ENV_KEY)

API_KEY_VERIFICATORE=os.getenv("API_KEY_VERIFICATORE")
# ===
ENDPOINT_MAPPA_ID_HASH = "http://localhost:8080/batch/mappa-id-hash"
ENDPOINT_IPFS_FILEBASE = "https://ipfs.filebase.io/ipfs"


ENDPOINT_METADATA_BATCH ="http://localhost:8080/metadata/batch"
ENDPOINT_METADATA_MISURAZIONE_SENSORE ="http://localhost:8080/metadata/misurazione-sensore"
URL_FILEBASE_IPFS = "https://ipfs.filebase.io/ipfs/"

# Costanti per indicare i nomi dei file
DIFFERENZE_RISCONTRATE = "differenze_riscontrate.json"
METADATI_ANOMALIE = "metadata_anomalie.json"
ESITO_ANALISI_INTEGRITA = "esito_analisi_integrita" # l'estensione viene aggiunta dopo nel codice