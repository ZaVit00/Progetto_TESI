from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union

# Import dei modelli di misurazione specifici
from entita.misurazione_temperatura import MisurazioneTemperatura
from entita.misurazione_joystick import MisurazioneJoystick
from entita.sensore import Sensore
from database.gestore_db import GestoreDatabase

app = FastAPI()
db = GestoreDatabase(soglia_batch=10)


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
async def ricevi_misurazione(misurazione: Union[MisurazioneJoystick, MisurazioneTemperatura]):
    """
    Endpoint per ricevere e salvare una misurazione da un sensore registrato.
    Restituisce anche l'ID del batch chiuso, se la soglia è stata raggiunta.
    """
    id_sensore = misurazione.id_sensore
    # Rimuovi i metadata dal JSON per ottenere solo i dati della misurazione
    dati = misurazione.estrai_dati_misurazione()

    # Inserimento della misurazione nel database
    successo, id_batch_chiuso = db.inserisci_misurazione(id_sensore=id_sensore, dati=dati)

    if not successo:
        raise HTTPException(status_code=500, detail="Errore nella memorizzazione della misurazione.")

    risposta = {
        "status": "misurazione registrata",
        "sensore": id_sensore,
        "ricevuto_alle": datetime.now().strftime("%H:%M:%S - %d/%m/%Y")
    }

    if id_batch_chiuso is not None:
        #estendo la risposta con altri due campi
        risposta["batch_completato"] = True
        risposta["id_batch"] = id_batch_chiuso
    
    return JSONResponse(content=risposta)