from typing import List, Dict
import json
from Classi_comuni.entita.modelli_dati import DatiBatch, DatiPayload, DatiMisurazione
from Classi_comuni.entita.costanti_comuni import  ID_BATCH_LOGICO
import logging

logger = logging.getLogger(__name__)

class CostruttorePayload:
    """
    Classe che prepara i dati per la costruzione del Merkle Tree e del payload.
    Primo momento (intermedio): estrae gli oggetti da una query INNER JOIN e calcola:
      - hash di ogni singola misurazione
      - hash del batch (separatamente)

    Secondo momento: costruisce il DatiPayload da inviare al cloud, includendo la Merkle Root.
    """
    def __init__(self) -> None:
        self.misurazioni: List[DatiMisurazione] = []
        self.batch: DatiBatch | None = None
        self.hash_misurazioni: List[str] = []
        self.hash_batch: str | None = None

    def estrai_dati_da_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae gli oggetti Pydantic dalle righe SQL e calcola:
        - hash per ogni misurazione
        - hash del batch (una sola volta)
        """
        self.misurazioni.clear()
        self.hash_misurazioni.clear()
        #Ordina esplicitamente i risultati per id_misurazione
        #Ordina usando il valore del campo id_misurazione come chiave di confronto".
        risultati_ordinati = sorted(risultati_query, key=lambda r: r["id_misurazione"])
        # Batch viene preso dalla prima riga (già ordinata)
        prima_riga = risultati_ordinati[0]
        self.batch = DatiBatch(
            id_batch=prima_riga["id_batch"],
            timestamp_creazione=prima_riga["timestamp_creazione"],
            numero_misurazioni=prima_riga["numero_misurazioni"],
            #merkle_root=""
        )
        self.hash_batch = self.batch.to_hash()

        for riga in risultati_ordinati:
            try:
                if isinstance(riga["dati"], str):
                    riga["dati"] = json.loads(riga["dati"])

                mis = DatiMisurazione(
                    id_misurazione=riga["id_misurazione"],
                    id_sensore=riga["id_sensore"],
                    timestamp=riga["timestamp"],
                    dati=riga["dati"]
                )
                self.misurazioni.append(mis)
                self.hash_misurazioni.append(mis.to_hash())

            except Exception as e:
                logger.error(f"[ERRORE] Errore durante la creazione della misurazione: {e}")

    def get_foglie_hash(self) -> List[str]:
        """
        Restituisce la lista degli hash da usare come foglie nel Merkle Tree:
        - N hash delle misurazioni
        - 1 hash del batch (come ultima foglia)
        """
        if not self.hash_batch:
            raise ValueError("Hash del batch non calcolato. Chiama prima estrai_dati_query.")
        if not self.hash_misurazioni:
            raise ValueError("Hash delle misurazioni non calcolate. Chiama prima estrai_dati_query.")
        # concatenazione delle liste di hash
        # La prima foglia è hash del batch; le restanti sono delle misurazioni
        return [self.hash_batch] + self.hash_misurazioni

    def costruisci_payload(self) -> DatiPayload:
        """
        Costruisce il payload da inviare al cloud.
        La Merkle Root può essere inserita nel batch per scopi di debug
        I Merkle Path NON sono inclusi (vanno su IPFS separatamente).
        """
        if self.batch is None:
            raise ValueError("Batch non inizializzato. Chiama prima 'estrai_dati_query'.")

        # self.misurazioni è una lista e questo controllo equivale a verificare se la
        # lista è vuota
        if not self.misurazioni:
            raise ValueError("Nessuna misurazione trovata. Il payload sarebbe vuoto.")

        # Crea un nuovo oggetto DatiBatch con Merkle Root. Possibile solo per classi PYDANTIC
        # DATIBATCH è una classe PYDANTIC
        #batch_con_root = self.batch.model_copy(update={"merkle_root": merkle_root})
        return DatiPayload(
            batch=self.batch,
            misurazioni=list(self.misurazioni)  # copia esplicita
        )

    def get_id_misurazioni(self) -> List[int]:
        # restituisce la lista degli id della misurazione concatenato con la lista contenente
        # IL PRIMO id FITTIZIO rappresentativo del batch = 0 (nessuna misurazione avrà mai id misurazione = 0
        # essendo il campo id_misurazione con autoincrement partirà da 1
        # Metodo necessario per la creazione dei merkle paths
        if not self.misurazioni:
            raise ValueError("Errore! Nessun id misurazione in elaborazione")
        return [ID_BATCH_LOGICO] + [mis.id_misurazione for mis in self.misurazioni]
