import json
from typing import List, Dict

from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.entita.modelli_dati import DatiBatch, PacchettoBatchMisurazioni, DatiMisurazione
from Classi_comuni.utils import Hashing
from modelli_dati import DatiSensore
from modelli_metadati import MetaDatiSensore, MetaDatiMisurazione


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
        self.hash_misurazioni_sensori: Dict[int, str] = {}  # id_misurazione → hash concatenato
        self.hash_batch: str | None = None

    def estrai_dati_da_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae gli oggetti Pydantic da una lista di righe SQL (INNER JOIN tra batch, misurazioni e sensori).
        Assume che tutte le righe appartengano allo stesso batch.
        Calcola:
        - hash per ogni misurazione e sensore (concatenati)
        - hash del batch (una sola volta)
        """
        if not risultati_query:
            raise ValueError("La query non ha restituito risultati. Verifica gli ID passati.")

        # Pulizia delle strutture dati interne prima della nuova estrazione
        self.misurazioni.clear()
        self.hash_misurazioni_sensori.clear()
        self.sensori.clear()

        # Ordina esplicitamente i risultati per ID misurazione (necessario per garantire ordine deterministico negli hash)
        risultati_ordinati = sorted(risultati_query, key=lambda r: r["id_misurazione"])

        # Estrazione del batch dalla prima riga (tutte le righe condividono gli stessi metadati di batch)
        prima_riga = risultati_ordinati[0]
        self.batch = CostruttorePayload.costruisci_dati_batch_da_query(prima_riga)

        # Calcolo dell'hash del batch una sola volta (sarà la prima foglia del Merkle Tree)
        self.hash_batch = self.batch.to_hash()

        # Estrazione oggetti misurazione + sensore da ogni riga della query e calcolo degli hash
        for riga in risultati_ordinati:
            dati_misurazione = CostruttorePayload.costruisci_dati_misurazione_da_query(riga)
            dati_sensore = CostruttorePayload.costruisci_dati_sensore_da_query(riga)

            self.misurazioni.append(dati_misurazione)
            self.sensori.append(dati_sensore)

            hash_concat = Hashing.hash_concat(
                dati_sensore.to_hash(),
                dati_misurazione.to_hash()
            )
            #chiave id_misurazione -> hash
            self.hash_misurazioni_sensori[dati_misurazione.id_misurazione] = hash_concat

    def costruisci_payload(self) -> PacchettoBatchMisurazioni:
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

        return PacchettoBatchMisurazioni(
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

        mappa_id_hash = {ID_BATCH_LOGICO: self.hash_batch}
        mappa_id_hash.update(self.hash_misurazioni_sensori)
        # Ordinamento finale del dizionario per chiave (ID)
        return dict(sorted(mappa_id_hash.items()))

    @staticmethod
    def costruisci_dati_misurazione_da_query(riga: dict) -> DatiMisurazione:
        """
        Costruisce un oggetto DatiMisurazione da una riga SQL.
        Esegue anche il parsing del campo 'dati' se è una stringa JSON.
        """
        if isinstance(riga["dati"], str):
            try:
                riga["dati"] = json.loads(riga["dati"])
            except json.JSONDecodeError as e:
                raise ValueError(f"[ERRORE JSON] Errore nel parsing del campo 'dati': {e}")

        return DatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            id_sensore=riga["id_sensore"],
            timestamp=riga["timestamp"],
            dati=riga["dati"]
        )

    @staticmethod
    def costruisci_dati_sensore_da_query(riga: dict) -> DatiSensore:
        """
        Costruisce un oggetto DatiSensore da una riga SQL.
        """
        return DatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"],
            descrizione=riga["descrizione"]
        )

    @staticmethod
    def costruisci_dati_batch_da_query(riga: dict) -> DatiBatch:
        """
        Costruisce un oggetto DatiBatch dalla prima riga della query.
        """
        return DatiBatch(
            id_batch=riga["id_batch"],
            timestamp_creazione=riga["timestamp_creazione"],
            numero_misurazioni=riga["numero_misurazioni"]
        )

    @staticmethod
    def costruisci_metadati_misurazione_da_query(riga: dict) -> MetaDatiMisurazione:
        """
        Costruisce un oggetto MetaDatiMisurazione da una riga SQL.
        """
        return MetaDatiMisurazione(
            id_misurazione=riga["id_misurazione"],
            id_batch=riga["id_batch"],
            timestamp=riga["timestamp"]
        )

    @staticmethod
    def costruisci_metadati_sensore_da_query(riga: dict) -> MetaDatiSensore:
        """
        Costruisce un oggetto MetaDatiSensore da una riga SQL.
        """
        return MetaDatiSensore(
            id_sensore=riga["id_sensore"],
            tipo=riga["tipo"]
        )
