import asyncio
import json
import logging

from database.gestore_db import GestoreDatabase
from utils.fog_api_utils import gestisci_batch_completo, invia_payload
logger = logging.getLogger(__name__)

# === TASK GENERICO PER INVIO ELEMENTI AL CLOUD ===
async def task_retry_generico(estrai_elementi_fn, chiave_id: str, etichetta_log: str, endpoint_cloud: str, intervallo: int = 60):
    """
    Task generico per invio periodico di elementi non ancora confermati al cloud provider.
    Usato sia per i sensori che per i batch con payload JSON.
    """
    await asyncio.sleep(5)  # piccolo delay iniziale
    while True:
        logger.info(f"[{etichetta_log}] Controllo elementi da inviare...")
        lista = estrai_elementi_fn()
        for elemento in lista:
            # Se elemento è una stringa JSON (batch), lo parsiamo (diventa un dizionario)
            if isinstance(elemento, str):
                elemento = json.loads(elemento)
            #"Prova a prendere elemento[chiave_id]; se non esiste, usa il valore di fallback "??"
            identificativo = elemento.get(chiave_id, "??")
            try:
                logger.debug(f"[{etichetta_log}] Tentativo invio {chiave_id}={identificativo}...")
                if invia_payload(elemento, endpoint_cloud):
                    logger.info(f"[{etichetta_log}] Inviato correttamente {chiave_id}={identificativo}")
                else:
                    logger.warning(f"[{etichetta_log}] Invio fallito per {chiave_id}={identificativo}")
                    break  # se il cloud è down, interrompe il ciclo
            except Exception as e:
                logger.error(f"[{etichetta_log}] Errore durante invio {chiave_id}={identificativo}: {e}")
        await asyncio.sleep(intervallo)

# === TASK PER ELABORAZIONE PERIODICA DEI BATCH COMPLETI ===
async def task_elabora_batch_completi(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Controlla periodicamente se esistono batch completi (hanno raggiunto la soglia)
    ma non ancora elaborati (manca Merkle Root o JSON), e li elabora.
    """
    await asyncio.sleep(10)
    while True:
        logger.info("[BATCH-ELAB] Controllo batch completi da elaborare...")
        lista_id_batch = db.ottieni_id_batch_completi()
        logger.debug(f"[BATCH-ELAB] Lista batch chiusi {lista_id_batch}")
        for id_batch in lista_id_batch:
            try:
                logger.debug(f"[BATCH-ELAB] Elaborazione batch {id_batch}...")
                if not gestisci_batch_completo(id_batch, db):
                    logger.debug(f"[BATCH-ELAB] Elaborazione batch {id_batch} FALLITA")
            except Exception as e:
                logger.error(f"[BATCH-ELAB] Errore durante elaborazione batch {id_batch}: {e}")
        await asyncio.sleep(intervallo)

# === AVVIO DEI TASK ASINCRONI ===
async def avvia_task_periodici(db : GestoreDatabase, endpoint_cloud: str):
    """
    task1 = asyncio.create_task(task_retry_generico(
        estrai_elementi_fn=db.ottieni_sensori_non_conferma_ricezione,
        chiave_id="id_sensore",
        etichetta_log="SENSORI",
        endpoint_cloud=endpoint_cloud,
        intervallo=30
    ))

    task2 = asyncio.create_task(task_retry_generico(
        estrai_elementi_fn=db.ottieni_payload_batch_pronti_per_invio,
        chiave_id="id_batch",
        etichetta_log="BATCH-JSON",
        endpoint_cloud=endpoint_cloud,
        intervallo=60
    ))
    """
    task3 = asyncio.create_task(task_elabora_batch_completi(
        db=db,
        endpoint_cloud=endpoint_cloud,
        intervallo=60
    ))

    try:
        #task1, task2
        await asyncio.gather(task3)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")
