import json
import re
from typing import Dict, List
from pydantic import Field, field_validator
from Classi_comuni.utils import canonizza_dict
from modelli import ModelliHashabili


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
    id_sensore: str = Field(..., description="Identificativo del sensore che ha generato la misurazione")
    timestamp: str = Field(..., description="Data e ora della misurazione")
    id_batch: int = Field(..., description="Identificativo del batch a cui appartiene la misurazione")
    dati: Dict = Field(..., title="Dati rilevati", description="Contenuto effettivo della misurazione in formato JSON")

    def to_json(self) -> str:
        # Copia dell'oggetto come dizionario
        # Classe pydantic --> Dizionario
        dump = self.model_dump()
        # Canonizza il campo "dati" separatamente
        # cioè rende OMOGENEO il campo dati. Necessario per la verifica dell'integrità salvare
        # in modo omogeneo i campi dei dati nello stesso modo tra sqlite e postegreSQL
        dump["dati"] = canonizza_dict(self.dati)
        return json.dumps(
            dump,
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )


    def differenza(self, altro: "DatiMisurazione") -> dict:
        differenze = {}
        # Confronta tutti i campi tranne 'dati'
        dump_self = self.model_dump(exclude={"dati"})
        dump_altro = altro.model_dump(exclude={"dati"})

        for campo, val_self in dump_self.items():
            val_altro = dump_altro.get(campo)
            if val_self != val_altro:
                differenze[campo] = {
                    "locale": val_self,
                    "ricevuto": val_altro
                }
        # Gestione dedicata per il campo 'dati'
        dati_locale = canonizza_dict(self.dati)
        dati_cloud = canonizza_dict(altro.dati)

        chiavi = set(dati_locale.keys()) | set(dati_cloud.keys())
        differenze_dati = {}

        for chiave in chiavi:
            val_locale = dati_locale.get(chiave)
            val_ricevuto = dati_cloud.get(chiave)

            if val_locale != val_ricevuto:
                differenze_dati[chiave] = {
                    "locale": val_locale,
                    "ricevuto": val_ricevuto
                }

        if differenze_dati:
            differenze["dati"] = differenze_dati

        return differenze


class DatiBatch(ModelliHashabili):
    """
    Rappresenta i dati di un batch di misurazioni.
    """
    id_batch: int = Field(..., title="ID Batch", description="Identificativo univoco del batch")
    timestamp_creazione: str = Field(..., description="Data e ora di creazione del batch")
    numero_misurazioni: int = Field(..., description="Numero totale di misurazioni nel batch")

class PacchettoBatchMisurazioni(ModelliHashabili):
    """
    Payload completo da inviare al cloud: contiene un batch e le sue misurazioni associate.
    """
    batch: DatiBatch = Field(..., title="Batch", description="Metadata del batch")
    misurazioni: List[DatiMisurazione] = Field(..., title="Lista di Misurazioni", description="Lista delle misurazioni associate al batch")

class DatiListaSensori(ModelliHashabili):
    sensori : List[DatiSensore] = Field(..., title="Lista di Sensori", description="Lista di sensori presenti nel sistema")

