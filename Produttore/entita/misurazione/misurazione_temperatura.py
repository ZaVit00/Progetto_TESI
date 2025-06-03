from misurazione_base import Misurazione
from pydantic import Field

class MisurazioneTemperatura(Misurazione):
    """
    Rappresenta una misurazione effettuata da un sensore di temperatura.
    Estende la classe astratta Misurazione.
    """
    valore: float = Field(..., description="Valore della temperatura rilevata (in gradi Celsius)")

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione di temperatura.
        """
        dati = {
            "id_sensore": self.id_sensore,
            "valore": self.valore
        }
        return dati
