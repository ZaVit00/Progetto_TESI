import asyncio
import json
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato, invia_payload

async def reinvia_batch_gia_pronti(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Task periodico: reinvia i batch già pronti con Merkle Root e payload_json.
    Default: ogni 60 secondi.
    """
    await asyncio.sleep(10)  # primo check rapido
    while True:
        print("[DEBUG] Controllo batch già pronti per invio...")
        batch_json_list = db.get_payload_batch_non_inviati()
        for p in batch_json_list:
            try:
                payload_dict = json.loads(p)
                id_batch = payload_dict["batch"]["id_batch"]
                if invia_payload(payload_dict, endpoint_cloud):
                    print(f"[INFO] Batch {id_batch} reinviato correttamente.")
                else:
                    print(f"[AVVISO] Reinvio fallito per batch {id_batch}.")
                    break  # interrompe il ciclo se il cloud è giù
            except Exception as e:
                print(f"[ERRORE] Errore durante la conversione/invio di un batch: {e}")
        await asyncio.sleep(intervallo)

async def recupera_batch_incompleti(db, endpoint_cloud: str, intervallo: int = 300):
    """
    Task periodico: tenta di recuperare i batch incompleti.
    Default: ogni 5 minuti (300 secondi).
    """
    await asyncio.sleep(20)  # delay iniziale diverso
    while True:
        print("[DEBUG] Controllo batch incompleti (manca Merkle Root o Payload)...")
        id_batch_list = db.estrai_batch_incompleti()
        #print(f" [DEBUG] {id_batch_list}")
        for id_batch in id_batch_list:
            try:
                print(f"[INFO] Tentativo di rielaborazione batch ID {id_batch}...")
                gestisci_batch_completato(id_batch, db, endpoint_cloud)
            except Exception as e:
                print(f"[ERRORE] Errore durante la rielaborazione del batch {id_batch}: {e}")
        await asyncio.sleep(intervallo)

async def retry_invio_batch_periodico(db, endpoint_cloud: str):
    """
    Avvia due task concorrenti:
    - Reinvio batch già pronti: ogni 60 secondi.
    - Recupero batch incompleti: ogni 300 secondi.
    """
    task1 = asyncio.create_task(reinvia_batch_gia_pronti(db, endpoint_cloud, intervallo=60))
    task2 = asyncio.create_task(recupera_batch_incompleti(db, endpoint_cloud, intervallo=300))
    await asyncio.gather(task1, task2)
