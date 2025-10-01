# Import dei moduli standard per logging, contesto asincrono e tipizzazione
import logging
from contextlib import asynccontextmanager
from typing import Dict, List
# Avvio server FastAPI
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Import di modelli condivisi tra i progetti
from Classi_comuni.entita.modelli_dati import (
    BatchPayload, DatiListaSensoriPayload, DatiBatch
)
# Middleware di autenticazione e autorizzazione basato sui ruoli API
from Cloud_provider.auth.auth_utils import (
    richiede_permesso_scrittura,
    richiede_permesso_verifica_estesa,
    richiede_permesso_verifica
)
# Istanza globale del DB locale (PostgreSQL), usata da tutti i metodi
from Cloud_provider.config.istanze_globali import gestore_db
# Classe utente con controllo permessi
from Cloud_provider.entita.utente_api import UtenteAPI
# Utility per elaborazione dei payload ricevuti
from cloud_api_utils import (
    elabora_pacchetto_batch_misurazioni,
    recupera_metadati_misurazione_sensore,
    recupera_dati_misurazione_sensore
)
# Utility per la costruzione della mappa id_misurazione → hash
from cloud_api_utils import costruisci_mappa_id_hash_foglie
from costanti_comuni import TipoServizio
# Modelli Pydantic specifici del cloud
from modelli_dati import DatiMisurazioneSensorePayload
from modelli_metadati import MetadatiMisurazioneSensorePayload, MetadatiBatchPayload
from registro_log import setup_logger

