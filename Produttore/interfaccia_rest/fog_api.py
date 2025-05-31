from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Union

# Import dei modelli di misurazione specifici
from entita.misurazione_temperatura import MisurazioneTemperatura
from entita.misurazione_joystick import MisurazioneJoystick

app = FastAPI()

@app.post("/misurazioni")
async def invia_misurazione(
    misurazione: Union[MisurazioneJoystick, MisurazioneTemperatura]):
    """
    Endpoint unificato per gestire qualsiasi tipo di misurazione,
    da sensori di differenti tipi
    FastAPI utilizza la struttura del payload JSON per determinare
    automaticamente quale modello Pydantic utilizzare.
    """
    # Conversione in dizionario secondo il tipo di misurazione
    dati = misurazione.to_dict()






    """ scopi di debug
    print("----- MISURAZIONE RICEVUTA -----")
    print("Dati:", dati)
    Risposta JSON
    return JSONResponse(content={
        "status": "ok",
        "tipo": misurazione.__class__.__name__,
        "timestamp": timestamp
    })
    """
