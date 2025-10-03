import asyncio
import json
import logging
from config.costanti_produttore import ENDPOINT_CLOUD_SENSORI, ENDPOINT_CLOUD_BATCH
from costanti_comuni import TipoServizio
from elaborazione_batch import elabora_batch_completo
from istanza_globale_db import  gestore_db
from modelli_dati import DatiListaSensoriPayload
from registro_log import setup_logger
from utils.api_cloud import invia_payload

logger = setup_logger(TipoServizio.PRODUTTORE, module = __name__,  level=logging.DEBUG)

# === TASK PERIODICO: INVIO SENSORI NON ANCORA CONFERMATI DA CLOUD ===
async def task_invio_sensori(intervallo: int = 60):
    # Breve pausa iniziale per evitare conflitti all'avvio
    await asyncio.sleep(5)

    while True:
        logger.info("[SENSORI] Controllo sensori da inviare...")
        # Ottiene dal DB la lista dei sensori che non hanno ancora ricevuto conferma dal cloud
        lista_sensori: DatiListaSensoriPayload = gestore_db.ottieni_sensori_non_conferma_ricezione()

        if not lista_sensori.sensori:
            logger.info("[TASK-INVIO-SENSORI] Nessun sensore da inviare al cloud.")
        else:
            try:
                logger.debug(f"[TASK-INVIO-SENSORI] Tentativo invio gruppo sensori ({len(lista_sensori.sensori)} sensori)...")

                # Serializza il modello Pydantic in dizionario python
                payload_dict : dict = lista_sensori.model_dump()
                # Invia il payload dei sensori al cloud
                esito_invio = invia_payload(payload_dict, ENDPOINT_CLOUD_SENSORI)

                if esito_invio:
                    logger.info("[TASK-INVIO-SENSORI] Invio gruppo sensori confermato dal cloud.")
                else:
                    logger.warning("[TASK-INVIO-SENSORI] Invio gruppo sensori fallito a causa del cloud.")
            except Exception as e:
                logger.error(f"[TASK-INVIO-SENSORI] Errore durante l'invio del gruppo di sensori: {e}")

        # Attende il prossimo ciclo
        await asyncio.sleep(intervallo)

# === TASK PERIODICO: INVIO DEL PAYLOAD BATCH
async def task_invio_payload_batch(intervallo: int = 60):
    """
    Questo task si occupa di inviare periodicamente al Cloud il payload JSON
    che contiene:
    - la tupla del batch (record della tabella
     `batch` con i metadati:
      id_batch, soglia, numero_misurazioni, timestamp, ecc.)
    - le tuple delle misurazioni associate a quel batch (dalla tabella `misurazioni`).
    Nota: Utilizzato termine batch perché il payload JSON è associato alla tupla batch nel DB
    """
    await asyncio.sleep(5)  # breve delay iniziale

    while True:
        logger.info("[TASK-INVIO-BATCH-JSON] Controllo batch da inviare...")
        # Recupera le tuple batch chiusi e con JSON già pronto (id + payload_json)
        lista_id_payload = gestore_db.ottieni_payload_batch_pronti_per_invio()
        # Set per evitare invii duplicati nello stesso ciclo
        batch_inviati = set()
        for id_batch, payload_json in lista_id_payload:
            if id_batch in batch_inviati:
                continue  # Skip se già processato in questo giro
            try:
                # Parsing JSON se necessario
                if isinstance(payload_json, str):
                    #stringa JSON -> python dict
                    payload : dict = json.loads(payload_json)
                else:
                    payload = payload_json

                logger.debug(f"[TASK-INVIO-BATCH-JSON] Tentativo invio id_batch={id_batch}...")

                # Invia il batch al cloud
                if invia_payload(payload, ENDPOINT_CLOUD_BATCH):
                    logger.info(f"[TASK-INVIO-BATCH-JSON] Inviato correttamente id_batch={id_batch}")
                    batch_inviati.add(id_batch)  # Marca come inviato con successo
                else:
                    logger.warning(f"[TASK-INVIO-BATCH-JSON] Invio fallito per id_batch={id_batch}")
                    break  # Esce dal ciclo se un invio fallisce
            except Exception as e:
                logger.error(f"[TASK-INVIO-BATCH-JSON] Errore invio id_batch={id_batch}: {e}")

        await asyncio.sleep(intervallo)


# === TASK PERIODICO: INIZIO PIPELINE DI ELABORAZIONE DEI BATCH COMPLETI ===
async def task_elabora_batch_completi(intervallo: int = 60):
    """
    Controlla periodicamente se esistono batch chiusi (completi)
    ma non ancora elaborati (manca Merkle Root o JSON), e avvia la pipeline di
    elaborazione per il batch selezionato.
    Nota:
    - Qui con 'batch' intendiamo l'insieme logico di misurazioni che è stato
      chiuso al raggiungimento della soglia.
    - L'elaborazione dovrebbe avvenire su un batch per volta, data la maggiore intensità
      computazionale rispetto all'inserimento delle singole misurazioni.
      Questo è un parametro modificabile dalla query SQL.
    """
    await asyncio.sleep(10)  # ritardo iniziale maggiore per evitare conflitti iniziali

    while True:
        logger.info("[TASK-BATCH-ELAB] Controllo batch completi da elaborare...")
        # Ottiene la lista di ID dei batch che hanno raggiunto la soglia
        # ma che non sono stati ancora elaborati nella pipeline di processo
        lista_id_batch = gestore_db.ottieni_id_batch_completi()
        logger.debug(f"[TASK-BATCH-ELAB] Lista batch chiusi {lista_id_batch}")

        for id_batch in lista_id_batch:
            try:
                logger.debug(f"[TASK-BATCH-ELAB] INIZIO ELABORAZIONE batch {id_batch}...")
                #avvia il processo di elaborazione del batch completo
                if not elabora_batch_completo(id_batch):
                    logger.debug(f"[TASK-BATCH-ELAB] Elaborazione batch {id_batch} FALLITA")
            except Exception as e:
                logger.error(f"[TASK-BATCH-ELAB] Errore durante elaborazione batch {id_batch}: {e}")

        await asyncio.sleep(intervallo)

# === FUNZIONE DI AVVIO DEI TASK PERIODICI ===
async def avvia_task_periodici():
    """
    Avvia in parallelo i 3 task asincroni principali:
    - Invio sensori NON CONFERMATI al cloud (utile in caso di cloud down e persistenza locale)
    - Invio pacchetto batchMisurazioni in formato JSON al cloud
    - Elaborazione batch completi(batch che hanno raggiunto la soglia di misuraziono
      e necessitano di attraversare la pipeline di elaborazione.
    """
    task1 = asyncio.create_task(task_invio_sensori())
    task2 = asyncio.create_task(task_invio_payload_batch())
    task3 = asyncio.create_task(task_elabora_batch_completi())

    try:
        # Resta in attesa che tutti i task vengano completati (in realtà girano all'infinito)
        await asyncio.gather(task1, task2, task3)
    except Exception as e:
        logger.critical(f"Errore critico nella gestione dei task periodici: {e}")
