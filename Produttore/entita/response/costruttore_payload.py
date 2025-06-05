from typing import List, Dict
import json

from dati_modellati import DatiBatch, DatiPayload
from dati_modellati import DatiMisurazione
from utils.hash_utils import calcola_hash

# === CLASSE PRINCIPALE ===
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

        prima_riga = risultati_query[0]
        self.batch = DatiBatch(
            id_batch=prima_riga["id_batch"],
            timestamp_creazione=prima_riga["timestamp_creazione"],
            numero_misurazioni=prima_riga["numero_misurazioni"],
        )

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
                hash_tupla = calcola_hash(self.batch.hash() + mis.hash())
                self.lista_hash_tuple.append(hash_tupla)

            except Exception as e:
                print(f"[ERRORE] Errore durante la creazione della misurazione_in_ingresso: {e}")

    def get_hash_foglie(self) -> List[str]:
        """
        Restituisce la lista di hash delle tuple (batch + misurazione).
        """
        return self.lista_hash_tuple

    def costruisci_payload(self, merkle_root: str | None = None) -> DatiPayload:
        """
        Costruisce il payload finale da inviare al cloud.
        Se viene fornita una Merkle Root, aggiorna il campo nel batch.
        Solleva un'eccezione se i dati non sono pronti.
        """
        if self.batch is None:
            raise ValueError("Il batch non è stato inizializzato. Chiama prima 'estrai_dati_query'.")

        if not self.misurazioni:
            raise ValueError("Nessuna misurazione_in_ingresso trovata. Il payload sarebbe vuoto.")

        batch_con_root = (
                self.batch.model_copy(update={"merkle_root": merkle_root})
                if merkle_root is not None
                else self.batch
        )

        return DatiPayload(
            batch=batch_con_root,
            misurazioni=self.misurazioni
        )

    #METODO DI DEBUG PER VISUALIZZARE UN PAYLOAD COMPLETO
    def to_json(self, merkle_root: str | None = None) -> str:
        dp = self.costruisci_payload(merkle_root=merkle_root)
        #costruire il JSON a partire dal dizionario
        return dp.model_dump_json(indent=2)