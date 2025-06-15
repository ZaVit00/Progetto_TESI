import asyncio
import json
import logging

from database.gestore_db import GestoreDatabase
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completo, invia_payload
#from database import gestore_db
logger = logging.getLogger(__name__)

async def invia_payload_batch_pronti(db : GestoreDatabase, endpoint_cloud: str, intervallo: int = 60):
    """
    Task periodico: rinvia i payload JSON dei batch pronti per l'invio al cloud provider
    Default: ogni 60 secondi.
    """
    await asyncio.sleep(10)  # primo check rapido
    while True:
        logger.info("Controllo batch già pronti per invio...")
        batch_payload_list = db.ottieni_payload_batch_non_inviati()
        for p in batch_payload_list:
            try:
                # creazione del dizionario da inviare
                #nel database memorizziamo stringhe e non dizionari
                payload_dict = json.loads(p)
                #id del batch estratto
                id_batch = payload_dict["batch"]["id_batch"]
                if invia_payload(payload_dict, endpoint_cloud):
                    logger.debug(f"Batch {id_batch} inviato correttamente.")
                else:
                    logger.warning(f"Reinvio fallito per batch {id_batch}.")
                    break  # interrompe il ciclo se il cloud è down
            except Exception as e:
                logger.error(f"Errore durante la conversione/invio di un batch: {e}")
        await asyncio.sleep(intervallo)


async def elabora_batch_completi_non_elaborati(db : GestoreDatabase, intervallo: int = 30):
    """
       Task periodico: cerca batch completati ma ancora non elaborati (cioè senza payload_json).
       Per ognuno invoca gestisci_batch_completato().
       """
    while True:
        logger.info("Controllo batch completati da elaborare...")
        try:
            # Estrae i batch completi che necessitano di elaborazione
            risultati = db.ottieni_id_batch_completi()
            lista_id = [r["id_batch"] for r in risultati]
            for id_batch in lista_id:
                try:
                    logger.info(f"Elaborazione batch completato ID {id_batch}")
                    gestisci_batch_completo(id_batch=id_batch, db=db, endpoint_cloud=endpoint_cloud)
                except Exception as e:
                    logger.error(f"Errore nell'elaborazione del batch {id_batch}: {e}")
        except Exception as e:
            logger.error(f"Errore durante la ricerca dei batch da elaborare: {e}")
        await asyncio.sleep(intervallo)  # puoi regolarlo a piacere


async def invio_periodico(db, endpoint_cloud: str):
    """
    Avvia task:
    - Reinvio batch già pronti: ogni 60 secondi.
    - Ricerca ed Elaborazione batch completati: ogni 30 secondi
    """
    task1 = asyncio.create_task(invia_payload_batch_pronti(db, endpoint_cloud, intervallo=60))
    task2 = asyncio.create_task(elabora_batch_completi_non_elaborati(db, intervallo=30))
    try:
        await asyncio.gather(task1)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")
