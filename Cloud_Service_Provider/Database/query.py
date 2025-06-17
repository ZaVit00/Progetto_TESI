CREA_TABELLA_SENSORE = """
CREATE TABLE IF NOT EXISTS sensore (
    id_sensore TEXT PRIMARY KEY,
    descrizione TEXT NOT NULL,
    tipo TEXT NOT NULL
);
"""

CREA_TABELLA_BATCH = """
CREATE TABLE IF NOT EXISTS batch (
    id_batch INTEGER PRIMARY KEY,
    timestamp_creazione TEXT NOT NULL,
    numero_misurazioni INTEGER NOT NULL
);
"""

CREA_TABELLA_MISURAZIONE = """
CREATE TABLE IF NOT EXISTS misurazione (
    id_misurazione INTEGER PRIMARY KEY,
    id_batch      INTEGER NOT NULL REFERENCES batch(id_batch),
    id_sensore    TEXT NOT NULL REFERENCES sensore(id_sensore),
    timestamp     TEXT    NOT NULL,
    dati          JSONB   NOT NULL
);
"""

# Inserisce un nuovo sensore
INSERISCI_SENSORE = """
INSERT INTO sensore (id_sensore, descrizione, tipo)
VALUES (%s, %s, %s);
"""

# Inserisce un nuovo batch
INSERISCI_BATCH = """
INSERT INTO batch (id_batch, timestamp_creazione, numero_misurazioni)
VALUES (%s, %s, %s);
"""

# Inserisce una nuova misurazione
INSERISCI_MISURAZIONE = """
INSERT INTO misurazione (id_misurazione, id_batch, id_sensore, timestamp, dati)
VALUES (%s, %s, %s, %s, %s);
"""
