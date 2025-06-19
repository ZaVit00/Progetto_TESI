import json
import os
from types import MappingProxyType  # per rendere il dict immutabile

from dotenv import load_dotenv

from utente_api import UtenteAPI

# === Percorsi ===
DIR_CORRENTE = os.path.dirname(__file__)
PERCORSO_ENV = os.path.join(DIR_CORRENTE, '.env')
PERCORSO_ENV_KEY = os.path.join(DIR_CORRENTE, '.env.key')

# === Carica env ===
load_dotenv(PERCORSO_ENV)
load_dotenv(PERCORSO_ENV_KEY)

# === Database ===
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME", "dati_cloud")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

# === API Keys immutabili ===
api_keys_raw = os.getenv("API_KEYS")
if not api_keys_raw:
    raise ValueError("Variabile API_KEYS mancante nel file .env.key")

try:
    api_keys_parsed = json.loads(api_keys_raw)
except json.JSONDecodeError as e:
    raise ValueError(f"Errore nel parsing API_KEYS: {e}")

# Costruisci oggetti UtenteAPI dinamicamente
_api_keys_dict = {
    chiave: UtenteAPI(nome=info["nome"], ruolo=info["ruolo"])
    for chiave, info in api_keys_parsed.items()
}

# Rendi il dizionario immutabile
API_KEYS = MappingProxyType(_api_keys_dict)




