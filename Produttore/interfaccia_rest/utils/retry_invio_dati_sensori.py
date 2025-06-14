import asyncio
import logging
from typing import Any

from database.gestore_db import GestoreDatabase
from fog_api_utils import invia_payload
logger = logging.getLogger(__name__)

async def invia_sensori_non_confermati(db: GestoreDatabase, endpoint_cloud: str, intervallo: int = 60):
    """
    Task periodico che tenta di rinviare/inviare al cloud i sensori registrati localmente
    ma che non hanno ancora ricevuto conferma di registrazione esplicita dal cloud
    :param db: Istanza del gestore DB locale.
    :param endpoint_cloud: URL dell'endpoint REST del cloud.
    :param intervallo: Tempo in secondi tra un tentativo e l'altro (default: 60).
    """
    await asyncio.sleep(10)  # breve attesa iniziale
    while True:
        logger.info("Controllo sensori non confermati...")
        lista_sensori = db.estrai_sensori_non_confermati()
        for sensore in lista_sensori:
            id_sensore = sensore["id_sensore"]
            try:
                logger.debug(f"Tentativo invio sensore {id_sensore}...")
                if invia_payload(sensore, endpoint_cloud):
                    logger.info(f"Sensore {id_sensore} inviato correttamente.")
                else:
                    logger.warning(f"Invio fallito per sensore {id_sensore}.")
                    break  # se il cloud è down, interrompe il ciclo
            except Exception as e:
                logger.error(f"Errore durante l'invio del sensore {id_sensore}: {e}")
        await asyncio.sleep(intervallo)

async def invio_periodico(db, endpoint_cloud: str):
    """
    Avvia il task di invio dati del sensore
    """
    task1 = asyncio.create_task(invia_sensori_non_confermati(db, endpoint_cloud, intervallo=20))
    try:
        await asyncio.gather(task1)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")