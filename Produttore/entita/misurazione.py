from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class Misurazione(BaseModel, ABC):
    """
    Classe base astratta per tutte le misurazioni inviate dai microcontrollori.
    Contiene solo i dati comuni ad ogni misurazione.
    """
    id_sensore: str = Field(..., description="Identificativo univoco del sensore")

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione.
        Deve essere implementato da ogni sottoclasse.
        """
        pass
