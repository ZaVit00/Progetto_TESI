from typing import Dict, List

from pydantic import Field

from Classi_comuni.utils import canonizza_dict, serializza_dict
from modelli import ModelliHashabili


class DatiSensore(ModelliHashabili):
    """
    Modello che rappresenta i dati essenziali di un sensore memorizzati nel sistema.
    Attenzione: questa classe è distinta da `DatiSensoreInIngresso`, che viene usata
    solo durante la fase di registrazione iniziale di un sensore. In particolare:
    - `DatiSensoreInIngresso` contiene anche la frequenza di invio dei dati (frequenza_hz),
      necessaria per il calcolo dinamico della soglia di batch, ma che non viene trasmessa al cloud e non
      viene coinvolta nel processo di calcolo del merkle tree (necessaria solo in locale)
    - `DatiSensore` rappresenta il modello persistente e condivisibile dei dati del sensore,
      privo di informazioni locali interne (come la frequenza) e che viene utilizzato per serializzare,
      salvare e trasmettere i dati verso il cloud
    """
    id_sensore: str = Field(..., description="Identificatore del sensore."
                                             "Deve essere nel formato JOY001, TEMP042, HUM123 ecc.")
    descrizione: str = Field(..., description="Descrizione testuale del sensore.")
    tipo: str = Field(
        default="",
        description="Tipo del sensore (es. joystick, temperatura, umidità, pressione)."
    )


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
        #serializza in modo omogeno il dict (dict --> stringa json)
        return serializza_dict(dump)


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


class DatiMisurazioneSensore(ModelliHashabili):
    dati_sensore : DatiSensore = Field(..., description="dati del sensore")
    dati_misurazione : DatiMisurazione = Field(..., description="dati della misurazioni")
