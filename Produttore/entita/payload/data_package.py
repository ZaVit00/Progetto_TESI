import requests
import json
from database.gestore_db import GestoreDatabase
from utils.hash_utils import calcola_hash
from merkle_tree import MerkleTree


class DataPackage:
    """
    Classe che rappresenta un pacchetto dati completo per un batch.
    La struttura interna è basata su una lista di dizionari,
    dove ciascun dizionario rappresenta una misurazione arricchita
    con i metadata del batch a cui appartiene (inner join)
    Questa classe consente:
    - l'applicazione della funzione di hashing su ogni misurazione completa,
      utilizzando una serializzazione stabile tramite JSON;
    - la costruzione del payload finale da inviare al cloud,
      ottimizzando la ridondanza dei dati.
    """
    def __init__(self, risultati_query: list[dict]) -> None:
        #lista di dizionari
        self.misurazioni_completate = []
        self._estrai_misurazioni(risultati_query)

    def _estrai_misurazioni(self, risultati_query: list[dict]) -> None:
        """
        Costruisce la struttura dati interna a partire dai risultati della query SQL.
        Ogni riga della query viene trasformata in un dizionario contenente:
        - i campi relativi alla misurazione (id, sensore, timestamp, dati);
        - un sotto-dizionario 'batch' con i metadati comuni del batch.
        Questa rappresentazione consente successivamente il calcolo dell'hash
        e la generazione del payload in modo efficiente e modulare.
        """
        for riga in risultati_query:
            try:
                misurazione_dict = {
                    "id_misurazione": riga["id_misurazione"],
                    "id_sensore": riga["id_sensore"],
                    "timestamp": riga["timestamp"],
                    # converto i dati sotto forma di JSON in dizionario
                    "dati": json.loads(riga["dati"]),
                    "batch": {
                        "id_batch": riga["id_batch"],
                        "timestamp_creazione": riga["timestamp_creazione"],
                        "numero_misurazioni": riga["numero_misurazioni"]
                    }
                }
                #aggiunta del dizionario alla lista
                self.misurazioni_completate.append(misurazione_dict)
            except json.JSONDecodeError as e:
                print(f"[ERRORE] Decodifica JSON fallita per {riga.get('id_misurazione', '?')}: {e}")

    def get_hashes(self) -> list[str]:
        """
        Calcola una lista di hash SHA-256 per ciascuna misurazione del batch.
        Ogni misurazione, comprensiva del sotto-dizionario 'batch', viene serializzata
        con JSON (senza spazi extra) per garantire una rappresentazione stabile e coerente.
        Gli hash generati sono poi utilizzati come foglie del Merkle Tree.
        """
        hash_list = []
        #ciascun elemento di misurazioni_completate è un dizionario
        #m è un dizionario
        for m in self.misurazioni_completate:
            #a partire dal dizionario creo il JSON
            json_string = json.dumps(m, separators=(",", ":"))
            hash_list.append(calcola_hash(json_string))
        return hash_list

    def costruisci_payload(self, merkle_root: str) -> dict:
        """
        Costruisce il payload JSON da inviare al cloud, includendo:
        - una sezione 'batch' con i metadati e la Merkle Root appena calcolata;
        - una lista 'misurazioni', dove ogni elemento è una misurazione priva
          del sotto-dizionario 'batch' per evitare ridondanza.
        La struttura è conforme al formato atteso dal cloud provider.
        """
        #estrare la parte relativa al batch dal dizionario
        dati_batch = self.misurazioni_completate[0]["batch"]
        # Estrai i metadati del batch
        batch_metadata = {
            "id_batch": dati_batch["id_batch"],
            "timestamp_creazione": dati_batch["timestamp_creazione"],
            "numero_misurazioni": dati_batch["numero_misurazioni"],
            "merkle_root": merkle_root
        }
        # Crea la lista di Dizionari. Ogni dizionario è un record di misurazione
        # senza includere i metadati del batch
        misurazioni = [
            {
                "id_misurazione": m["id_misurazione"],
                "id_sensore": m["id_sensore"],
                "timestamp": m["timestamp"],
                "dati": m["dati"]
            }
            #creo un dizionario per ogni record di misurazione
            for m in self.misurazioni_completate
        ]
        # Combina tutto nel payload da inviare al cloud
        payload_finale = {
            "batch": batch_metadata,
            "misurazioni": misurazioni
        }
        return payload_finale