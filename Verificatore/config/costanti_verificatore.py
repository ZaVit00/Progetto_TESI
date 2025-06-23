import os
from dotenv import load_dotenv


DIR_CORRENTE = os.path.dirname(__file__)
PERCORSO_ENV_KEY = os.path.join(DIR_CORRENTE, '.env.key')

# === Carica env ===
load_dotenv(PERCORSO_ENV_KEY)

# ===
ENDPOINT_MAPPA_ID_HASH = "http://localhost:8080/batch/mappa-id-hash"
ENDPOINT_IPFS_FILEBASE = "https://ipfs.filebase.io/ipfs"
API_KEY_VERIFICATORE=os.getenv("API_KEY_VERIFICATORE")

ENDPOINT_METADATA_BATCH ="http://localhost:8080/metadata/batch"
ENDPOINT_METADATA_MISURAZIONE ="http://localhost:8080/metadata/misurazione"