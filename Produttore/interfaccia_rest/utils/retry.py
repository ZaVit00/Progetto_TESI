import asyncio
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato

async def retry_invio_batch_periodico(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Controlla immediatamente e poi periodicamente se ci sono batch completati ma non ancora inviati,
    tentando di inviarli al cloud.
    """
    #funzione nested visibile solo all'interno della funzione
    async def invia_batch_non_inviati():
        print("[DEBUG] Controllo batch non inviati...")
        # verifica la presenza di batch COMPLETATI ma NON INVIATI e tenta il reinvio
        batch_non_inviati = db.get_batch_non_inviati()
        for batch in batch_non_inviati:
            gestisci_batch_completato(batch["id_batch"], db, endpoint_cloud)

    # Primo invio immediato
    await invia_batch_non_inviati()
    # Esecuzione periodica
    while True:
        await asyncio.sleep(intervallo)
        await invia_batch_non_inviati()
