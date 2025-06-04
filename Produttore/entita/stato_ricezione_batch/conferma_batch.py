from pydantic import BaseModel


class ConfermaBatch(BaseModel):
    id_batch: int
    messaggio: str