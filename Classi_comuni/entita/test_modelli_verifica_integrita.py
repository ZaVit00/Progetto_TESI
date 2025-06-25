from modelli_dati import DatiBatch, DatiSensore, DatiMisurazione
from modelli_verifica_integrita import DatiMisurazioneSensore, DatiPerVerificaEstesa

# 1. Creazione dati locali
batch_locale = DatiBatch(
    id_batch=1,
    timestamp_creazione="2024-06-01T12:00:00",
    numero_misurazioni=2
)

sensore_locale = DatiSensore(
    id_sensore="TEMP001",
    descrizione="Sensore stanza A"
)

misurazione_locale = DatiMisurazione(
    id_misurazione=100,
    id_sensore="TEMP001",
    timestamp="2024-06-01T12:01:00",
    id_batch=1,
    dati={"temp": 23.5, "hum": 55}
)

dms_locale = DatiMisurazioneSensore(
    dati_sensore=sensore_locale,
    dati_misurazione=misurazione_locale
)

verifica_locale = DatiPerVerificaEstesa(
    dati_batch=batch_locale,
    dati_misurazione_sensore=[dms_locale]
)

# 2. Creazione dati ricevuti (simula cloud manomesso o alterato)
batch_ricevuto = DatiBatch(
    id_batch=1,
    timestamp_creazione="2024-06-01T12:05:00",  # ← timestamp differente
    numero_misurazioni=2
)

sensore_ricevuto = DatiSensore(
    id_sensore="TEMP001",
    descrizione="Sensore stanza modificato"  # ← descrizione modificata
)

misurazione_ricevuta = DatiMisurazione(
    id_misurazione=100,
    id_sensore="TEMP001",
    timestamp="2024-06-01T12:01:00",
    id_batch=5,
    dati={"temp": 23.7, "hum": 55, "extra": 1000, "mamt": 2000}  # ← temp cambiato, chiave extra aggiunta
)

dms_ricevuto = DatiMisurazioneSensore(
    dati_sensore=sensore_ricevuto,
    dati_misurazione=misurazione_ricevuta
)

verifica_ricevuta = DatiPerVerificaEstesa(
    dati_batch=batch_ricevuto,
    dati_misurazione_sensore=[dms_ricevuto]
)

# 3. Calcolo differenze
differenze = verifica_locale.differenza(verifica_ricevuta)

# 4. Output
import json
print(json.dumps(differenze, indent=2, ensure_ascii=False))
