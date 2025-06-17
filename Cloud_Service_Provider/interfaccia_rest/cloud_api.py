import logging
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from Classi_comuni.entita.modelli_dati import DatiSensore, DatiPayload
from Cloud_Service_Provider.Database.gestore_db import GestoreDatabase
from Cloud_Service_Provider.interfaccia_rest.utils.cloud_api_utils import elabora_payload
import os
from dotenv import load_dotenv


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
    logger.info("StartUp lifespan")
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    gestore_db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)

@app.post("/sensori")
def registra_sensore(dati: DatiSensore):
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
def ricevi_batch(payload: DatiPayload):
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


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()