logger = setup_logger(TipoServizio.CLOUD, module=__name__, level=logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("StartUp Applicazione")
    yield  # Applicazione avviata
    #operazioni da effettuare alla terminazione dell'applicazione
    logger.info("Chiusura dell'applicazione: chiusura connessione al DB.")
    gestore_db.chiudi_connessione()

# Istanzia l'app FastAPI con supporto al lifecycle
app = FastAPI(lifespan=lifespan)

# === METODI PER L'INSERIMENTO DEI DATI ===
# Questi endpoint sono utilizzati dal nodo produttore per inviare
# al cloud i sensori registrati e i batch (raggruppamento di misurazioni)
@app.post("/sensori")
def ricevi_lista_sensori(payload: DatiListaSensoriPayload, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    """
    Inserisce una lista di nuovi sensori nel DB.
    Restituisce conferma e gli ID generati.
    """
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
def ricevi_batch(payload: BatchPayload, utente: UtenteAPI = Depends(richiede_permesso_scrittura)):
    """
    Endpoint per ricevere un intero batch (con le sue misurazioni)
    Il payload contiene un oggetto DatiBatch e una lista di DatiMisurazione.
    """
    if payload.batch is None:
        raise HTTPException(status_code=400, detail="DatiBatch non avvalorato")
    if not payload.misurazioni:
        raise HTTPException(status_code=400, detail="DatiMisurazione è una lista vuota")

    logger.info(f"Ricezione batch {payload.batch.id_batch} con {len(payload.misurazioni)} misurazioni...")
    successo_operazione = elabora_pacchetto_batch_misurazioni(payload)

    if successo_operazione:
        logger.info(f"Batch {payload.batch.id_batch} salvato correttamente con {len(payload.misurazioni)} misurazioni....")
        return JSONResponse(content={
            "conferma_ricezione": True,
            "id_batch": payload.batch.id_batch,
            "messaggio": "Payload Batch (DatiBatch + Lista DatiMisurazione) salvato correttamente"
        })
    else:
        logger.warning(f"Errore durante il salvataggio del batch {payload.batch.id_batch}.")
        return JSONResponse(
            content={"conferma_ricezione": False, "messaggio": "Errore durante il salvataggio del batch"},
            status_code=500
        )

# === METODI PER LA VERIFICA DELL'INTEGRITÀ ===
# Questi endpoint sono utilizzati dal nodo verificatore per ottenere
# la mappa id → hash delle foglie (batch + misurazioni)
@app.get("/batch/mappa-id-hash/{id_batch}", response_model=Dict[int, str])
def ottieni_mappa_id_hash_foglie(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    """
    Restituisce la mappa (id_misurazione → hash foglia) per un batch
    specifico inteso come raggruppamento di misurazioni
    """
    try:
        logger.debug(f"[DEBUG] Ricevuta richiesta per costruzione mappa id-hash del batch con id = {id_batch}")
        mappa_id_hash = costruisci_mappa_id_hash_foglie(id_batch)
        return mappa_id_hash
    except Exception as e:
        logger.error(f"[ERRORE GET /batch] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# METODI UTILIZZATI UNICAMENTE DAL PRODUTTORE CHE DISPONE DEI DATI ORIGINALI
# PER LA VERIFICA ESTESA (determinare le differenze campo per campo esattamente)
@app.post("/dati/misurazione-sensore", response_model=list[DatiMisurazioneSensorePayload])
def ricostruisci_dati_misurazione_sensore(lista_id: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica_estesa)):
    """
    Restituisce i dati completi delle misurazioni inner join sensore (compresi i dati sensibili),
    accessibili solo al produttore.
    """
    ris_query : list[DatiMisurazioneSensorePayload] = recupera_dati_misurazione_sensore(lista_id)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Nessuna Misurazione trovata associata al batch")
    return ris_query

@app.get("/dati/batch/{id_batch}", response_model=DatiBatch)
def ricostruisci_dati_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica_estesa)):
    """
    Ricostruisce e restituisce i dati completi del batch (solo per verifica estesa).
    Nota bene: in questo caso con batch intendiamo solo le informazioni della tupla
    del batch memorizzata nel DB interno al cloud (PostegreSQL)
    """
    ris_query : DatiBatch = gestore_db.ottieni_dati_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query

"""
=== METODI PER OTTENERE I METADATI (informazioni NON SENSIBILI sui dati memorizzati) ===
Quando il verificatore rileva un’anomalia,
può richiedere al cloud i metadati (informazioni non sensibili)
relativi alla tupla del batch e alle misurazioni (e le informazioni sul sensore che ha prodotto la misurazione) 
sospette, così da avere una prima valutazione “ad alto livello” della situazione.

Importante: anche questi metadati potrebbero essere stati
manomessi. Solo il produttore, che conserva
i dati originali NON alterati, è in grado di stabilire con certezza
quali modifiche siano effettivamente avvenute ma il verificatore può solo determinare
l'anomalia di integrità (coerentemente con il principio della separazione dei ruoli)
"""
@app.post("/metadata/misurazione-sensore", response_model=list[MetadatiMisurazioneSensorePayload])
def ottieni_metadata_misurazione_sensore(lista_id_mis: List[int], utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    """
    Restituisce i metadati (non sensibili) di sensore e misurazione per ID specificati.
    Usato per mostrare info leggibili su dati potenzialmente alterati
    su una misurazione + sensore che lo ha prodotto.
    """
    ris_query : List[MetadatiMisurazioneSensorePayload]= recupera_metadati_misurazione_sensore(lista_id_mis)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Misurazioni non trovate")
    return ris_query

@app.get("/metadata/batch/{id_batch}", response_model=MetadatiBatchPayload)
def ottieni_metadata_batch(id_batch: int, utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    """
    Restituisce i metadati del batch richiesto (non include le misurazioni).
    """
    ris_query : MetadatiBatchPayload = gestore_db.ottieni_metadata_batch(id_batch)
    if not ris_query:
        raise HTTPException(status_code=404, detail="Batch non trovato")
    return ris_query

@app.get("/metadata/batch", response_model=list[MetadatiBatchPayload])
def ottieni_tutti_metadata_batch(utente: UtenteAPI = Depends(richiede_permesso_verifica)):
    #restituisce l'elenco di metadati dei batch attualmente memorizzati nel sistema
    ris_query: MetadatiBatchPayload = gestore_db.ottieni_tutti_metadata_batch()
    if not ris_query:
        raise HTTPException(status_code=404, detail="Nessun Batch attualmente memorizzato nel sistema")
    return ris_query


def main():
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()