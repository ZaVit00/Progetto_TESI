from typing import List, Dict
from Classi_comuni.config.costanti_comuni import ID_BATCH_LOGICO
from Classi_comuni.entita.modelli_dati import DatiBatch, BatchPayload, DatiMisurazione
from costruttore_modelli_da_query import CostruttoreModelliDaQuery

class CostruttorePayload:

    def __init__(self) -> None:
        # === strutture dati di supporto === #
        self.misurazioni: List[DatiMisurazione] = []
        self.batch: DatiBatch | None = None

        # === strutture dati contenenti gli hash === #
        # id_misurazione → hash tupla misurazione + sensore
        self.hash_misurazioni_sensori: Dict[int, str] = {}
        # hash della tupla del batch
        self.hash_batch: str | None = None

    def estrai_dati_da_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae dati da query SQL e popola le strutture interne.
        La logica è delegata a CostruttoreModelliDaQuery.
        """
        if not risultati_query:
            raise ValueError("La query non ha restituito risultati. Verifica gli ID passati.")

        # delego l'estrazione al modulo EstrattoreQuery
        (self.batch,
         self.misurazioni,
         self.hash_misurazioni_sensori,
         self.hash_batch) = CostruttoreModelliDaQuery.costruisci_modelli_da_query(risultati_query)

    def costruisci_payload(self) -> BatchPayload:
        """
        Costruisce il payload da inviare al cloud. il payload, ovvero l'entità BatchPayload
         è composto da una istanza di batch (una tupla presa dal db) e N istanze di DatiMisurazione
         (N tuple prese dal db formate da sensore inner join misurazione su chiave id_sensore) dove n è la soglia dinamica che può variare più volte durante
         l'esecuzione. Alcuni dettagli sul pacchetto
        - I Merkle Path NON sono inclusi (vanno su IPFS separatamente).
        - La merkle root non è inclusa (va solo su blockchain)
        """
        #Questi due controlli servono per intercettare bug logici nel programma
        if self.batch is None:
            raise ValueError("Batch non inizializzato. Chiama prima costruisci_modelli_da_query")

        # Verifica se la lista delle misurazioni è vuota
        if not self.misurazioni:
            raise ValueError("Nessuna misurazione trovata. Chiama prima costruisci_modelli_da_query")

        return BatchPayload(
            batch=self.batch,
            misurazioni=list(self.misurazioni)  # copia esplicita
        )

    def ottieni_mappa_id_foglie(self) -> dict[int, str]:
        """
        Costruisce una mappa id --> hash (foglie) a partire da DatiBatch e DatiMisurazione.
        Restituisce un dizionario che mappa ogni ID logico al suo hash:
        - ID 0 per il batch
        - ID della misurazione per ogni misurazione

        Utilità: necessario per costruire in modo semplice e veloce il merkle tree che lavora
        solo su foglie (hash) senza dover saper nient altro. Mentre gli id sono necessari per dare
        un significato ai merkle path (ovvero l'unico modo che abbiamo per
        ricostruire la prova di integrità foglia per foglia)

        ATTENZIONE: questo metodo lavora internamente su oggetti specifici dell'istanza e
        che hanno subito una fase di ordinamento sui campi all'interno del metodo
        CostruttoreModelliDaQuery.costruisci_modelli_da_query
        """
        if not self.hash_batch:
            raise ValueError("Hash del batch non calcolato. Chiama prima costruisci_modelli_da_query.")
        if not self.hash_misurazioni_sensori:
            raise ValueError("Hash delle misurazioni non calcolate. Chiama prima costruisci_modelli_da_query.")

        mappa_id_hash = {ID_BATCH_LOGICO: self.hash_batch} #primo elemento mappato con 0
        mappa_id_hash.update(self.hash_misurazioni_sensori) #tutti i restanti elementi

        # Ordinamento finale del dizionario per chiave (ID)
        return dict(sorted(mappa_id_hash.items()))