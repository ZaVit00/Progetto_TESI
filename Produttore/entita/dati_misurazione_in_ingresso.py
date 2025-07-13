from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel, Field
from Classi_comuni.utils import serializza_dict
from config.costanti_produttore import TIPO_SENSORE_JOYSTICK, TIPO_SENSORE_UMIDITA, TipoSensore
from config.costanti_produttore import TIPO_SENSORE_TEMPERATURA


class DatiMisurazioneInIngresso(BaseModel, ABC):
    """
    Classe base astratta per tutte le misurazioni inviate dai sensori (es. tramite Arduino).
    Contiene esclusivamente gli attributi comuni a ogni tipo di misurazione.

    Questa classe viene utilizzata da FastAPI per:
    - determinare dinamicamente quale sottoclasse di misurazione istanziare;
    - validare i campi presenti nel JSON ricevuto tramite richiesta HTTP.

    ⚠️ Il campo 'tipo' deve essere esplicitamente presente nel JSON in ingresso.
    Anche se ridondante, è necessario per permettere a FastAPI di discriminare correttamente
    tra i diversi tipi di misurazioni durante il parsing e la validazione.
    """
    id_sensore: str = Field(..., description="Identificativo univoco del sensore")

    tipo: TipoSensore = Field(..., description="Tipo di misurazioni. Necessario per identificare"
                                       "l'istanza corretta di misurazione")

    @abstractmethod
    def dati_misurazione_to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso.
        Deve essere implementato da ogni sottoclasse.
        """
        pass

    def estrai_dati_misurazione(self) -> str:
        """
        Estrae e normalizza i dati effettivi della misurazione:
        - Rimuove 'id_sensore' (metadata)
        - Normalizza gli zeri float (0.0, -0.0, -0.000 → 0)
        - Arrotonda tutti i float a 6 cifre decimali
        - Ordina le chiavi e restituisce una stringa JSON compatta
        """
        d = self.dati_misurazione_to_dict()
        # Normalizzazione (IMPORTANTISSIMO) di tutti i valori float equivalenti a zero
        for key, value in d.items():
            if isinstance(value, float) and abs(value) == 0.0:
                #normalizza a 0
                d[key] = 0
            else:
                d[key] = round(value, 6)  # Arrotonda a 6 cifre decimali

        # Serializzazione ordinata e compatta per uso coerente (es. hashing, confronto)
        return serializza_dict(d)



class DatiMisurazioneInIngressoJoystick(DatiMisurazioneInIngresso):
    """
    Estensione della classe Misurazione per le misurazioni effettuate
    da un sensore joystick. Aggiunge le coordinate x, y e il flag 'pressed'.
    """
    x: float = Field(..., description="Valore X del joystick")
    y: float = Field(..., description="Valore Y del joystick")
    pressed: bool = Field(..., description="Pulsante premuto o no")
    # Literal ti permette di dire: Questa variabile può valere solo uno (o più) valori precisi”.
    tipo: Literal[TipoSensore.JOYSTICK] = Field(
        default=TipoSensore.JOYSTICK,
        description="Tipo di misurazioni. Necessario per identificare l'istanza corretta."
    )

    def dati_misurazione_to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici del joystick.
        """
        dati = {
            "x": self.x,
            "y": self.y,
            "pressed": self.pressed
        }
        return dati

class DatiMisurazioneInIngressoTemperatura(DatiMisurazioneInIngresso):
    """
    Rappresenta una misurazione_in_ingresso effettuata da un sensore di temperatura.
    Estende la classe astratta Misurazione.
    """
    valore: float = Field(..., description="Valore della temperatura rilevata (in gradi Celsius)")
    tipo: Literal[TipoSensore.TEMPERATURA] = Field(
        default=TipoSensore.JOYSTICK,
        description="Tipo di misurazioni. Necessario per identificare l'istanza corretta."
    )

    def dati_misurazione_to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso di temperatura.
        """
        dati = {
            "valore": self.valore
        }
        return dati


class DatiMisurazioneInIngressoUmidita(DatiMisurazioneInIngresso):
    """
    Rappresenta una misurazione_in_ingresso effettuata da un sensore di umidità.
    Estende la classe astratta Misurazione.
    """
    valore: float = Field(..., description="Valore dell'umidità rilevata")
    tipo: Literal[TipoSensore.UMIDITA] = Field(
        default=TipoSensore.JOYSTICK,
        description="Tipo di misurazioni. Necessario per identificare l'istanza corretta."
    )

    def dati_misurazione_to_dict(self) -> dict:
        """
        Restituisce un dizionario con i dati specifici della misurazione_in_ingresso di temperatura.
        """
        dati = {
            "valore": self.valore
        }
        return dati
