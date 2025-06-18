import asyncio
import json
import logging
from config.costanti_produttore import ENDPOINT_CLOUD_SENSORI, ENDPOINT_CLOUD_BATCH
from database.gestore_db import GestoreDatabase
from utils.fog_api_utils import gestisci_batch_completo, invia_payload
logger = logging.getLogger(__name__)

# === TASK PER INVIO SENSORI NON CONFERMATI ===
async def task_invio_sensori(gestore_database: GestoreDatabase, intervallo: int = 20):
    await asyncio.sleep(5)
    while True:
        logger.info("[SENSORI] Controllo sensori da inviare...")
        lista_sensori = gestore_database.ottieni_sensori_non_conferma_ricezione()
        for sensore in lista_sensori:
            id_sensore = sensore.get("id_sensore", "??")
            try:
                logger.debug(f"[SENSORI] Tentativo invio id_sensore={id_sensore}...")
                if invia_payload(sensore, ENDPOINT_CLOUD_SENSORI, gestore_database):
                    logger.info(f"[SENSORI] Inviato correttamente id_sensore={id_sensore}")
                else:
                    logger.warning(f"[SENSORI] Invio fallito per id_sensore={id_sensore}")
                    break # interrompi il ciclo in caso di errori
            except Exception as e:
                logger.error(f"[SENSORI] Errore invio id_sensore={id_sensore}: {e}")
        await asyncio.sleep(intervallo)


async def task_invio_batch(gestore_db: GestoreDatabase, intervallo: int = 60):
    await asyncio.sleep(5)
    while True:
        logger.info("[BATCH-JSON] Controllo batch da inviare...")
        # restituisce lista di tuple (id_batch, payload_json)
        lista_id_payload = gestore_db.ottieni_payload_batch_pronti_per_invio()
        for id_batch, payload_json in lista_id_payload:
            try:
                if isinstance(payload_json, str):
                    payload = json.loads(payload_json)
                else:
                    payload = payload_json
                logger.debug(f"[BATCH-JSON] Tentativo invio id_batch={id_batch}...")
                if invia_payload(payload, ENDPOINT_CLOUD_BATCH, gestore_db):
                    logger.info(f"[BATCH-JSON] Inviato correttamente id_batch={id_batch}")
                else:
                    logger.warning(f"[BATCH-JSON] Invio fallito per id_batch={id_batch}")
                    break  # se fallisce, interrompi per evitare retry inutili
            except Exception as e:
                logger.error(f"[BATCH-JSON] Errore invio id_batch={id_batch}: {e}")

        await asyncio.sleep(intervallo)

# === TASK PER ELABORAZIONE PERIODICA DEI BATCH COMPLETI ===
async def task_elabora_batch_completi(db, intervallo: int = 60):
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
                logger.debug(f"[BATCH-ELAB] INIZIO ELABORAZIONE batch {id_batch}...")
                if not gestisci_batch_completo(id_batch, db):
                    logger.debug(f"[BATCH-ELAB] Elaborazione batch {id_batch} FALLITA")
            except Exception as e:
                logger.error(f"[BATCH-ELAB] Errore durante elaborazione batch {id_batch}: {e}")
        await asyncio.sleep(intervallo)


# === AVVIO DEI TASK ASINCRONI ===
async def avvia_task_periodici(db: GestoreDatabase):
    task1 = asyncio.create_task(task_invio_sensori(db))
    task2 = asyncio.create_task(task_invio_batch(db))
    task3 = asyncio.create_task(task_elabora_batch_completi(db))
    try:
        await asyncio.gather(task1, task2, task3)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")

