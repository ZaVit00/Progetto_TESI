import json
from abc import ABC
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


    def differenza(self, altro: "ModelliSerializzabili") -> dict:
        """
        Confronta campo per campo due istanze Pydantic dello stesso tipo.
        Restituisce un dizionario con le differenze riscontrate:
        campo → {"locale": valore_self, "cloud": valore_altro}
        """
        differenze = {}
        dump_self = self.model_dump()
        dump_altro = altro.model_dump()

        for campo in dump_self:
            val_self = dump_self[campo]
            val_altro = dump_altro.get(campo)
            if val_self != val_altro:
                differenze[campo] = {
                    "locale": val_self,
                    "ricevuto": val_altro
                }

        return differenze


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
