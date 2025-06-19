from fastapi import Request, HTTPException, Depends
from Cloud_Service_Provider.entita.utente_api import UtenteAPI
from Cloud_Service_Provider.config.costanti_cloud import API_KEYS

def get_utente(request: Request) -> UtenteAPI:
    # DA CHIAVE --> UTENTE API DEL SISTEMA
    api_key = request.headers.get("X-API-Key")
    #cerca di trovare l'utente associato a quella chiave
    utente = API_KEYS.get(api_key)
    if not utente:
        raise HTTPException(status_code=403, detail="API Key non valida o mancante.")
    return utente

def richiede_permesso_scrittura(utente: UtenteAPI = Depends(get_utente)) -> UtenteAPI:
    if not utente.puo_scrivere():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per scrivere.")
    return utente

def richiede_permesso_verifica(utente: UtenteAPI = Depends(get_utente)) -> UtenteAPI:
    if not utente.puo_verificare():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per verificare.")
    return utente
