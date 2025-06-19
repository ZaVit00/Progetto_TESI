from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field

from config.costanti_produttore import TIPO_SENSORE_JOYSTICK
from config.costanti_produttore import TIPO_SENSORE_TEMPERATURA

TipoSensore = Literal["JOYSTICK", "TEMPERATURA"]

class MisurazioneInIngresso(BaseModel, ABC):
    """
    Classe base astratta per tutte le misurazioni inviate dai microcontrollori.
    Contiene solo i dati Classi_comuni a ogni misurazione_in_ingresso.
    """
    id_sensore: str = Field(..., description="Identificativo univoco del sensore")

    #il tipo viene utilizzato da FastAPi per determinare quale istanza di misurazione è in ingresso
    # e validare i campi del JSON arrivato nella richiesta HTTP
    #È usato esclusivamente durante la fase di parsing e validazione dell’input JSON da parte di fastAPI
    #il campo tipo deve essere esplicitamente presente nel JSON ricevuto. é una ridondanza di informazioni
    #ma, necessaria ai fini della validazione delle misurazioni
    tipo: TipoSensore = Field(..., description="Tipo di misurazioni. Necessario per identificare"
                                       "l'istanza corretta di misurazione")

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso.
        Deve essere implementato da ogni sottoclasse.
        """
        pass

    def estrai_dati_misurazione(self):
        """
        Mantiene solo i dati effettivi della misurazione in ingresso eliminando
        i metadata. Elimino id_sensore e tipo che viene solo utilizzato per determinare
        la classe corretta da istanziare in fase di validazione dell'input ricevi_misurazione.)
        """
        d = self.to_dict()
        d.pop("id_sensore", None)
        # il tipo non viene memorizzato nella rappresentazione a dizionario
        #ora d contiene solo i dati effettivi della misurazione
        return d


class MisurazioneInIngressoJoystick(MisurazioneInIngresso):
    """
    Estensione della classe Misurazione per le misurazioni effettuate
    da un sensore joystick. Aggiunge le coordinate x, y e il flag 'pressed'.
    """
    x: float = Field(..., description="Valore X del joystick")
    y: float = Field(..., description="Valore Y del joystick")
    pressed: bool = Field(..., description="Pulsante premuto o no")
    # Literal ti permette di dire: Questa variabile può valere solo uno (o più) valori precisi”.
    tipo: Literal["JOYSTICK"] = TIPO_SENSORE_JOYSTICK

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
    tipo: Literal["TEMPERATURA"] = TIPO_SENSORE_TEMPERATURA

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso di temperatura.
        """
        dati = {
            "id_sensore": self.id_sensore,
            "valore": self.valore
        }
        return dati
