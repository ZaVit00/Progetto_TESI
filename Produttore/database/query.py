PRAGMA_FK = "PRAGMA foreign_keys = ON"
"""
Conferma_ricezione: 0 → tutti i sensori appena registrati sono considerati non ancora confermati.
Questo campo sarà aggiornato a 1 (TRUE) solo dopo conferma ricevuta dal cloud che il sensore è stato
memorizzato correttamente. Se un batch contiene delle misurazioni di sensori non ancora confermati dal cloud
(significa che non sono stati registrati nel cloud per problemi di quest'ultimo, allora i batch devono essere
trattenuti in locale per evitare vincoli di integrità referenziale. Inoltre, i dati del sensore devono essere
inviati prima di qualsiasi altra misurazione proprio per problemi di foreign key
"""
CREA_TABELLA_SENSORE = """
    CREATE TABLE IF NOT EXISTS sensore (
        id_sensore TEXT PRIMARY KEY,
        tipo TEXT NOT NULL,
        descrizione TEXT NOT NULL,
        conferma_ricezione INTEGER DEFAULT 0;
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

VERIFICA_ESISTENZA_SENSORE = """
SELECT 1 FROM sensore 
WHERE id_sensore = ?
"""

SENSORI_NON_RICEVUTI = """
    SELECT id_sensore, descrizione
    FROM sensore
    WHERE conferma_ricezione = 0
    LIMIT 5;
"""

INSERISCI_SENSORE = """
    INSERT OR IGNORE INTO sensore (id_sensore, descrizione)
    VALUES (?, ?)
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

BATCH_ATTIVO = """
    SELECT id_batch, numero_misurazioni
    FROM batch
    WHERE completato = 0
    ORDER BY id_batch DESC
    LIMIT 1
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

"""
In seguito ad errori gravi, i batch possono essere marcati come NON ELABORABILI
ovvero, non recuperabili dal sistema (richiedono intervento umano)
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
"""
Estrae i batch completati, elaborabili, non ancora inviati al cloud (conferma_ricezione = 0),
che risultano elaborabili e per cui è già stata generata la Merkle Root e il payload_json.
Inoltre, si assicura che tutte le misurazioni associate siano collegate a sensori 
già confermati dal cloud (sensore.conferma_ricezione = 1), così da evitare 
violazioni di integrità referenziale durante l'invio.
La query restituisce al massimo 6 batch ordinati per ID crescente.
"""
BATCH_NON_INVIATI_COMPLETATI_ELABORABILI = """
    SELECT DISTINCT b.*
    FROM batch b
    JOIN misurazione m ON b.id_batch = m.id_batch
    JOIN sensore s ON m.id_sensore = s.id_sensore
    WHERE b.completato = 1
    AND b.conferma_ricezione = 0
    AND b.elaborabile = 1
    AND b.merkle_root IS NOT NULL AND b.merkle_root != ''
    AND b.payload_json IS NOT NULL AND b.payload_json != ''
    AND s.conferma_ricezione = 1
    ORDER BY b.id_batch,
    LIMIT 6;
"""

"""
Riconosce i batch che sono stati chiusi ma, 
per un errore durante la creazione del Merkle Tree o del payload JSON
(es. crash, errore di hash, eccezione), non sono stati elaborati correttamente né inviati.
Considerato come errore di run-time.

QUERY PREVISTA PER EFFETTUARE UN TENTATIVO DI RIELABORAZIONE
DI BATCH CON ERRORI BLOCCANTI. ATTUALMENTE NON UTILIZZATA NEL SISTEMA.
Un eventuale recupero dovrà essere gestito manualmente o con tool dedicati.
"""
BATCH_NON_ELABORABILI_COMPLETATI = """
    SELECT id_batch
    FROM batch
    WHERE completato = 1
      AND conferma_ricezione = 0
      AND elaborabile = 0
      AND merkle_root IS NULL
      AND payload_json IS NULL;
"""
