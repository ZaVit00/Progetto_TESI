import re
from pydantic import BaseModel, Field, field_validator


class Sensore(BaseModel):
    """
    Modello che rappresenta un sensore generico.
    """

    id_sensore: str = Field(
        ...,
        description="Identificatore del sensore. Deve essere nel formato JOY001, TEMP042, HUM123 ecc."
    )

    descrizione: str = Field(
        ...,
        description="Descrizione testuale del sensore."
    )

    @field_validator("id_sensore")
    @classmethod
    def id_formato_standard(cls, v: str) -> str:
        """
        Valida che l'id_sensore sia nel formato corretto:
        - Deve iniziare con JOY, TEMP, HUM o PRESS
        - Seguito da 3 cifre
        - Viene convertito automaticamente in maiuscolo
        """
        v = v.upper()
        if not re.fullmatch(r"(JOY|TEMP|HUM|PRESS)\d{3}", v):
            raise ValueError("id_sensore non segue il formato previsto (es. JOY001, TEMP042, HUM123)")
        return v
