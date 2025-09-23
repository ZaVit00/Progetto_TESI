import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Union
import uvicorn
from fastapi import FastAPI, HTTPException, Body
from costanti_comuni import TipoServizio
from istanze_globali_produttore import gestore_db
from gestione_soglia_batch import aggiorna_soglia_chiusura_batch
from registro_log import setup_logger
from task_manager import avvia_task_periodici

"""
Import dei modelli di misurazione_in_ingresso specifici
i modelli di misurazione in ingresso e dati sensore in ingresso servono solo al fog node e
non al cloud provider (Il fog node gestisce solo la comunicazione interna tra sensori e nodo fog)
"""
from dati_misurazione_in_ingresso import DatiMisurazioneInIngressoJoystick, DatiMisurazioneInIngressoAccelerometro, \
    DatiMisurazioneInIngressoGiroscopio, DatiMisurazioneInIngressoTemperatura, DatiMisurazioneInIngressoUmidita
from dati_sensore_in_ingresso import DatiSensoreInIngresso

logger = setup_logger(TipoServizio.PRODUTTORE, module=__name__, level=logging.DEBUG)

#Funzione che viene eseguita all'avvio dell'applicazione
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Avvio dei task periodici per invio dati sensori, invio payload al cloud,"
                "elaborazione dei batch completi")
    asyncio.create_task(avvia_task_periodici())
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    #chiusura della connesione del database sqlite (dati_nodo_fog.sqlite)
    gestore_db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)

@app.post("/sensore", summary="Registra un sensore", response_model=dict)
async def registra_sensore(dati_sensore: DatiSensoreInIngresso):
    """
    Endpoint per la registrazione di un sensore.
    """
    if not gestore_db.inserisci_dati_sensore(dati_sensore):
        logger.error(f"Errore nella registrazione del sensore {dati_sensore.id_sensore}")
        raise HTTPException(status_code=500, detail="Errore nella registrazione del sensore.")

    logger.info(f"Registrazione completata per il sensore {dati_sensore.id_sensore}, aggiorno soglia batch...")
    """
    Passo cruciale: aggiornamento della soglia dinamica di chiusura batch.
    Ogni volta che un nuovo sensore viene registrato, comunica la propria frequenza di invio dati.
    Questa informazione modifica la soglia di chiusura dei batch, che deve quindi essere ricalcolata
    per mantenere coerente la dimensione/tempo dei batch rispetto al numero e alla frequenza dei sensori attivi.
    """
    aggiorna_soglia_chiusura_batch() # step cruciale da guardare bene

    return {
        "status": "sensore registrato",
        "sensore": dati_sensore.id_sensore,
        "ricevuto_alle": datetime.now().strftime("%H:%M:%S - %d/%m/%Y"),
        "timestamp_iso": datetime.now().isoformat()
    }

"""
Con Field(discriminator="tipo"), FastAPI:
- legge il Body ed estrae il campo "tipo" dal JSON in ingresso
- se vale "joystick", usa MisurazioneInIngressoJoystick 
- se vale "accelerometro", usa MisurazioneInIngressoAccelerometro
- se vale "giroscopio", usa MisurazioneInIngressoGiroscopio
- possibile estensione per future misurazioni di sensori differenti (importante riutilizzare la stessa sintassi)
- valida il resto del contenuto (i campi) in base al modello di classe selezionato
"""
misurazioni_accettate = Union[DatiMisurazioneInIngressoJoystick,
DatiMisurazioneInIngressoGiroscopio,
DatiMisurazioneInIngressoAccelerometro,
DatiMisurazioneInIngressoTemperatura,
DatiMisurazioneInIngressoUmidita]
@app.post("/misurazione", summary="Registra una misurazione", response_model=dict)
async def registra_misurazione(mis: misurazioni_accettate = Body(..., discriminator="tipo")):
    """
    Endpoint per ricevere e salvare una misurazione proveniente da un sensore registrato.
    La misurazione viene associata al batch attivo o ne crea uno nuovo se necessario.
    """
    id_sensore:str = mis.id_sensore.upper()
    #estraggo un dizionario contenente solo i dati effettivi dalla misurazione separandolo dai metadata
    dati = mis.estrai_dati_misurazione()
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
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
