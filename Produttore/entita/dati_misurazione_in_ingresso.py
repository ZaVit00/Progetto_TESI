from abc import ABC, abstractmethod
from typing import Literal
from pydantic import BaseModel, Field
from Classi_comuni.utils.dict_utils import serializza_dict
from config.costanti_produttore import  TipoSensore


class DatiMisurazioneInIngresso(BaseModel, ABC):
    """
    Classe base astratta per tutte le misurazioni ricevute in ingresso dai sensori (es. Arduino).

    Contiene esclusivamente gli attributi comuni a ogni tipo di misurazione e viene utilizzata
    da FastAPI per effettuare:

    - la validazione dei dati contenuti nel JSON ricevuto via HTTP;
    - l’instanziazione automatica della sottoclasse corretta, in base al tipo di sensore.

    ⚠️ Nota importante:
    Il campo 'tipo' deve essere presente nel JSON in ingresso.
    Anche se apparentemente ridondante, è fondamentale per consentire a FastAPI di discriminare
    tra i diversi tipi di misurazioni (parsing discriminato).
    """
    id_sensore: str = Field(..., description="Identificativo univoco del sensore")

    tipo: TipoSensore = Field(..., description=(
        "Tipo della misurazione (es. 'joystick', 'temperatura', ecc.). "
        "Serve a discriminare la sottoclasse corretta da istanziare."
    ))

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
