import logging
import os
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from Classi_comuni.entita.modelli_dati import DatiSensore, DatiPayload
from Cloud_Service_Provider.auth.auth_utils import richiede_permesso_scrittura, richiede_permesso_verifica
from Cloud_Service_Provider.database.gestore_db import GestoreDatabase
from Cloud_Service_Provider.entita.utente_api import UtenteAPI
from Cloud_Service_Provider.interfaccia_rest.utils.cloud_api_utils import elabora_payload
from cloud_api_utils import costruisci_payload_per_batch

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)
#Path assoluto al file .env
env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
load_dotenv(dotenv_path=os.path.abspath(env_path))
config_db = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}
gestore_db = GestoreDatabase(config_db)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StartUp Applicazione")
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    gestore_db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)
@app.post("/sensori")
def registra_sensore(dati: DatiSensore, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    """
    Endpoint per la registrazione di un sensore.
    Riceve un oggetto DatiSensore, lo valida e lo salva nel database.
    Restituisce un messaggio di conferma con l'id del sensore
    per confermare la corretta registrazione del sensore
    """
    successo_operazione = gestore_db.inserisci_sensore(dati)
    if successo_operazione:
        logger.info(f"Sensore registrato: {dati.id_sensore}")
        return JSONResponse(content={
            "conferma_ricezione": True,
            "id_sensore": dati.id_sensore,
            "messaggio": "Sensore registrato correttamente"
        })
    else:
        logger.warning(f"Registrazione sensore fallita: {dati.id_sensore}")
        return JSONResponse(
            content={"conferma_ricezione": False, "messaggio": "Errore nella registrazione del sensore"},
            status_code=500
        )

@app.post("/batch")
def ricevi_batch(payload: DatiPayload, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    """
    Endpoint per ricevere un intero batch con le sue misurazioni.
    Il payload contiene un oggetto DatiBatch e una lista di DatiMisurazione.
    """
    logger.info(f"Ricezione batch {payload.batch.id_batch} con {len(payload.misurazioni)} misurazioni...")
    successo_operazione = elabora_payload(payload, gestore_db)

    if successo_operazione:
        logger.info(f"Batch {payload.batch.id_batch} salvato correttamente.")
        return JSONResponse(content={
            "conferma_ricezione": True,
            "id_batch": payload.batch.id_batch,
            "messaggio": "Batch salvato correttamente"
        })
    else:
        logger.warning(f"Errore durante il salvataggio del batch {payload.batch.id_batch}.")
        return JSONResponse(
            content={"conferma_ricezione": False, "messaggio": "Errore durante il salvataggio del batch"},
            status_code=500
        )

@app.get("/batch", response_model=DatiPayload)
def ottieni_batch(id: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    try:
        print(f"[DEBUG] Ricevuta richiesta batch con id = {id}")
        payload = costruisci_payload_per_batch(id, gestore_db)
        #print(f"[DEBUG] Payload costruito: {payload}")
        return payload
    except Exception as e:
        print(f"[ERRORE GET /batch] {e}")
        raise HTTPException(status_code=500, detail=str(e))


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()