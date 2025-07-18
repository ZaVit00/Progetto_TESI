import json
from typing import List, Dict
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.entita.modelli_dati import DatiBatch, PacchettoBatchMisurazioni, DatiMisurazione
from Classi_comuni.utils.hashing_utils import Hashing
from estrattore_dati_query import EstrattoreDatiQuery
from modelli_dati import DatiSensore
from modelli_metadati import MetaDatiSensore, MetaDatiMisurazione

class CostruttorePayload:

    def __init__(self) -> None:
        # === strutture dati di supporto === #

        self.misurazioni: List[DatiMisurazione] = []
        self.batch: DatiBatch | None = None

        # === strutture dati contenenti gli hash === #
        self.hash_misurazioni_sensori: Dict[int, str] = {}  # id_misurazione → hash concatenato
        self.hash_batch: str | None = None

    def estrai_dati_da_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae dati da query SQL e popola le strutture interne.
        La logica è delegata a EstrattoreDatiQuery.
        """
        if not risultati_query:
            raise ValueError("La query non ha restituito risultati. Verifica gli ID passati.")

        # delego l'estrazione al modulo EstrattoreQuery
        (self.batch,
         self.misurazioni,
         self.hash_misurazioni_sensori,
         self.hash_batch) = EstrattoreDatiQuery.estrai_dati_da_query(risultati_query)

    def costruisci_payload(self) -> PacchettoBatchMisurazioni:
        """
        Costruisce il payload da inviare al cloud. il payload, ovvero l'entità PacchettoBatchMisurazioni
         è composto da una istanza di batch (una tupla presa dal db) e N istanze di DatiMisurazione
         (N tuple prese dal db formate da sensore inner join misurazione su chiave id_sensore) dove n è la soglia dinamica che può variare più volte durante
         l'esecuzione. Alcuni dettagli sul pacchetto
        - I Merkle Path NON sono inclusi (vanno su IPFS separatamente).
        - La merkle root non è inclusa (va solo su blockchain)
        """
        if self.batch is None:
            raise ValueError("Batch non inizializzato. Chiama prima 'estrai_dati_query'.")

        # Verifica se la lista è vuota
        if not self.misurazioni:
            raise ValueError("Nessuna misurazione trovata. Il payload sarebbe vuoto.")

        return PacchettoBatchMisurazioni(
            batch=self.batch,
            misurazioni=list(self.misurazioni)  # copia esplicita
        )

    def ottieni_mappa_id_foglie(self) -> dict[int, str]:
        """
        Costruisce una mappa id --> hash (foglie) a partire da DatiBatch e DatiMisurazione.
        Restituisce un dizionario che mappa ogni ID logico al suo hash:
        - ID 0 per il batch
        - ID della misurazione per ogni misurazione

        ATTENZIONE: questo metodo lavora internamente su oggetti che hanno subito una fase di
        ordinamento sui campi. Se così non fosse, non potremmo utilizzare
        """
        if not self.hash_batch:
            raise ValueError("Hash del batch non calcolato. Chiama prima estrai_dati_query.")
        if not self.hash_misurazioni_sensori:
            raise ValueError("Hash delle misurazioni non calcolate. Chiama prima estrai_dati_query.")

        mappa_id_hash = {ID_BATCH_LOGICO: self.hash_batch}
        mappa_id_hash.update(self.hash_misurazioni_sensori)

        # Ordinamento finale del dizionario per chiave (ID)
        return dict(sorted(mappa_id_hash.items()))