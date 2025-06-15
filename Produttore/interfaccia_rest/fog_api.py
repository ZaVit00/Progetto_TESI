from contextlib import asynccontextmanager
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, Body
from datetime import datetime
from typing import Union, Annotated
import asyncio
# Import dei modelli di misurazione_in_ingresso specifici
from misurazioni_in_ingresso import MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura
from costanti_produttore import SOGLIA_BATCH, ENDPOINT_CLOUD_STORAGE
from entita.sensore_base import Sensore
from database.gestore_db import GestoreDatabase
from retry_invio_dati_batch import retry_invio_batch_periodico

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)
# Istanza del database (con soglia per batch)
db = GestoreDatabase(soglia_batch=SOGLIA_BATCH)
# Endpoint del cloud service


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio del task periodico per il retry dei batch.")
    asyncio.create_task(retry_invio_batch_periodico(db, ENDPOINT_CLOUD_STORAGE))
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)

@app.post("/sensori")
async def registra_sensore(sensore: Sensore):
    """
    Endpoint per la registrazione di un sensore.
    """
    if not db.inserisci_dati_sensore(sensore.id_sensore, sensore.descrizione):
        logger.error(f"Errore nella registrazione del sensore {sensore.id_sensore}")
        raise HTTPException(status_code=500, detail="Errore nella registrazione del sensore.")

    logger.info(f"Sensore registrato correttamente: {sensore.id_sensore}")
    return {
        "status": "sensore registrato",
        "id": sensore.id_sensore,
        "descrizione": sensore.descrizione
    }

"""
Con discriminator="tipo", FastAPI:
- legge il Body ed estrae il campo "tipo" dal JSON in ingresso
- se vale "joystick", usa MisurazioneInIngressoJoystick 
- se vale "temperatura", usa MisurazioneInIngressoTemperatura altrimenti
- valida il resto del contenuto (i campi) in base al modello di classe selezionato
"""
MisurazioneInIngresso = Annotated[Union[MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura],
                         Body(discriminator="tipo")]
@app.post("/misurazioni")
async def ricevi_misurazione(misurazione: MisurazioneInIngresso):
    """
    Endpoint per ricevere e salvare una misurazione proveniente da un sensore registrato.
    La misurazione viene associata al batch attivo o ne crea uno nuovo se necessario.
    """
    id_sensore = misurazione.id_sensore
    dati = misurazione.estrai_dati_misurazione()
    logger.debug(f"Misurazione ricevuta dal sensore {id_sensore}: {dati}")
    successo_operazione = db.inserisci_misurazione(id_sensore=id_sensore, dati=dati)
    if not successo_operazione:
        logger.error("Errore nella memorizzazione della misurazione", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Errore nella memorizzazione della misurazione."
        )
    risposta = {
        "status": "misurazione in ingresso registrata",
        "sensore": id_sensore,
        "ricevuto_alle": datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
        "timestamp_iso": datetime.now().isoformat()
    }
    return risposta


def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
