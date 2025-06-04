import requests
import json
from payload_pacchetto import DataPackage
from database.gestore_db import GestoreDatabase
from merkle_tree import MerkleTree


def gestisci_batch_completato(id_batch_chiuso: int, db: GestoreDatabase, endpoint_cloud: str) -> None:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae dal database locale le misurazioni associate al batch identificato.
    2. Costruisce una rappresentazione intermedia (BatchDataPackage) per:
       - calcolare gli hash di ciascuna misurazione (inclusi metadati di batch);
       - generare il Merkle Tree e ottenere la Merkle Root;
       - costruire il response strutturato da inviare al cloud.
    3. Aggiorna il database locale con la Merkle Root ottenuta.
    4. Invia il response al cloud provider tramite POST HTTP.
    5. L’eliminazione delle misurazioni locali avverrà solo dopo conferma
       esplcita.
    """
    try:
        dati_batch = db.estrai_dati_batch(id_batch_chiuso)
        if not dati_batch:
            print(f"[ERRORE] Nessun dato trovato per il batch {id_batch_chiuso}")
            return
        pacchetto = DataPackage(dati_batch)
        try:
            merkle_tree = MerkleTree(pacchetto.get_hashes())
            merkle_root = merkle_tree.costruisci_binario()
        except Exception as e:
            print(f"[ERRORE] Creazione Merkle Tree fallita: {e}")
            return

        try:
            #aggiorna il record corrispondente al batch con il merkle root nuovo
            db.aggiorna_merkle_root_batch(id_batch_chiuso, merkle_root)
        except Exception as e:
            print(f"[ERRORE] Aggiornamento Merkle Root nel DB fallito: {e}")
            return

        try:
            #costruisco il response da inviare
            payload = pacchetto.costruisci_payload(merkle_root)
            print("[DEBUG] Payload JSON da inviare:")
            print(json.dumps(payload, indent=2))
        except Exception as e:
            print(f"[ERRORE] Costruzione del response fallita: {e}")
            return

        if invia_payload(payload, endpoint_cloud):
            print(f"[INFO] Batch {id_batch_chiuso} inviato. In attesa conferma ricezione.")
        else:
            print(f"[AVVISO] Invio del batch {id_batch_chiuso} fallito. Dati ancora locali.")

    except Exception as e:
        print(f"[ERRORE GENERALE] Errore batch {id_batch_chiuso}: {e}")


def invia_payload(payload: dict, endpoint_cloud: str) -> bool:
    """
    Invia il response JSON al servizio cloud specificato tramite una richiesta HTTP POST.
    Ritorna True se la richiesta ha esito positivo (status code 2xx), altrimenti False.
    """
    try:
        response = requests.post(endpoint_cloud, json=payload)
        response.raise_for_status()
        print("[INFO] Invio del response al cloud riuscito.")
        return True
    except requests.RequestException as e:
        print(f"[ERRORE] Invio del response al cloud fallito: {e}")
        return False
