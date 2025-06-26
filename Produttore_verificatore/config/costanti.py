import os

from dotenv import load_dotenv

load_dotenv()

API_KEY_VERIFICATORE_ESTESO = os.getenv("API_KEY_VERIFICATORE_ESTESO")

ENDPOINT_DATI_BATCH = "http://localhost:8080/dati/batch"
ENDPOINT_DATI_MISURAZIONE_SENSORE = "http://localhost:8080/dati/misurazione-sensore"