import json
import re
from abc import ABC
from typing import Dict, List

from hash_utils import Hashing
from pydantic import BaseModel, Field, field_validator


class ModelliHashabili(BaseModel, ABC):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    e da cui calcolare un hash univoco.
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

    def to_hash(self) -> str:
        """
        Calcola e restituisce hash SHA-256 della tupla,
        serializzandola prima in formato JSON.
        """
        return Hashing.calcola_hash(self.to_json())


class DatiSensore(ModelliHashabili):
    """
    Modello che rappresenta un sensore generico registrabile nel sistema fog.
    Il tipo del sensore (joystick, temperatura, ecc.) Viene dedotto automaticamente
    dal prefisso dell'ID del sensore.
    """
    id_sensore: str = Field(..., description="Identificatore del sensore."
                                             "Deve essere nel formato JOY001, TEMP042, HUM123 ecc.")
    descrizione: str = Field(..., description="Descrizione testuale del sensore.")
    tipo: str = Field(
        default="",
        description="Tipo del sensore (es. joystick, temperatura, umidità, pressione)."
    )

    @field_validator("id_sensore")
    @classmethod
    def id_formato_standard(cls, v: str) -> str:
        """
        Valida il formato dell'ID del sensore:
        - Deve iniziare con uno dei prefissi ammessi: JOY, TEMP, HUM o PRESS
        - Deve essere seguito da esattamente tre cifre numeriche
        - L'ID viene automaticamente convertito in maiuscolo
        """
        v = v.upper()
        if not re.fullmatch(r"(JOY|TEMP|HUM|PRESS)\d{3}", v):
            raise ValueError("id_sensore non segue il formato previsto (es. JOY001, TEMP042, HUM123)")
        return v

    def model_post_init(self, __context):
        """
        Metodo speciale eseguito dopo l'inizializzazione del modello.
        Imposta automaticamente il campo `tipo` sulla base del prefisso dell'`id_sensore`.
        La mappatura è: JOY  → joystick, TEMP → temperatura, HUM  → umidità, PRESS→ pressione
        Se il prefisso non è riconosciuto, il tipo viene impostato su 'generico'.
        """
        mapping = {
            "JOY": "joystick",
            "TEMP": "temperatura",
            "HUM": "umidità",
            "PRESS": "pressione"
        }
        # Estrae il prefisso alfabetico (primi quattro caratteri) ignorando eventuali numeri
        # esempio: JOY20-> JOY
        prefisso = self.id_sensore[:4].strip("0123456789")
        self.tipo = mapping.get(prefisso, "generico")

class DatiMisurazione(ModelliHashabili):
    """
    Rappresenta una singola misurazione arricchita con metadata interni proveniente da un sensore.
    """
    id_misurazione: int = Field(..., title="ID Misurazione", description="Identificativo univoco della misurazione")
    id_sensore: str = Field(..., title="ID Sensore", description="Identificativo del sensore IoT che ha generato la misurazione")
    timestamp: str = Field(..., title="Timestamp", description="Data e ora della misurazione in formato ISO 8601")
    dati: Dict = Field(..., title="Dati rilevati", description="Contenuto effettivo della misurazione in formato JSON")


class DatiBatch(ModelliHashabili):
    """
    Rappresenta i metadata di un batch di misurazioni.
    """
    id_batch: int = Field(..., title="ID Batch", description="Identificativo univoco del batch")
    timestamp_creazione: str = Field(..., title="Timestamp di creazione", description="Data e ora di creazione del batch in formato ISO 8601")
    numero_misurazioni: int = Field(..., title="Numero misurazioni", description="Numero totale di misurazioni contenute nel batch")
    """
    Il campo merkle_root non è inviato al cloud ma è un campo associato al batch
    Può essere usato se vogliamo che il cloud lo memorizzi insieme ai dati del batch
    merkle_root: str = Field(
        "", title="Merkle Root",
        description="Hash radice dell’albero Merkle costruito sulle misurazioni del batch")
    """

class DatiPayload(ModelliHashabili):
    """
    Payload completo da inviare al cloud: contiene un batch e le sue misurazioni associate.
    """
    batch: DatiBatch = Field(..., title="Batch", description="Metadata del batch")
    misurazioni: List[DatiMisurazione] = Field(..., title="Lista di Misurazioni", description="Lista delle misurazioni associate al batch")


