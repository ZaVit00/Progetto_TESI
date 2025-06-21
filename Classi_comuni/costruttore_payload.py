import json
import logging
from typing import List, Dict
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.entita.modelli_dati import DatiBatch, DatiPayload, DatiMisurazione

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
            except Exception as e:
                logger.error(f"[ERRORE] Errore durante la creazione della misurazione: {e}")
        # Alla fine di estrai_dati_da_query
        self.misurazioni.sort(key=lambda m: m.id_misurazione)
        self.hash_misurazioni = [m.to_hash() for m in self.misurazioni]

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

    def ottieni_mappa_id_foglie(self) -> dict[int, str]:
        """
        Costruisce una mappa id --> hash (foglie) a partire da DatiBatch e datiMisurazione.
        Restituisce un dizionario che mappa ogni ID logico al suo hash:
        - ID 0 per il batch
        - ID della misurazione per ogni misurazione
        """
        if not self.hash_batch:
            raise ValueError("Hash del batch non calcolato. Chiama prima estrai_dati_query.")
        if not self.hash_misurazioni:
            raise ValueError("Hash delle misurazioni non calcolate. Chiama prima estrai_dati_query.")
        mappa_id_hash = {ID_BATCH_LOGICO: self.batch.to_hash()}
        for mis in self.misurazioni:
            # 2047 --> ababhuduhjcdbjkcbkdshdcwi
            mappa_id_hash[mis.id_misurazione] = mis.to_hash()

        # Ordinamento finale del dizionario per chiave (ID)
        return dict(sorted(mappa_id_hash.items()))
