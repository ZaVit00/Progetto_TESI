import json
from abc import ABC, abstractmethod
from typing import Dict, List
from pydantic import BaseModel
from utils.utils import calcola_hash


class ModelliHashabili(BaseModel, ABC):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    e da cui calcolare un hash univoco.
    """

    def to_json(self) -> str:
        """
        Restituisce una rappresentazione JSON ordinata e leggibile della misurazione.
        Questa serializzazione viene utilizzata per il calcolo dell'hash e per eventuali
        operazioni di debug o logging.
        """
        #utilizzo metodo della classe JSON di python
        # ha più opzioni per la formattazione della stringa JSON
        return json.dumps(
            # Pydantic --> DICT
            self.model_dump(),
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )

    def hash(self) -> str:
        """
        Calcola e restituisce l'hash SHA-256 della misurazione,
        serializzandola prima in formato JSON.

        Questo hash viene usato per garantire l’integrità della misurazione,
        ed è parte della costruzione delle foglie del Merkle Tree.
        """
        return calcola_hash(self.to_json())


class DatiMisurazione(ModelliHashabili):
    """
    Rappresenta una singola misurazione proveniente da un sensore.
    """
    id_misurazione: int
    id_sensore: str
    timestamp: str
    dati: Dict


class DatiBatch(ModelliHashabili):
    """
    Rappresenta i metadata di un batch di misurazioni.
    """
    id_batch: int
    timestamp_creazione: str
    numero_misurazioni: int
    merkle_root: str = ""


# La rappresenta il payload finale composto da un record di batch
# e N record di misurazioni
class DatiPayload(BaseModel):
    batch: DatiBatch
    misurazioni: List[DatiMisurazione]
