from contextlib import asynccontextmanager
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union
import asyncio

# Import dei modelli di misurazione_in_ingresso specifici
from misurazioni_in_ingresso import MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura
from sensore_base import Sensore
from database.gestore_db import GestoreDatabase
from fog_api_utils import gestisci_batch_completato
from retry_invio_batch import retry_invio_batch_periodico

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Istanza del database (con soglia per batch)
db = GestoreDatabase(soglia_batch=31)

# Endpoint del cloud service
ENDPOINT_CLOUD = "http://localhost:8080/ricevi_batch"

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio del task periodico per il retry dei batch.")
    asyncio.create_task(retry_invio_batch_periodico(db, ENDPOINT_CLOUD))
    yield  # Applicazione avviata
    db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)

@app.post("/sensori")
async def registra_sensore(sensore: Sensore):
    """
    Endpoint per la registrazione manuale di un sensore.
    """
    if not db.inserisci_dati_sensore(sensore.id_sensore, sensore.descrizione):
        logger.error(f"Errore nella registrazione del sensore {sensore.id_sensore}")
        raise HTTPException(status_code=500, detail="Errore nella registrazione del sensore.")

    logger.debug(f"Sensore registrato correttamente: {sensore.id_sensore}")
    return {
        "status": "sensore registrato",
        "id": sensore.id_sensore,
        "descrizione": sensore.descrizione
    }

@app.post("/misurazioni")
async def ricevi_misurazione(misurazione: Union[MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura]):
    """
    Endpoint per ricevere e salvare una misurazione_in_ingresso da un sensore registrato.
    Restituisce anche l'ID del batch chiuso, se la soglia è stata raggiunta.
    """
    id_sensore = misurazione.id_sensore
    dati = misurazione.estrai_dati_misurazione()
    logger.debug(f"Misurazione ricevuta dal sensore {id_sensore}: {dati}")

    successo, id_batch_chiuso = db.inserisci_misurazione(id_sensore=id_sensore, dati=dati)
    if not successo:
        logger.error(f"Errore nella memorizzazione della misurazione del sensore {id_sensore}")
        raise HTTPException(status_code=500, detail="Errore nella memorizzazione della misurazione_in_ingresso.")

    risposta = {
        "status": "misurazione_in_ingresso registrata",
        "sensore": id_sensore,
        "ricevuto_alle": datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    }

    if id_batch_chiuso is not None:
        logger.debug(f"Batch completato: ID {id_batch_chiuso}. Avvio elaborazione.")
        risposta["batch_completato"] = True
        risposta["id_batch"] = id_batch_chiuso
        gestisci_batch_completato(id_batch_chiuso, db, ENDPOINT_CLOUD)

    return JSONResponse(content=risposta)

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
