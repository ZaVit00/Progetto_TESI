import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List
import uvicorn
from dotenv import load_dotenv
from fastapi import Depends
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from Classi_comuni.entita.modelli_dati import PacchettoBatchMisurazioni, DatiListaSensori, DatiBatch
from modelli_dati import DatiMisurazioneSensore
from Cloud_Service_Provider.auth.auth_utils import richiede_permesso_scrittura, richiede_permesso_verifica_profonda, \
    richiede_permesso_verifica
from Cloud_Service_Provider.database.gestore_db import GestoreDatabase
from Cloud_Service_Provider.entita.utente_api import UtenteAPI
from Cloud_Service_Provider.interfaccia_rest.utils.cloud_api_utils import elabora_payload, elabora_lista_sensori, \
    recupera_metadati_misurazione_sensore, recupera_dati_misurazione_sensore
from cloud_api_utils import costruisci_mappa_id_hash_foglie
from modelli_metadati import MetaDatiMisurazioneSensore, MetaDatiBatch, MetaDatiMisurazione

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
def registra_lista_sensori(payload: DatiListaSensori, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    if not payload.sensori:
        raise HTTPException(status_code=400, detail="Lista sensori vuota.")
    id_inseriti = elabora_lista_sensori(payload, gestore_db)
    conferma = bool(id_inseriti)
    return JSONResponse(content={
        "conferma_ricezione": conferma,
        "id_sensori": id_inseriti,
        "messaggio": f"{len(id_inseriti)} sensori registrati correttamente su {len(payload.sensori)}"
    })


@app.post("/batch")
def ricevi_batch(payload: PacchettoBatchMisurazioni, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
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

@app.get("/batch/mappa-id-hash/{id_batch}", response_model=Dict[int, str])
def ottieni_mappa_id_hash_foglie(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    try:
        logger.debug(f"[DEBUG] Ricevuta richiesta batch con id = {id_batch}")
        mappa_id_hash = costruisci_mappa_id_hash_foglie(id_batch, gestore_db)
        return mappa_id_hash
    except Exception as e:
        logger.error(f"[ERRORE GET /batch] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === METODI a COMPLETAMENTO DELLA VERIFICA DELL'INTEGRITA' === #
@app.post("/metadata/misurazione-sensore", response_model=list[MetaDatiMisurazioneSensore])
def ricostruisci_metadata_misurazione_sensore(lista_id: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    if not lista_id:
        raise HTTPException(status_code=400, detail="Lista di ID vuota")
    try:
        return recupera_metadati_misurazione_sensore(lista_id, gestore_db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
#
@app.get("/metadata/batch/{id_batch}", response_model=MetaDatiBatch)
def ricostruisci_metadata_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    ris_query : MetaDatiBatch = gestore_db.ottieni_metadata_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query


@app.post("/dati/misurazione-sensore", response_model=list[DatiMisurazioneSensore])
def ricostruisci_dati_misurazione_sensore(lista_id: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica_profonda)):
    try:
        return recupera_dati_misurazione_sensore(lista_id, gestore_db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/dati/batch/{id_batch}", response_model=DatiBatch)
def ricostruisci_data_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica_profonda)):
    ris_query : DatiBatch = gestore_db.ottieni_data_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()