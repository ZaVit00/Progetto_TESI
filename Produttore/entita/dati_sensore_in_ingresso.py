import re
from pydantic import BaseModel, Field, field_validator, ConfigDict
from costanti_produttore import MAPPING_PREFISSO_TIPO_SENSORE, REGEX_ID_SENSORE, TipoSensore


class DatiSensoreInIngresso(BaseModel):
    """
    Modello che rappresenta un sensore generico registrabile nel sistema fog.
    Il tipo del sensore (joystick, temperatura, etc) viene dedotto automaticamente
    dal prefisso dell'ID del sensore, a meno che non venga specificato esplicitamente.
    """
    id_sensore: str = Field(..., description="Identificatore del sensore. "
                                             "Deve seguire il formato JOY001, TEMP042, HUM123, ecc.")
    descrizione: str = Field(..., description="Descrizione testuale del sensore.")

    # il tipo viene infierito automaticamente a partire dalla sintassi del campo id_sensore
    tipo: TipoSensore = Field(
        default=TipoSensore.GENERICO,
        description="Tipo del sensore (es. joystick, temperatura, umidità, pressione)."
    )

    frequenza_hz: float = Field(..., gt=0, description="Frequenza di invio delle misurazioni (in Hz).")

    @field_validator("id_sensore")
    @classmethod
    def id_formato_standard(cls, v: str) -> str:
        """
        Valida il formato dell'ID del sensore:
        - Deve iniziare con un prefisso alfabetico valido (JOY, TEMP, HUM, PRESS)
        - Seguito da tre cifre numeriche
        - L'ID viene automaticamente convertito in maiuscolo
        """
        v = v.upper()
        #Validazione dell'id_sensore da inserire
        #in caso contrario FastAPI non crea l'istanza
        if not re.fullmatch(REGEX_ID_SENSORE, v):
            raise ValueError("id_sensore non rispetta il formato previsto (es. JOY001, TEMP042, HUM123)")
        return v

    def model_post_init(self, __context):
        """
        Metodo eseguito automaticamente da Pydantic dopo l'inizializzazione del modello.
        Deduce il tipo del sensore in base al prefisso dell'ID, se il campo 'tipo' è vuoto.
        Mappatura gestita da MAPPING_PREFISSO_TIPO_SENSORE.
        """
        if self.tipo.strip():
            # Se il campo tipo è già valorizzato (non stringa vuota o solo spazi), non modificarlo
            return

        # Estrae il prefisso alfabetico dall'ID
        # Esempi: "JOY001" → "JOY", "TEMP42" → "TEMP"
        match = re.match(r"([A-Z]+)", self.id_sensore)
        prefisso = match.group(1) if match else ""

        # Mappa il prefisso al tipo di sensore, se possibile
        self.tipo = MAPPING_PREFISSO_TIPO_SENSORE.get(prefisso, TipoSensore.GENERICO)
