from typing import List, Dict
import json

from dati_modellati import DatiBatch, DatiPayload
from dati_modellati import DatiMisurazione
from utils.utils import calcola_hash

class CostruttorePayload:
    """
    Classe che estrae oggetti da una query INNER JOIN batch+misurazione_in_ingresso e
    calcola gli hash delle tuple (batch + misurazione_in_ingresso) tramite composizione
    degli hash individuali.
    """

    def __init__(self) -> None:
        #Lista che contiene gli N = SOGLIA oggetti DatiMisurazione
        self.misurazioni: List[DatiMisurazione] = []
        self.batch: DatiBatch | None = None
        self.lista_hash_tuple: List[str] = []

    def estrai_dati_query(self, risultati_query: List[Dict]) -> None:
        """
        Estrae gli oggetti Pydantic dalle righe SQL e calcola gli hash compositi.
        """
        self.misurazioni.clear()
        self.lista_hash_tuple.clear()

        #estrapola gli elementi della query
        prima_riga = risultati_query[0]
        self.batch = DatiBatch(
            id_batch=prima_riga["id_batch"],
            timestamp_creazione=prima_riga["timestamp_creazione"],
            numero_misurazioni=prima_riga["numero_misurazioni"],
        )
        batch_hash = self.batch.hash()

        for riga in risultati_query:
            try:
                #è un controllo per garantire che dati
                # sia effettivamente un dizionario
                # prima di creare l’oggetto DatiMisurazione.
                if isinstance(riga["dati"], str):
                    riga["dati"] = json.loads(riga["dati"])

                #crea l'oggetto DatiMisurazione
                mis = DatiMisurazione(
                    id_misurazione=riga["id_misurazione"],
                    id_sensore=riga["id_sensore"],
                    timestamp=riga["timestamp"],
                    dati=riga["dati"]
                )

                self.misurazioni.append(mis)
                # Combinazione hash: hash(batch) + hash(misurazione_in_ingresso)
                hash_tupla = calcola_hash(batch_hash + mis.hash())
                self.lista_hash_tuple.append(hash_tupla)

            except Exception as e:
                print(f"[ERRORE] Errore durante la creazione della misurazione_in_ingresso: {e}")

    def get_hash_foglie(self) -> List[str]:
        """
        Restituisce la lista di hash delle tuple (batch + misurazione).
        """
        return self.lista_hash_tuple

    def costruisci_payload(self, merkle_root: str) -> DatiPayload:
        """
        Costruisce il payload finale da inviare al cloud.
        La Merkle Root è obbligatoria e viene inserita nel campo `batch`.
        Solleva eccezioni se i dati non sono pronti.
        """
        if self.batch is None:
            raise ValueError("Il batch non è stato inizializzato. Chiama prima 'estrai_dati_query'.")

        if not self.misurazioni:
            raise ValueError("Nessuna misurazione trovata. Il payload sarebbe vuoto.")

        # Crea un nuovo oggetto Pydantic,a partire da self.batch con il campo merkle_root
        # avvalorato
        batch_con_root = self.batch.model_copy(update={"merkle_root": merkle_root})

        # Restituisce un oggetto Pydantic formato da un oggetto DatiBatch e una
        # lista di DatiMisurazioni
        return DatiPayload(
            batch=batch_con_root,
            # Copia esplicita per evitare alias: impedisce modifiche a self.misurazioni
            misurazioni= list(self.misurazioni)
        )