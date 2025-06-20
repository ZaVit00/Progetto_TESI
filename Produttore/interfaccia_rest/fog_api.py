import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Union, Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Body

from Classi_comuni.entita.modelli_dati import DatiSensore
from config.costanti_produttore import SOGLIA_BATCH
from database.gestore_db import GestoreDatabase
# Import dei modelli di misurazione_in_ingresso specifici
# i modelli di misurazione in ingresso servono solo al fog node e non al cloud provider
from misurazioni_in_ingresso import MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura
from task_manager import avvia_task_periodici

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

# Istanza del database (con soglia per batch)
gestore_db = GestoreDatabase(soglia_batch=SOGLIA_BATCH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio dei task periodici per invio dati sensori, invio payload al cloud,"
                "elaborazione dei batch completi")
    asyncio.create_task(avvia_task_periodici(gestore_db))
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    gestore_db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)
@app.post("/sensori", summary="Registra un sensore", response_model=dict)
async def registra_sensore(dati_sensore: DatiSensore):
    """
    Endpoint per la registrazione di un sensore.
    """
    if not gestore_db.inserisci_dati_sensore(dati_sensore.id_sensore.upper(), dati_sensore.descrizione,
                                             dati_sensore.tipo):
        logger.error(f"Errore nella registrazione del sensore {dati_sensore.id_sensore}")
        raise HTTPException(status_code=500, detail="Errore nella registrazione del sensore.")

    logger.info(f"Sensore registrato correttamente: {dati_sensore.id_sensore}")
    return {
        "status": "sensore registrato",
        "id": dati_sensore.id_sensore,
        "descrizione": dati_sensore.descrizione
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
@app.post("/misurazioni", summary="Registra una misurazione", response_model=dict)
async def registra_misurazione(misurazione: MisurazioneInIngresso):
    """
    Endpoint per ricevere e salvare una misurazione proveniente da un sensore registrato.
    La misurazione viene associata al batch attivo o ne crea uno nuovo se necessario.
    """
    id_sensore:str = misurazione.id_sensore.upper()
    #estraggo un dizionario contenente solo i dati effettivi dalla misurazione separandolo dai metadata
    dati = misurazione.estrai_dati_misurazione()
    logger.debug(f"Misurazione ricevuta dal sensore {id_sensore}: {dati}")
    successo_operazione = gestore_db.inserisci_misurazione(id_sensore=id_sensore, dati=dati)
    if not successo_operazione:
        logger.error("Errore nella memorizzazione della misurazione del sensore", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Errore nella memorizzazione della misurazione del sensore."
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
