import json
import logging
from typing import List, Dict
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.entita.modelli_dati import DatiBatch, DatiPayload, DatiMisurazione
from Classi_comuni.hash_utils import Hashing
from modelli_dati import DatiSensore

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
        self.sensori: List[DatiSensore] = []
        self.batch: DatiBatch | None = None
        # === strutture dati contenenti gli hash === #
        self.hash_misurazioni_sensori: List[str] = []
        self.hash_batch: str | None = None
        self.hash_sensori: list[str] = []

    def estrai_dati_da_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae gli oggetti Pydantic dalle righe SQL e calcola:
        - hash per ogni misurazione
        - hash dei dati del sensore (insieme alla misurazione)
        - hash del batch (una sola volta)
        """
        self.misurazioni.clear()
        self.hash_misurazioni_sensori.clear()
        self.sensori.clear()
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

                dati_misurazione = DatiMisurazione(
                    id_misurazione=riga["id_misurazione"],
                    id_sensore=riga["id_sensore"],
                    id_batch=prima_riga["id_batch"],
                    timestamp=riga["timestamp"],
                    dati=riga["dati"]
                )

                dati_sensore = DatiSensore(
                    id_sensore=riga["id_sensore"],
                    tipo=riga["tipo"],
                    descrizione =riga["descrizione"],
                )
                self.misurazioni.append(dati_misurazione)
                self.sensori.append(dati_sensore)
            except Exception as e:
                logger.error(f"[ERRORE] Errore durante la creazione della misurazione: {e}")
        # Alla fine di estrai_dati_da_query rioridino i risultati
        #self.misurazioni.sort(key=lambda m: m.id_misurazione)

        for dati_s, dati_m in zip(self.sensori, self.misurazioni):
            hash_concat : str = Hashing.hash_concat(dati_s.to_hash(), dati_m.to_hash())
            self.hash_misurazioni_sensori.append(hash_concat)

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
        if not self.hash_misurazioni_sensori:
            raise ValueError("Hash delle misurazioni non calcolate. Chiama prima estrai_dati_query.")
        mappa_id_hash = {ID_BATCH_LOGICO: self.batch.to_hash()}
        for mis, hash_mis_sensore in zip(self.misurazioni, self.hash_misurazioni_sensori):
            # 2047 --> ababhuduhjcdbjkcbkdshdcwi
            mappa_id_hash[mis.id_misurazione] = hash_mis_sensore

        # Ordinamento finale del dizionario per chiave (ID)
        return dict(sorted(mappa_id_hash.items()))
