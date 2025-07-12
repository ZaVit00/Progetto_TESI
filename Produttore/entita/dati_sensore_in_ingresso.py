import re

from pydantic import Field, field_validator, BaseModel

from costanti_produttore import MAPPING_PREFISSO_TIPO_SENSORE, REGEX_ID_SENSORE


class DatiSensoreInIngresso(BaseModel):
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
    frequenza_hz: float = Field(..., gt=0, description="Frequenza con cui il sensore invia misurazioni (in Hertz).")

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
        if not re.fullmatch(REGEX_ID_SENSORE, v):
            raise ValueError("id_sensore non segue il formato previsto (es. JOY001, TEMP042, HUM123)")
        return v

    def model_post_init(self, __context):
        """
        Metodo speciale eseguito dopo l'inizializzazione del modello.
        Imposta automaticamente il campo `tipo` sulla base del prefisso dell'`id_sensore`.
        La mappatura è: JOY  → joystick, TEMP → temperatura, HUM  → umidità, PRESS→ pressione
        Se il prefisso non è riconosciuto, il tipo viene impostato su 'generico'.
        """
        if self.tipo:
            # Se tipo è già avvalorato (non stringa vuota), NON lo toccare
            # SE VIENE ELIMINATO, IL CAMPO TIPO VIENE RIMPIAZZATO DAL TIPO CORRETTO
            # INVALIDA L'ANOMALIA
            return

        # Estrae il prefisso alfabetico (primi quattro caratteri) ignorando eventuali numeri
        # esempio: JOY20-> JOY
        prefisso = self.id_sensore[:4].strip("0123456789")
        self.tipo = MAPPING_PREFISSO_TIPO_SENSORE.get(prefisso, "generico")