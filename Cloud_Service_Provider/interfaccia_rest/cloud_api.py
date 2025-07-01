import logging
from contextlib import asynccontextmanager
from typing import Dict, List

import uvicorn
from fastapi import Depends
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from Classi_comuni.entita.modelli_dati import PacchettoBatchMisurazioni, DatiListaSensori, DatiBatch
from Cloud_Service_Provider.auth.auth_utils import richiede_permesso_scrittura, richiede_permesso_verifica_estesa, \
    richiede_permesso_verifica
from Cloud_Service_Provider.config.istanze_globali import gestore_db
from Cloud_Service_Provider.entita.utente_api import UtenteAPI
from Cloud_Service_Provider.interfaccia_rest.utils.cloud_api_utils import elabora_pacchetto_batch_misurazioni, \
    recupera_metadati_misurazione_sensore, recupera_dati_misurazione_sensore
from cloud_api_utils import costruisci_mappa_id_hash_foglie
from modelli_dati import DatiMisurazioneSensore
from modelli_metadati import MetaDatiMisurazioneSensore, MetaDatiBatch

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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

    #inserisci la lista di sensori
    id_sensori_inseriti = gestore_db.inserisci_lista_sensori(payload.sensori)

    # controlla se la lista è vuota
    if not id_sensori_inseriti:
        messaggio = "Nessun sensore registrato. Errore del database."
    else:
        messaggio = f"{len(id_sensori_inseriti)} sensori registrati correttamente su {len(payload.sensori)}"

    conferma = bool(id_sensori_inseriti)

    return JSONResponse(content={
        "conferma_ricezione": conferma,
        "id_sensori": id_sensori_inseriti,
        "messaggio": messaggio
    })


@app.post("/batch")
def ricevi_batch(payload: PacchettoBatchMisurazioni, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    """
    Endpoint per ricevere un intero batch con le sue misurazioni.
    Il payload contiene un oggetto DatiBatch e una lista di DatiMisurazione.
    """
    logger.info(f"Ricezione batch {payload.batch.id_batch} con {len(payload.misurazioni)} misurazioni...")
    successo_operazione = elabora_pacchetto_batch_misurazioni(payload)

    if successo_operazione:
        logger.info(f"Batch {payload.batch.id_batch} salvato correttamente con {len(payload.misurazioni)} misurazioni....")
        return JSONResponse(content={
            "conferma_ricezione": True,
            "id_batch": payload.batch.id_batch,
            "messaggio": "Batch e Misurazioni salvate correttamente"
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
        logger.debug(f"[DEBUG] Ricevuta richiesta per costruzione mappa id-hash del batch con id = {id_batch}")
        mappa_id_hash = costruisci_mappa_id_hash_foglie(id_batch)
        return mappa_id_hash
    except Exception as e:
        logger.error(f"[ERRORE GET /batch] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === METODI a COMPLETAMENTO DELLA VERIFICA DELL'INTEGRITA' === #
@app.post("/metadata/misurazione-sensore", response_model=list[MetaDatiMisurazioneSensore])
def ottieni_metadata_misurazione_sensore(lista_id_mis: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    ris_query : List[MetaDatiMisurazioneSensore]= recupera_metadati_misurazione_sensore(lista_id_mis)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Misurazioni non trovate")
    return ris_query
#
@app.get("/metadata/batch/{id_batch}", response_model=MetaDatiBatch)
def ottieni_metadata_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    ris_query : MetaDatiBatch = gestore_db.ottieni_metadata_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query

@app.get("/metadata/batch", response_model=list[MetaDatiBatch])
def ottieni_metadata_batch(utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    #restituisce l'elenco di metadati dei batch attualmente memorizzati nel sistema
    ris_query: MetaDatiBatch = gestore_db.ottieni_tutti_metadata_batch()
    if not ris_query:
        raise HTTPException(status_code=404, detail="Nessun Batch attualmente memorizzato nel sistema")
    return ris_query

@app.post("/dati/misurazione-sensore", response_model=list[DatiMisurazioneSensore])
def ricostruisci_dati_misurazione_sensore(lista_id: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica_estesa)):
    try:
        return recupera_dati_misurazione_sensore(lista_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/dati/batch/{id_batch}", response_model=DatiBatch)
def ricostruisci_data_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica_estesa)):
    ris_query : DatiBatch = gestore_db.ottieni_data_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()