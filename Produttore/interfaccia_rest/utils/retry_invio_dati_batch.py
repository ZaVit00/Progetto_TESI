import asyncio
import json
import logging
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato, invia_payload

# Logger locale
logger = logging.getLogger(__name__)

async def invia_batch_pronti(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Task periodico: reinvia i batch già pronti con Merkle Root e payload_json.
    Default: ogni 60 secondi.
    """
    await asyncio.sleep(10)  # primo check rapido
    while True:
        logger.info("Controllo batch già pronti per invio...")
        batch_payload_list = db.ottieni_payload_batch_non_inviati()
        for p in batch_payload_list:
            try:
                payload_dict = json.loads(p)
                id_batch = payload_dict["batch"]["id_batch"]
                if invia_payload(payload_dict, endpoint_cloud):
                    logger.debug(f"Batch {id_batch} inviato correttamente.")
                else:
                    logger.warning(f"Reinvio fallito per batch {id_batch}.")
                    break  # interrompe il ciclo se il cloud è down
            except Exception as e:
                logger.error(f"Errore durante la conversione/invio di un batch: {e}")
        await asyncio.sleep(intervallo)


async def invio_periodico(db, endpoint_cloud: str):
    """
    Avvia task:
    - Reinvio batch già pronti: ogni 60 secondi.
    """
    task1 = asyncio.create_task(invia_batch_pronti(db, endpoint_cloud, intervallo=20))
    try:
        await asyncio.gather(task1)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")
