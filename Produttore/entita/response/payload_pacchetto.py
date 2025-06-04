from typing import Dict, List
import json
from pydantic import BaseModel
from utils.hash_utils import calcola_hash  # Funzione che calcola hash SHA-256


# === MODELLI DEI DATI USATI PER COSTRUIRE IL PAYLOAD ===

class DatiMisurazione(BaseModel):
    """
    Modello che rappresenta una singola misurazione proveniente da un sensore.
    """
    id_misurazione: int
    id_sensore: str
    timestamp: str
    dati: Dict  # dizionario generico con i dati del sensore (es. {"x": ..., "y": ...})


class DatiBatch(BaseModel):
    """
    Modello che rappresenta i metadati di un batch di misurazioni.
    """
    id_batch: int
    timestamp_creazione: str
    numero_misurazioni: int
    merkle_root: str  # hash finale calcolato con Merkle Tree


class DatiPayload(BaseModel):
    """
    Payload completo da inviare al cloud: include batch + lista di misurazioni.
    """
    batch: DatiBatch
    misurazioni: List[DatiMisurazione]

    def to_json(self) -> str:
        """
        Restituisce la rappresentazione JSON compatta del payload,
        pronta per essere inviata tramite API o salvata.
        """
        return json.dumps(self.model_dump(), separators=(",", ":"))

    def hash(self) -> str:
        """
        Calcola l'hash SHA-256 del payload serializzato in JSON.
        Questo hash rappresenta l'identità e integrità del pacchetto dati.
        """
        return calcola_hash(self.to_json())


class DataPackage:
    """
    Classe che rappresenta un pacchetto dati completo per un batch.
    Funzionalità principali:
    - Costruisce oggetti Pydantic a partire dai risultati di una query SQL.
    - Costruisce il payload finale da inviare al cloud, aggiungendo la Merkle Root.
    """

    def __init__(self, risultati_query: List[Dict]) -> None:
        # Lista di oggetti DatiMisurazione
        self.misurazioni : list[DatiMisurazione] = []
        # Oggetto DatiBatch (verrà inizializzato una volta sola)
        self.batch: DatiBatch
        # Chiama metodo interno per costruire i modelli dai dati grezzi
        self._estrai_dati(risultati_query)

    def _estrai_dati(self, risultati_query: List[Dict]) -> None:
        """
        Estrae i dati grezzi restituiti dalla query (in forma di lista di dizionari)
        e li trasforma in oggetti Pydantic per batch e misurazioni.
        """
        # Recupera i metadata del batch dalla prima riga
        prima_riga = risultati_query[0]
        self.batch = DatiBatch(
            id_batch=prima_riga["id_batch"],
            timestamp_creazione=prima_riga["timestamp_creazione"],
            numero_misurazioni=prima_riga["numero_misurazioni"],
            merkle_root=""  # la Merkle Root verrà aggiunta dopo
        )

        # Estrae tutte le misurazioni riga per riga
        for riga in risultati_query:
            try:
                self.misurazioni.append(
                    DatiMisurazione(
                        id_misurazione=riga["id_misurazione"],
                        id_sensore=riga["id_sensore"],
                        timestamp=riga["timestamp"],
                        dati=json.loads(riga["dati"])  # i dati vengono convertiti da stringa JSON a dizionario
                    )
                )
            except json.JSONDecodeError as e:
                print(f"[ERRORE] Decodifica JSON fallita per {riga.get('id_misurazione', '?')}: {e}")

    def costruisci_payload(self, merkle_root: str | None = None) -> DatiPayload:
        """
        Costruisce e restituisce un oggetto DatiPayload.
        - Se viene passato `merkle_root`, aggiorna i metadata del batch.
        - Se `merkle_root` è None, restituisce il payload "grezzo" per calcolo hash.
        """
        if merkle_root is not None:
            batch_con_root = self.batch.model_copy(update={"merkle_root": merkle_root})
        else:
            batch_con_root = self.batch
        return DatiPayload(batch=batch_con_root, misurazioni=self.misurazioni)

