from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union
import asyncio

# Import dei modelli di misurazione_in_ingresso specifici
from modelli import MisurazioneInIngressoJoystick, MisurazioneInIngressoTemperatura
from sensore_base import Sensore
from database.gestore_db import GestoreDatabase
from fog_api_utils import gestisci_batch_completato
from retry_invio_batch import retry_invio_batch_periodico

# misurazioni + ultima foglia batch che è la potenza di due
db = GestoreDatabase(soglia_batch=31)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[INFO] Avvio del task periodico per il retry dei batch.")
    asyncio.create_task(retry_invio_batch_periodico(db, ENDPOINT_CLOUD))
    yield  #Applicazione avviata
    # ✅ Chiusura della connessione in uscita
    db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifespan
app = FastAPI(lifespan=lifespan)
#Endpoint del cloud service
ENDPOINT_CLOUD = "http://localhost:8080/api/invia"


@app.post("/sensori")
async def registra_sensore(sensore: Sensore):
    """
    Endpoint per la registrazione manuale di un sensore.
    """
    if not db.inserisci_dati_sensore(sensore.id_sensore, sensore.descrizione):
        raise HTTPException(status_code=500, detail="Errore nella registrazione del sensore.")
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
    # Rimuovi i metadata dal JSON per ottenere solo i dati della misurazione_in_ingresso
    dati = misurazione.estrai_dati_misurazione()

    # Inserimento della misurazione_in_ingresso nel database
    successo, id_batch_chiuso = db.inserisci_misurazione(id_sensore=id_sensore, dati=dati)
    if not successo:
        raise HTTPException(status_code=500, detail="Errore nella memorizzazione della misurazione_in_ingresso.")
    #creazione del messaggio di risposta
    risposta = {
        "status": "misurazione_in_ingresso registrata",
        "sensore": id_sensore,
        "ricevuto_alle": datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    }

    # Elaborazione di un batch che può essere inviato al cloud
    if id_batch_chiuso is not None:
        #estendo la risposta con altri due campi
        risposta["batch_completato"] = True
        risposta["id_batch"] = id_batch_chiuso
        gestisci_batch_completato(id_batch_chiuso, db, ENDPOINT_CLOUD)

    return JSONResponse(content=risposta)

"""
@app.post("/conferma_batch")
def conferma_ricezione_batch(batch: ConfermaBatch):
    pass
    
    id_batch = batch.id_batch
    # Aggiorna lo stato del batch solo se esiste ed è completato
    if not db.imposta_batch_conferma_ricezione(id_batch):
        raise HTTPException(
            status_code=404,
            detail=f"Batch {id_batch} non trovato o non completato."
        )

    # Elimina le misurazioni ora che la conferma è avvenuta
    if not db.elimina_misurazioni_batch(id_batch):
        raise HTTPException(
            status_code=500,
            detail=f"Errore nell'eliminazione delle misurazioni per il batch {id_batch}."
        )

    return {"status": "successo", "id_batch": id_batch, "messaggio": batch.messaggio}
"""
"""
    Endpoint chiamato dal cloud provider per confermare la ricezione di un batch.
    Se la conferma è valida, il campo 'conferma_ricezione' del batch viene aggiornato a 1
    e le misurazioni locali associate al batch vengono eliminate.
"""