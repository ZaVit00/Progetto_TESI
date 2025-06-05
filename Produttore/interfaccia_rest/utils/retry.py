import asyncio
import json
from interfaccia_rest.utils.fog_api_utils import gestisci_batch_completato, invia_payload


async def retry_invio_batch_periodico(db, endpoint_cloud: str, intervallo: int = 60):
    """
    Controlla immediatamente e poi periodicamente se ci sono batch completati ma non ancora inviati,
    tentando di inviarli al cloud.
    """
    #funzione nested visibile solo all'interno della funzione
    async def reinvia():
        print("[DEBUG] Controllo batch non inviati già pronti (con Merkle Root e payload JSON)...")
        #estraggo i payload JSON già pronti per l'invio al cloud server
        # attenzione: i payload sono stringhe che però devono essere
        # convertite in dizionari se vogliamo manipolarli
        batch_json_list = db.get_payload_batch_non_inviati()
        for p in batch_json_list:
            # p è una stringa JSON
            # JSON --> DICT
            payload_dict = json.loads(p)  # dizionario
            id_batch = payload_dict["batch"]["id_batch"]

            if invia_payload(payload_dict, endpoint_cloud):
                print(f"[INFO] Batch {id_batch} reinviato correttamente. In attesa conferma ricezione.")
            else:
                print(f"[AVVISO] Reinvio fallito per batch {id_batch}. Verrà ritentato più tardi.")

    #attendi 10 secondi e cerca i batch non inviati
    await asyncio.sleep(10)
    await reinvia()
    # Esecuzione periodica
    while True:
        await asyncio.sleep(intervallo)
        await reinvia()
