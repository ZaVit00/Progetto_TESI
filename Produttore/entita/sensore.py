from pydantic import BaseModel

#classe che modella l'entità Sensore
class Sensore(BaseModel):
    id_sensore: str
    descrizione: str