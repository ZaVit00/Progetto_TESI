import requests
import json
from costruttore_payload import CostruttorePayload
from dati_modellati import DatiPayload
from database.gestore_db import GestoreDatabase
from merkle_tree import MerkleTree

from costruttore_payload import CostruttorePayload  # Assicurati che sia importata

def gestisci_batch_completato(id_batch_chiuso: int, db: GestoreDatabase, endpoint_cloud: str) -> None:
    try:
        dati_batch = db.estrai_dati_batch_misurazioni(id_batch_chiuso)
        if not dati_batch:
            print(f"[ERRORE] Nessun dato trovato per il batch {id_batch_chiuso}")
            return

        # 1. Costruzione del pacchetto intermedio
        payload_intermedio = CostruttorePayload()
        payload_intermedio.estrai_dati_query(dati_batch)

        # 2. Calcolo Merkle Root
        try:
            merkle_tree = MerkleTree(payload_intermedio.get_hash_foglie())
            merkle_root = merkle_tree.costruisci_binario()
        except Exception as e:
            print(f"[ERRORE] Creazione Merkle Tree fallita: {e}")
            return

        # 3. Aggiorna la Merkle Root nel DB
        try:
            db.aggiorna_merkle_root_batch(id_batch_chiuso, merkle_root)
        except Exception as e:
            print(f"[ERRORE] Aggiornamento Merkle Root nel DB fallito: {e}")
            return

        # 4. Costruzione del payload da inviare
        try:
            payload_finale = payload_intermedio.costruisci_payload(merkle_root)
            print("[DEBUG] Payload JSON da inviare:")
            print("-------------------\n")
            print(payload_finale.model_dump_json(indent=2))
            print("-------------------\n")
        except Exception as e:
            print(f"[ERRORE] Costruzione del payload fallita: {e}")
            return

        # 5. Invio al cloud
        if invia_payload(payload_finale, endpoint_cloud):
            print(f"[INFO] Batch {id_batch_chiuso} inviato. In attesa conferma ricezione.")
        else:
            print(f"[AVVISO] Invio del batch {id_batch_chiuso} fallito. Dati ancora locali.")

    except Exception as e:
        print(f"[ERRORE GENERALE] Errore batch {id_batch_chiuso}: {e}")

#ATTENZIONE PERCHé DATIPAYLOAD NON é UN DIZIONARIO MA SOLO UNA SEMPLICE CLASSE

def invia_payload(payload: DatiPayload, endpoint_cloud: str) -> bool:
    """
    Invia il response JSON al servizio cloud specificato tramite una richiesta HTTP POST.
    Ritorna True se la richiesta ha esito positivo (status code 2xx), altrimenti False.
    """
    try:
        response = requests.post(endpoint_cloud, json=payload.model_dump())
        response.raise_for_status()
        print("[INFO] Invio del response al cloud riuscito.")
        return True
    except requests.RequestException as e:
        print(f"[ERRORE] Invio del response al cloud fallito: {e}")
        return False
