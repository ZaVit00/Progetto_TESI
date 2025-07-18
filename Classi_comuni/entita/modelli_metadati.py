# === CLASSI Pydantic DI SUPPORTO PER IL PROCESSO DI VERIFICA DELL'INTEGRITÀ ===
#
# Queste classi rappresentano metadati minimali relativi a sensori, misurazioni e batch.
# NON fanno parte del flusso regolare di invio dei dati (dal fog node al cloud).
#
# Vengono richieste ed elaborate ESCLUSIVAMENTE dal verificatore nel momento in cui
# una misurazione o un batch viene segnalato come "manomesso", al fine di:
# - analizzare manualmente o automaticamente le anomalie rilevate;
# - fornire un contesto comprensibile per il dato alterato;
# - confrontare in modo leggibile lo stato attuale con quello originario.
#
# ⚠ Attenzione: anche i metadati restituiti dal cloud potrebbero essere stati manomessi.
# Il verificatore li utilizza solo come riferimento informativo per confronti strutturati.

from pydantic import Field
from modelli import ModelliSerializzabili


class MetaDatiMisurazione(ModelliSerializzabili):
    id_misurazione: int = Field(..., title="ID Misurazione", description="Identificativo univoco della misurazione")
    id_batch: int = Field(..., description="Identificativo del batch a cui appartiene la misurazione")
    timestamp: str = Field(..., description="Data e ora della misurazione")

class MetaDatiSensore(ModelliSerializzabili):
 id_sensore: str = Field(..., description="Identificatore del sensore."
                                          "Deve essere nel formato JOY001, TEMP042, HUM123 ecc.")
 tipo: str = Field(
     default="",
     description="Tipo del sensore (es. joystick, temperatura, umidità, pressione)."
 )

class MetaDatiMisurazioneSensore(ModelliSerializzabili):
    metadati_sensore: MetaDatiSensore = Field(..., description="Metadati del sensore")
    metadati_misurazione: MetaDatiMisurazione = Field(..., description="Metadati della misurazione" )

class MetaDatiBatch(ModelliSerializzabili):
    id_batch: int = Field(..., title="ID Batch", description="Identificativo univoco del batch")
    timestamp_creazione: str = Field(..., description="Data e ora di creazione del batch")
    numero_misurazioni: int = Field(..., description="Numero totale di misurazioni nel batch")