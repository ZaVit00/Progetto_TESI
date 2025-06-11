import requests
from database.gestore_db import GestoreDatabase
from merkle_tree import MerkleTree

from costruttore_payload import CostruttorePayload  # Assicurati che sia importata

def gestisci_batch_completato(id_batch_chiuso: int, db: GestoreDatabase, endpoint_cloud: str) -> None:
    """
    Gestisce l'intero ciclo di elaborazione di un batch completo:
    1. Estrae le misurazioni associate dal DB.
    2. Costruisce il payload.
    3. Calcola la Merkle Root.
    4. Aggiorna la root nel DB.
    5. Salva il payload come JSON nel DB per debug o reinvio futuro.
    6. Converte il payload in dizionario e lo invia al cloud.
    """

    try:
        # 1. Estrai i dati (batch + misurazioni) dal DB
        dati_query = db.estrai_dati_batch_misurazioni(id_batch_chiuso)
        if not dati_query:
            #verifica se la lista contiene almeno un elemento
            print(f"[ERRORE] Nessun dato trovato per il batch {id_batch_chiuso}")
            return

        # 2. Costruzione oggetto intermedio (modello Pydantic)
        payload_intermedio = CostruttorePayload()
        payload_intermedio.estrai_dati_da_query(dati_query)

        # 3. Calcolo Merkle Root sulle tuple hashate (batch + misurazione)
        try:
            foglie_hash = payload_intermedio.get_foglie_hash()
            merkle_tree = MerkleTree(foglie_hash)
            # Mappa_id serve per costruire i Merkle Path
            mappa_id = payload_intermedio.get_id_misurazioni()
            merkle_root = merkle_tree.costruisci_albero(mappa_id=mappa_id, verbose=True)
        except Exception as e:
            print(f"[ERRORE] Creazione Merkle Tree fallita: {e}")
            return

        # 4. Aggiorna la Merkle Root nel record del batch
        try:
            db.aggiorna_merkle_root_batch(id_batch_chiuso, merkle_root)
        except Exception as e:
            print(f"[ERRORE] Aggiornamento Merkle Root nel DB fallito: {e}")
            return

        # 5. Costruzione del payload finale da inviare
        try:
            # oggetto Pydantic (DatiBatch e Lista di DatiMisurazioni)
            payload_finale = payload_intermedio.costruisci_payload(merkle_root)
            # SERIALIZZAZIONE: da oggetto Pydantic → stringa JSON
            # utilizzare il metodo model_dump_json SOLO per oggetti Pydantic
            #payload_json è una stringa JSON
            payload_json = payload_finale.model_dump_json(indent=2)
            # Salvataggio del JSON nel DB per tracciabilità/debug/reinvio di pacchetti
            db.aggiorna_payload_json_batch(id_batch_chiuso, payload_json)

            # Debug: stampa il JSON costruito
            print("[INFO] Payload JSON costruito:")
            print("-------------------")
            print(payload_json)
            print("-------------------")

        except Exception as e:
            print(f"[ERRORE] Costruzione del payload fallita: {e}")
            return

        try:
            # 6. INVIO: da oggetto Pydantic → dizionario Python → POST HTTP
            # Metodo model_dump solo per ottenere dizionari da oggetti Pydantic
            # la conversione è automatica e fatta da Pydantic con il metodo model_dump
            payload_dict = payload_finale.model_dump()  # dict per il client HTTP
            if invia_payload(payload_dict, endpoint_cloud):
                print(f"[INFO] Batch {id_batch_chiuso} inviato con successo. In attesa conferma ricezione.")
            else:
                print(f"[AVVISO] Invio del batch {id_batch_chiuso} fallito. I dati resteranno locali.")
        except Exception as e:
            print(f"[ERRORE] Invio del batch {id_batch_chiuso} fallito: {e}")

    except Exception as e:
        print(f"[ERRORE GENERALE] Errore durante l'elaborazione del batch {id_batch_chiuso}: {e}")



def invia_payload(payload_dict: dict, endpoint_cloud: str) -> bool:
    """
    Invia il payload (già convertito in dizionario) al servizio cloud tramite HTTP POST.
    Ritorna True se la richiesta ha esito positivo (status code 2xx), altrimenti False.
    """
    try:
        response = requests.post(endpoint_cloud, json=payload_dict)
        response.raise_for_status()
        print("[INFO] Invio del payload al cloud riuscito.")
        return True
    except requests.RequestException as e:
        print(f"[ERRORE] Invio del payload al cloud fallito: {e}")
        return False

