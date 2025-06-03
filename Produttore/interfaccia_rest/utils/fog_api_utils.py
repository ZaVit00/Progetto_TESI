from fastapi import requests

from database.gestore_db import GestoreDatabase
from utils.hash_utils import calcola_hash
from merkle_tree import MerkleTree
import json

"""
Funzione che gestisce tutte le operazioni da effettuare quando
un batch diventa disponibile per la creazione del merkle tree
e successivo invio al cloud provider storage
"""
import json

def gestisci_batch_completato(id_batch_chiuso: int, db: GestoreDatabase, endpoint_cloud: str):
    try:
        # 1. Estrai tutte le misurazioni con dati di batch
        dati_batch = db.estrai_dati_batch(id_batch_chiuso)
        if not dati_batch:
            print(f"[ERRORE] Nessun dato trovato per il batch {id_batch_chiuso}")
            return

        # 2. Calcola gli hash completi per ciascun record di dati
        try:
            lista_hash = [genera_hash_misurazione_completa(r) for r in dati_batch]
        except Exception as e:
            print(f"[ERRORE] Calcolo degli hash fallito: {e}")
            return

        # 3. Costruisci il Merkle Tree
        try:
            merkle_tree = MerkleTree(lista_hash)
            merkle_root = merkle_tree.merkle_tree_binario()
        except Exception as e:
            print(f"[ERRORE] Errore nella costruzione del Merkle Tree: {e}")
            return

        # 4. Salva la Merkle Root nel DB
        try:
            db.aggiorna_merkle_root_batch(id_batch_chiuso, merkle_root)
        except Exception as e:
            print(f"[ERRORE] Fallita l'aggiornamento della Merkle Root nel database: {e}")
            return

        # 5. Costruisci il payload JSON da inviare
        try:
            payload = {
                "batch": {
                    "id_batch": dati_batch[0]["id_batch"],
                    "timestamp_creazione": dati_batch[0]["timestamp_creazione"],
                    "numero_misurazioni": dati_batch[0]["numero_misurazioni"],
                    "merkle_root": merkle_root
                },
                "misurazioni": []
            }
            for riga in dati_batch:
                try:
                    payload["misurazioni"].append({
                        "id_misurazione": riga["id_misurazione"],
                        "id_sensore": riga["id_sensore"],
                        "timestamp": riga["timestamp"],
                        "dati": json.loads(riga["dati"])
                    })
                except json.JSONDecodeError as e:
                    print(f"[ERRORE] Decodifica JSON fallita per la misurazione {riga.get('id_misurazione', '?')}: {e}")
                    continue

        except KeyError as e:
            #questa casistica gestisce errori sulle chiavi del dizionario
            print(f"[ERRORE] Chiave mancante durante la costruzione del JSON: {e}")
            return
        except Exception as e:
            print(f"[ERRORE] Errore inatteso nella costruzione del JSON: {e}")
            return

        # 6. Mostra il JSON finale
        print("[DEBUG] Payload JSON da inviare:")
        print(json.dumps(payload, indent=2))

        # 6. Invia il JSON al cloud
        if invia_payload(payload, endpoint_cloud):
            try:
                db.elimina_misurazioni_batch(id_batch_chiuso)
                print(f"[INFO] Misurazioni del batch {id_batch_chiuso} eliminate dal database locale.")
            except Exception as e:
                print(f"[ERRORE] Impossibile eliminare le misurazioni del batch {id_batch_chiuso}: {e}")
        else:
            print(f"[AVVISO] Il batch {id_batch_chiuso} non è stato eliminato perché l'invio è fallito.")
    except Exception as e:
        print(f"[ERRORE GENERALE] Errore imprevisto nella gestione del batch {id_batch_chiuso}: {e}")

"""
Ogni foglia nel Merkle Tree rappresenta una misurazione + info del batch
Qualunque manomissione sul batch renderà la root diversa, così
come anche qualunque manomissione sulle informazioni della misurazione
json.dumps(...) → converte un oggetto Python (dict) in una stringa JSON
json.loads(...) → fa il contrario: prende una stringa JSON e la trasforma in un dict Python
Funzione	    Cosa fa
json.dumps()	da dict Python → str JSON
json.loads()	da str JSON → dict Python
"""
def genera_hash_misurazione_completa(risultato_query: dict) -> str:
    """
    Calcola l'hash SHA-256 completo di una misurazione e dei suoi metadati di batch.
    Protegge sia i dati raccolti che le informazioni sul batch di appartenenza.
    Utilizzo il JSON perché fornisce una rappresentazione testuale stabile e serializzata.
    """

    #la struttura forma un singolo record di dati che dovrà essere inviato
    #al cloud provider storage per la memorizzazione
    struttura = {
        "id_misurazione": risultato_query["id_misurazione"],
        "id_sensore": risultato_query["id_sensore"],
        "timestamp": risultato_query["timestamp"],
        "dati": json.loads(risultato_query["dati"]),
        "batch": {
            "id_batch": risultato_query["id_batch"],
            "timestamp_creazione": risultato_query["timestamp_creazione"],
            "numero_misurazioni": risultato_query["numero_misurazioni"]
        }
    }
    #compatto la struttura
    json_string = json.dumps(struttura, separators=(",", ":"))
    #calcolo l'hash dell'intera stringa JSON
    hashed_json_string = calcola_hash(json_string)
    return hashed_json_string

def invia_payload(payload: dict, endpoint_cloud: str) -> bool:
    """
    Invia il batch al servizio cloud.
    Args:
    payload (dict): Il dizionario JSON da inviare.
    Endpoint_cloud_url (str): L'URL dell'endpoint remoto.
    Returns:
    bool: True se l'invio ha avuto successo, False altrimenti.
    """
    try:
        response = requests.post(endpoint_cloud, json=payload)
        response.raise_for_status()
        print("[INFO] Batch e Misurazioni inviate correttamente al cloud.")
        return True
    except requests.RequestException as e:
        print(f"[ERRORE] Errore durante l'invio del batch al cloud: {e}")
        return False