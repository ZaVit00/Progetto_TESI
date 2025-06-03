import asyncio
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato

async def retry_invio_batch_periodico(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Controlla periodicamente se ci sono batch completati ma non ancora inviati
    e tenta di inviarli nuovamente al cloud.
    """
    while True:
        await asyncio.sleep(intervallo)
        print("[DEBUG] Controllo periodico: cerco batch non inviati...")
        batch_non_inviati = db.get_batch_non_inviati()
        for batch in batch_non_inviati:
            gestisci_batch_completato(batch["id_batch"], db, endpoint_cloud)
