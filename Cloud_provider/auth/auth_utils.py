from fastapi import Request, HTTPException, Depends
from Cloud_provider.config.istanze_globali import API_KEYS
from Cloud_provider.entita.utente_api import UtenteAPI


def ottieni_utente(request: Request) -> UtenteAPI:
    # DA CHIAVE --> UTENTE API DEL SISTEMA
    api_key = request.headers.get("X-API-Key")
    #cerca di trovare l'utente associato a quella chiave
    utente = API_KEYS.get(api_key)
    if not utente:
        raise HTTPException(status_code=403, detail="API Key non valida o mancante.")
    return utente

def richiede_permesso_scrittura(utente: UtenteAPI = Depends(ottieni_utente)) -> UtenteAPI:
    if not utente.permesso_scrittura():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per scrivere.")
    return utente

def richiede_permesso_verifica(utente: UtenteAPI = Depends(ottieni_utente)) -> UtenteAPI:
    if not utente.permesso_verifica():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per verificare.")
    return utente

def richiede_permesso_verifica_estesa(utente: UtenteAPI = Depends(ottieni_utente)) -> UtenteAPI:
    #NB solo il produttore può effettuare la verifica estesa
    #Per verifica estesa intendiamo una differenza 1 a 1 tra dato originale conservato nel
    #produttore e dato ottenuto dal cloud. Vista la sensibilità dei dati solo un ruolo privilegiato
    #può accedere ai dati in chiaro.
    if not utente.permesso_verifica_estesa():
        raise HTTPException(status_code=403, detail="Permessi insufficienti per effettuare la verifica estesa.")
    return utente