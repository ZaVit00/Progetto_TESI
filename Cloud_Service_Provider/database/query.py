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
    id_batch      INTEGER NOT NULL,
    id_sensore    TEXT NOT NULL,
    timestamp     TEXT    NOT NULL,
    dati          JSONB   NOT NULL,
    FOREIGN KEY (id_batch) REFERENCES batch(id_batch) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_sensore) REFERENCES sensore(id_sensore) ON DELETE CASCADE ON UPDATE CASCADE
);
"""

# Inserisce un nuovo sensore
INSERISCI_SENSORE = """
INSERT INTO sensore (id_sensore, descrizione, tipo)
VALUES (%s, %s, %s)
ON CONFLICT (id_sensore) DO NOTHING;
"""

# Inserisce un nuovo batch
INSERISCI_BATCH = """
INSERT INTO batch (id_batch, timestamp_creazione, numero_misurazioni)
VALUES (%s, %s, %s)
ON CONFLICT (id_batch) DO NOTHING;
"""

# Inserisce una nuova misurazione
INSERISCI_MISURAZIONE = """
INSERT INTO misurazione (id_misurazione, id_batch, id_sensore, timestamp, dati)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id_misurazione) DO NOTHING;
"""

# Estrae tutte le misurazioni di un batch, includendo anche i dati delle misurazioni e del sensore
# che lo ha generato
OTTIENI_DATI_BATCH_MISURAZIONI_SENSORI = """
    SELECT m.id_misurazione,
    m.id_sensore,
    m.timestamp,
    m.dati,
    b.id_batch,
    b.timestamp_creazione,
    b.numero_misurazioni,
    s.tipo,
    s.descrizione
    FROM misurazione AS m
    INNER JOIN batch AS b ON m.id_batch = b.id_batch
    INNER JOIN sensore as s ON m.id_sensore = s.id_sensore
    WHERE b.id_batch = %s
    ORDER BY m.id_misurazione ASC;
"""

#estrae le informazioni associate a una misurazione
OTTIENI_METADATA_MISURAZIONE_SENSORE = """
    SELECT m.id_misurazione, m.id_batch, m.timestamp, s.id_sensore, s.tipo
    from misurazione as m inner join sensore as s on m.id_sensore = s.id_sensore
    where id_misurazione = %s
"""

OTTIENI_METADATA_BATCH = """
    SELECT id_batch, numero_misurazioni, timestamp_creazione
    from batch
    where id_batch = %s
"""
OTTIENI_DATA_BATCH = """
    SELECT id_batch, numero_misurazioni, timestamp_creazione
    from batch
    where id_batch = %s
"""

OTTIENI_DATI_MISURAZIONE_SENSORE = """
SELECT m.id_misurazione, m.id_batch, m.id_sensore, m.dati, m.timestamp, s.tipo, s.descrizione
FROM misurazione m INNER JOIN sensore s ON m.id_sensore = s.id_sensore
WHERE m.id_misurazione = ?
"""