PRAGMA_FK = "PRAGMA foreign_keys = ON"

CREA_TABELLA_SENSORE = """
    CREATE TABLE IF NOT EXISTS sensore (
        id_sensore TEXT PRIMARY KEY,
        descrizione TEXT NOT NULL
    )
"""

CREA_TABELLA_BATCH = """
    CREATE TABLE IF NOT EXISTS batch (
        id_batch INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_creazione TEXT NOT NULL,
        numero_misurazioni INTEGER NOT NULL DEFAULT 0,
        completato INTEGER NOT NULL DEFAULT 0,
        conferma_ricezione INTEGER NOT NULL DEFAULT 0,
        elaborabile BOOLEAN DEFAULT 1,
        messaggio_errore TEXT DEFAULT NULL,
        tipo_errore TEXT DEFAULT  NULL,
        merkle_root TEXT DEFAULT NULL,
        payload_json TEXT DEFAULT NULL
        
    )
"""

CREA_TABELLA_MISURAZIONE = """
    CREATE TABLE IF NOT EXISTS misurazione (
        id_misurazione INTEGER PRIMARY KEY AUTOINCREMENT,
        id_sensore TEXT NOT NULL,
        id_batch INTEGER NOT NULL,
        dati TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (id_sensore) REFERENCES sensore(id_sensore) ON DELETE CASCADE,
        FOREIGN KEY (id_batch) REFERENCES batch(id_batch) ON DELETE CASCADE
    )
"""

BATCH_NON_INVIATI = """
    SELECT *
    FROM batch
    WHERE completato = 1
    AND conferma_ricezione = 0
    AND elaborabile = 1
    AND merkle_root IS NOT NULL
    AND merkle_root != ''
    AND payload_json IS NOT NULL
    AND payload_json != ''
    ORDER BY batch.id_batch;
"""

INSERISCI_SENSORE = """
    INSERT OR IGNORE INTO sensore (id_sensore, descrizione)
    VALUES (?, ?)
"""

BATCH_ATTIVO = """
    SELECT id_batch, numero_misurazioni
    FROM batch
    WHERE completato = 0
    ORDER BY id_batch DESC
    LIMIT 1
"""

INSERISCI_MISURAZIONE = """
    INSERT INTO misurazione (id_sensore, id_batch, dati, timestamp)
    VALUES (?, ?, ?, ?)
"""

AGGIORNA_BATCH_NUM_MISURAZIONI = """
    UPDATE batch
    SET numero_misurazioni = ?
    WHERE id_batch = ?
"""

AGGIORNA_MERKLE_ROOT_BATCH = """
    UPDATE batch
    SET merkle_root = ?
    WHERE id_batch = ?
"""

AGGIORNA_PAYLOAD_JSON_BATCH = """
    UPDATE batch
    SET payload_json = ?
    WHERE id_batch = ?
"""
CHIUDI_BATCH = """
    UPDATE batch
    SET completato = 1
    WHERE id_batch = ?
"""

IMPOSTA_BATCH_CONFERMA_RICEZIONE = """
    UPDATE batch
    SET conferma_ricezione = 1
    WHERE id_batch = ? AND completato = 1
"""

ELIMINA_MISURAZIONI = """
    DELETE FROM misurazione WHERE id_batch = ?
"""

CREA_BATCH = """
    INSERT INTO batch (timestamp_creazione, numero_misurazioni, completato, conferma_ricezione)
    VALUES (?, 0, 0, 0)
"""

ESTRAI_DATI_BATCH_MISURAZIONI = """
    SELECT 
        m.id_misurazione,
        m.id_sensore,
        m.timestamp,
        m.dati,
        b.id_batch,
        b.timestamp_creazione,
        b.numero_misurazioni
    FROM misurazione AS m
    INNER JOIN batch AS b ON m.id_batch = b.id_batch
    WHERE b.id_batch = ?
    ORDER BY m.id_misurazione ASC;
"""

# 0 = condizione di errore grave
# 1 = Nessun errore
IMPOSTA_ERRORE_ELABORAZIONE_BATCH = """
    UPDATE batch
    SET elaborabile = 0,
        messaggio_errore = ?,
        tipo_errore = ?
    WHERE id_batch = ?;
"""
BATCH_NON_ELABORABILI = """
    SELECT id_batch, tipo_errore, messaggio_errore, timestamp_creazione
    FROM batch
    WHERE elaborabile = 0
    ORDER BY id_batch;
"""

BATCH_ELABORALABILI_NON_COMPLETATI = """
    SELECT id_batch
    FROM batch
    WHERE completato = 1
    AND conferma_ricezione = 0
    AND elaborabile = 1
    AND merkle_root IS NULL
    AND payload_json IS NULL;
"""