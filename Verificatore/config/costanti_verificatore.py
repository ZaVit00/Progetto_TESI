import os
from dotenv import load_dotenv


DIR_CORRENTE = os.path.dirname(__file__)
PERCORSO_ENV_KEY = os.path.join(DIR_CORRENTE, '.env.key')

# === Carica env ===
load_dotenv(PERCORSO_ENV_KEY)

# ===
ENDPOINT_CLOUD_PROVIDER = "http://localhost:8080/batch/mappa-id-hash"
ENDPOINT_IPFS_FILEBASE = "https://ipfs.filebase.io/ipfs"
API_KEY_VERIFICATORE=os.getenv("API_KEY_VERIFICATORE")