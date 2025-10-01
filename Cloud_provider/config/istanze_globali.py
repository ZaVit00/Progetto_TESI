import logging
import os
import json
from types import MappingProxyType
from dotenv import load_dotenv

from Cloud_provider.database.gestore_db import GestoreDatabase
from utente_api import UtenteAPI

# === Percorsi ===
DIR_CORRENTE = os.path.dirname(__file__)
PERCORSO_ENV = os.path.join(DIR_CORRENTE, '.env')
PERCORSO_ENV_KEY = os.path.join(DIR_CORRENTE, '.env.key')

# === Carica env ===
load_dotenv(PERCORSO_ENV)
load_dotenv(PERCORSO_ENV_KEY)

# === Configurazione DB ===
config_db = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "dati_cloud"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "admin")
}

# Istanza globale del gestore DB
gestore_db = GestoreDatabase(config_db)

# === API Keys immutabili ===
_api_keys_raw = os.getenv("API_KEYS")

if not _api_keys_raw:
    raise ValueError("Variabile API_KEYS mancante nel file .env.key")

try:
    api_keys_parsed = json.loads(_api_keys_raw)
except json.JSONDecodeError as e:
    raise ValueError(f"Errore nel parsing API_KEYS: {e}")

# Costruisci oggetti UtenteAPI dinamicamente
_api_keys_dict = {
    chiave: UtenteAPI(nome=info["nome"], ruolo=info["ruolo"])
    for chiave, info in api_keys_parsed.items()
}

# Rendi il dizionario immutabile
API_KEYS = MappingProxyType(_api_keys_dict)