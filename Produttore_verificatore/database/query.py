RECUPERA_DATI_BATCH = """
SELECT id_batch, numero_misurazioni, timestamp_creazione
FROM batch WHERE id_batch = ?
"""

RECUPERA_DATI_MISURAZIONE = """
SELECT id_misurazione, id_batch, id_sensore, dati, timestamp
FROM misurazione_in_ingresso WHERE id_misurazione = ?
"""