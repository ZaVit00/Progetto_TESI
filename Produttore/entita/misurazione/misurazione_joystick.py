from misurazione_base import Misurazione
from pydantic import Field


class MisurazioneJoystick(Misurazione):
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
