from pydantic import BaseModel, Field
from abc import ABC, abstractmethod


class MisurazioneInIngresso(BaseModel, ABC):
    """
    Classe base astratta per tutte le misurazioni inviate dai microcontrollori.
    Contiene solo i dati comuni a ogni misurazione_in_ingresso.
    """
    id_sensore: str = Field(..., description="Identificativo univoco del sensore")

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso.
        Deve essere implementato da ogni sottoclasse.
        """
        pass

    def estrai_dati_misurazione(self):
        """
        Mantiene solo i campi della misurazione_in_ingresso eliminando
        quelli irrilevanti. Elimino id_sensore
        """
        d = self.to_dict()
        d.pop("id_sensore", None)
        return d


class MisurazioneInIngressoJoystick(MisurazioneInIngresso):
    """
    Estensione della classe Misurazione per le misurazioni effettuate
    da un sensore joystick. Aggiunge le coordinate x, y e il flag 'pressed'.
    """
    x: float = Field(..., description="Valore X del joystick")
    y: float = Field(..., description="Valore Y del joystick")
    pressed: bool = Field(..., description="Pulsante premuto o no")

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici del joystick.
        """
        dati = {
            "id_sensore": self.id_sensore,
            "x": self.x,
            "y": self.y,
            "pressed": self.pressed
        }
        return dati


class MisurazioneInIngressoTemperatura(MisurazioneInIngresso):
    """
    Rappresenta una misurazione_in_ingresso effettuata da un sensore di temperatura.
    Estende la classe astratta Misurazione.
    """
    valore: float = Field(..., description="Valore della temperatura rilevata (in gradi Celsius)")

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso di temperatura.
        """
        dati = {
            "id_sensore": self.id_sensore,
            "valore": self.valore
        }
        return dati
