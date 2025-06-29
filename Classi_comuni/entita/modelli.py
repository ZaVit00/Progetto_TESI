import json
from abc import ABC

from deepdiff import DeepDiff
from pydantic import BaseModel

from Classi_comuni.utils import Hashing


class ModelliSerializzabili(BaseModel, ABC):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    """
    def to_json(self) -> str:
        """
        Restituisce una rappresentazione JSON ordinata e leggibile della tupla.
        Questa serializzazione viene utilizzata per il calcolo dell'hash e per eventuali
        operazioni di debug o logging. APPLICABILE SOLO A ISTANZE DI PYDANTIC (modul_dump)
        """
        return json.dumps(
            self.model_dump(),
            #ordina le chiavi
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )

class ModelliHashabili(ModelliSerializzabili):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    e da cui calcolare un hash univoco.
    """
    def to_hash(self) -> str:
        """
        Calcola e restituisce hash SHA-256 della tupla,
        serializzandola prima in formato JSON.
        """
        return Hashing.calcola_hash(self.to_json())

    def differenze_con(self, altro: "ModelliHashabili") -> dict:
        """
        Confronta l'istanza corrente con un'altra e restituisce un dizionario
        con le differenze rilevate usando DeepDiff.
        """
        return DeepDiff(
            self.model_dump(),
            altro.model_dump(),
            ignore_order=True,
            verbose_level = 2
        )
