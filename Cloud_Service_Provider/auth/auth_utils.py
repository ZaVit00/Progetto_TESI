import os
import json
from fastapi import Request, HTTPException, Depends
from dotenv import load_dotenv
from Cloud_Service_Provider.entita.utente_api import UtenteAPI
from Cloud_Service_Provider.config.costanti_cloud import RUOLO_PRODUTTORE, RUOLO_VERIFICATORE

# Carica da .env.keys (assumendo sia accanto a .env)
env_keys_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env.keys")
load_dotenv(dotenv_path=os.path.abspath(env_keys_path))

def _carica_api_keys() -> dict:
    api_keys_json = os.getenv("API_KEYS")
    if not api_keys_json:
        raise ValueError("Variabile API_KEYS mancante nel file .env.keys")
    try:
        api_keys = json.loads(api_keys_json)
        if not isinstance(api_keys, dict):
            raise ValueError("API_KEYS deve essere un dizionario valido")
        return api_keys
    except json.JSONDecodeError as e:
        raise ValueError(f"Errore nel parsing di API_KEYS: {e}")

_API_KEYS = _carica_api_keys()

def get_utente(request: Request) -> UtenteAPI:
    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in _API_KEYS:
        raise HTTPException(status_code=403, detail="API Key non valida o mancante.")
    user = _API_KEYS[api_key]
    return UtenteAPI(nome=user["nome"], ruolo=user["ruolo"])

def richiede_permesso_scrittura(utente: UtenteAPI = Depends(get_utente)) -> UtenteAPI:
    if not utente.puo_scrivere():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per scrivere.")
    return utente

def richiede_permesso_verifica(utente: UtenteAPI = Depends(get_utente)) -> UtenteAPI:
    if not utente.puo_verificare():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per verificare.")
    return utente
