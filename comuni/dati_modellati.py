import json
from abc import ABC
from typing import Dict, List
from pydantic import BaseModel, Field
from hash_utils import Hashing


class ModelliHashabili(BaseModel, ABC):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    e da cui calcolare un hash univoco.
    """

    def to_json(self) -> str:
        """
        Restituisce una rappresentazione JSON ordinata e leggibile della tupla.
        Questa serializzazione viene utilizzata per il calcolo dell'hash e per eventuali
        operazioni di debug o logging. APPLICABILE SOLO A ISTANZE DI PYDANTIC (modul_dump)
        """
        return json.dumps(
            self.model_dump(),
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )

    def to_hash(self) -> str:
        """
        Calcola e restituisce l'hash SHA-256 della tupla,
        serializzandola prima in formato JSON.
        """
        return Hashing.calcola_hash(self.to_json())


class DatiMisurazione(ModelliHashabili):
    """
    Rappresenta una singola misurazione proveniente da un sensore.
    """
    id_misurazione: int = Field(..., title="ID Misurazione", description="Identificativo univoco della misurazione")
    id_sensore: str = Field(..., title="ID Sensore", description="Identificativo del sensore IoT che ha generato la misurazione")
    timestamp: str = Field(..., title="Timestamp", description="Data e ora della misurazione in formato ISO 8601")
    dati: Dict = Field(..., title="Dati rilevati", description="Contenuto effettivo della misurazione in formato JSON")


class DatiBatch(ModelliHashabili):
    """
    Rappresenta i metadati di un batch di misurazioni.
    """
    id_batch: int = Field(..., title="ID Batch", description="Identificativo univoco del batch")
    timestamp_creazione: str = Field(..., title="Timestamp di creazione", description="Data e ora di creazione del batch in formato ISO 8601")
    numero_misurazioni: int = Field(..., title="Numero misurazioni", description="Numero totale di misurazioni contenute nel batch")
    merkle_root: str = Field(
        "", title="Merkle Root",
        description="Hash radice dell’albero Merkle costruito sulle misurazioni del batch"
    )

class DatiPayload(BaseModel):
    """
    Payload completo da inviare al cloud: contiene un batch e le sue misurazioni associate.
    """
    batch: DatiBatch = Field(..., title="Batch", description="Metadati del batch, inclusa la Merkle Root")
    misurazioni: List[DatiMisurazione] = Field(..., title="Misurazioni", description="Lista delle misurazioni associate al batch")