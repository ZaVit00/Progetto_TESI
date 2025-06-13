import asyncio
import json
import logging
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato, invia_payload

# Logger locale
logger = logging.getLogger(__name__)

async def reinvia_batch_gia_pronti(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Task periodico: reinvia i batch già pronti con Merkle Root e payload_json.
    Default: ogni 60 secondi.
    """
    await asyncio.sleep(10)  # primo check rapido
    while True:
        logger.info("Controllo batch già pronti per invio...")
        batch_payload_list = db.get_payload_batch_non_inviati()
        for p in batch_payload_list:
            try:
                payload_dict = json.loads(p)
                id_batch = payload_dict["batch"]["id_batch"]
                if invia_payload(payload_dict, endpoint_cloud):
                    logger.debug(f"Batch {id_batch} reinviato correttamente.")
                else:
                    logger.warning(f"Reinvio fallito per batch {id_batch}.")
                    break  # interrompe il ciclo se il cloud è down
            except Exception as e:
                logger.error(f"Errore durante la conversione/invio di un batch: {e}")
        await asyncio.sleep(intervallo)

async def recupera_batch_incompleti(db, endpoint_cloud: str, intervallo: int = 300):
    """
    Task periodico: tenta di recuperare i batch incompleti.
    Default: ogni 5 minuti (300 secondi).
    """
    await asyncio.sleep(20)  # delay iniziale diverso
    while True:
        logger.info("Controllo batch incompleti (manca Merkle Root o Payload)...")
        id_batch_list = db.estrai_batch_incompleti()
        for id_batch in id_batch_list:
            try:
                logger.debug(f"Tentativo di rielaborazione batch ID {id_batch}...")
                gestisci_batch_completato(id_batch, db, endpoint_cloud)
            except Exception as e:
                logger.error(f"Errore durante la rielaborazione del batch {id_batch}: {e}")
        await asyncio.sleep(intervallo)

async def retry_invio_batch_periodico(db, endpoint_cloud: str):
    """
    Avvia due task concorrenti:
    - Reinvio batch già pronti: ogni 60 secondi.
    - Recupero batch incompleti: ogni 300 secondi.
    """
    task1 = asyncio.create_task(reinvia_batch_gia_pronti(db, endpoint_cloud, intervallo=60))
    task2 = asyncio.create_task(recupera_batch_incompleti(db, endpoint_cloud, intervallo=300))
    try:
        await asyncio.gather(task1, task2)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")
