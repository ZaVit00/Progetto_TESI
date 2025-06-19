# Abilita i vincoli di integrità referenziale in SQLite (obbligatorio per usare FOREIGN KEY)
PRAGMA_FK = "PRAGMA foreign_keys = ON"

# Crea la tabella dei sensori registrati localmente.
# Il campo `conferma_ricezione` indica se il sensore è stato confermato dal cloud provider (0 = no, 1 = sì).
# È fondamentale per evitare problemi di integrità referenziale: se un sensore non è confermato,
# le sue misurazioni non possono essere mandate al cloud.
CREA_TABELLA_SENSORE = """
    CREATE TABLE IF NOT EXISTS sensore (
        id_sensore TEXT PRIMARY KEY,
        descrizione TEXT NOT NULL,
        tipo TEXT NOT NULL,
        conferma_ricezione INTEGER DEFAULT 0
    )
"""

# Crea la tabella dei batch. Ogni batch raccoglie un gruppo di misurazioni.
# completo: 1 = batch chiuso, 0 = ancora in raccolta.
# conferma_ricezione: 1 = batch confermato dal cloud, 0 = ancora in locale.
# merkle_root: radice Merkle calcolata per le misurazioni.
# cid_merkle_path: riferimento su IPFS ai Merkle Path.
# payload_json: JSON aggregato da inviare al cloud.
# elaborabile: 1 = batch valido, 0 = errore grave (non elaborabile).
# messaggio_errore e tipo_errore: info per il debug in caso di errore.
CREA_TABELLA_BATCH = """
    CREATE TABLE IF NOT EXISTS batch (
        id_batch INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_creazione TEXT NOT NULL,
        numero_misurazioni INTEGER NOT NULL DEFAULT 0,
        completo INTEGER NOT NULL DEFAULT 0,
        conferma_ricezione INTEGER NOT NULL DEFAULT 0,
        elaborabile INTEGER DEFAULT 1,
        merkle_root TEXT DEFAULT NULL,
        cid_merkle_path TEXT DEFAULT NULL,
        payload_json TEXT DEFAULT NULL,
        messaggio_errore TEXT DEFAULT NULL,
        tipo_errore TEXT DEFAULT  NULL
    )
"""

# Crea la tabella delle misurazioni.
# Ogni misurazione è associata a un sensore e a un batch tramite foreign key.
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

# Controlla se esiste già un sensore con l'id specificato
VERIFICA_ESISTENZA_SENSORE = """
SELECT 1 FROM sensore 
WHERE id_sensore = ?
"""

# Inserisce un nuovo sensore, ignorando la richiesta se l'ID è già presente
INSERISCI_SENSORE = """
    INSERT OR IGNORE INTO sensore (id_sensore, descrizione, tipo)
    VALUES (?, ?, ?)
"""

# Inserisce una nuova misurazione associata a sensore e batch
INSERISCI_MISURAZIONE = """
    INSERT INTO misurazione (id_sensore, id_batch, dati, timestamp)
    VALUES (?, ?, ?, ?)
"""

# Aggiorna il numero di misurazioni presenti in un batch
AGGIORNA_BATCH_NUM_MISURAZIONI = """
    UPDATE batch
    SET numero_misurazioni = ?
    WHERE id_batch = ?
"""

# Restituisce l’ultimo batch attivo (non completo), da usare per nuove misurazioni
OTTIENI_BATCH_ATTIVO = """
    SELECT id_batch, numero_misurazioni
    FROM batch
    WHERE completo = 0
    ORDER BY id_batch DESC
    LIMIT 1
"""

# Chiude un batch (completo = 1)
CHIUDI_BATCH = """
    UPDATE batch
    SET completo = 1
    WHERE id_batch = ?
"""

# Segna un batch come ricevuto dal cloud (conferma_ricezione = 1), ma solo se è completo
AGGIORNA_BATCH_CONFERMA_RICEZIONE = """
    UPDATE batch
    SET conferma_ricezione = 1
    WHERE id_batch = ? AND completo = 1
"""

# Elimina tutte le misurazioni associate a un batch (tipicamente dopo invio al cloud)
ELIMINA_MISURAZIONI = """
    DELETE FROM misurazione WHERE id_batch = ?
"""

# Crea un nuovo batch inizializzato con 0 misurazioni e non completo
CREA_BATCH = """
    INSERT INTO batch (timestamp_creazione, numero_misurazioni, completo, conferma_ricezione)
    VALUES (?, 0, 0, 0)
"""

# Estrae tutte le misurazioni di un batch, includendo anche i metadata del batch stesso
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

# In caso di errore grave durante l’elaborazione del batch lo segna come non elaborabile
# CASI DI ERRORE:
# - IPFS
# - BLOCKCHAIN
# - HTTP (errori di http non considerati come errori gravi tali da interrompere l'elaborazione
# del batch)
AGGIORNA_ERRORE_ELABORAZIONE_BATCH = """
    UPDATE batch
    SET elaborabile = ?,
        messaggio_errore = ?,
        tipo_errore = ?
    WHERE id_batch = ?
"""

#Salva il merkle root, il cid IPFS e il payload JSON di un batch correttamente
# elaborato durante la pipeline di esecuzione
AGGIORNA_METADATA_BATCH = """
    UPDATE batch 
    SET merkle_root = ?, cid_merkle_path = ?, payload_json = ?
    WHERE id_batch = ?
"""

#--------------------------------#
# QUERY ESEGUITE DA TASK DI RETRY
#--------------------------------#

"""
Seleziona i batch completi (hanno raggiunto la soglia di misurazioni massime previste)
che necessitano di elaborazioni:
(elaborabile=1) e merkle_root e/o payload_json nulli
(significa che il batch deve ancora attraversare la pipeline di elaborazione)
"""
OTTIENI_ID_BATCH_COMPLETI_DA_ELABORARE = """
    SELECT DISTINCT b.id_batch
    FROM batch b
    INNER JOIN misurazione m ON b.id_batch = m.id_batch
    WHERE b.completo = 1
    AND b.conferma_ricezione = 0
    AND b.elaborabile = 1
    AND (b.merkle_root IS NULL OR b.merkle_root = '')
    AND (b.payload_json IS NULL OR b.payload_json = '')
    ORDER BY b.id_batch ASC
    LIMIT 1;
"""

"""
Restituisce i batch pronti per l’invio: 
- payload_json presente,
- ancora non confermati (conferma_ricezione = 0)
- non corrotti/errori gravi durante la pipeline (elaborabile = 1)
Il batch passa attraverso varie fasi di esecuzione e un errore di elaborazione
tale da impedire la elaborazione può avvenire in tre casi: 
- Durante il salvataggio del merkle path su IPFS
- Durante il salvataggio del merkle root + cid ipfs su blockchain

- Durante Http,considerato errore non grave ma dovuto alla connessione Internet
Se accade un errore di elaborazione in qualunque di queste due fasi, il batch si troverà
in uno stato inconsistente e quindi la sua elaborazione deve essere bloccata. Se avviene anche solo
un errore durante la elaborazione il batch è marcato come non elaborabile e la query così scritta
ne impedisce l'invio del payload JSON. Per evitare violazioni ai vincoli di integrità referenziale lato
cloud, è possibile inviare il payload di un batch solo se i sensori che hanno eseguito le misurazioni
sono stati registrati dal cloud (conferma_ricezione di sensore). Se così non fosse si creerebbero errori
a cascata.
"""
OTTIENI_PAYLOAD_BATCH_PRONTI_PER_INVIO = """
    SELECT b.id_batch, b.payload_json   
    FROM batch as b
    INNER JOIN misurazione as m ON b.id_batch = m.id_batch
    INNER JOIN sensore as s ON m.id_sensore = s.id_sensore
    WHERE payload_json IS NOT NULL
    AND b.conferma_ricezione = 0
    AND elaborabile = 1
    AND s.conferma_ricezione = 1
    ORDER BY b.id_batch ASC
    LIMIT 1
"""

"""
Restituisce un elenco (massimo 6) dei sensori registrati localmente ma non ancora confermati dal cloud.
Questa informazione è utile per eseguire un retry dell'invio dei dati sensore al cloud provider.
"""
OTTIENI_SENSORI_NON_CONFERMA_RICEZIONE = """
    SELECT id_sensore, descrizione
    FROM sensore
    WHERE conferma_ricezione = 0
    LIMIT 3;
"""

AGGIORNA_CONFERMA_RICEZIONE_BATCH = """
    UPDATE batch
    SET conferma_ricezione = 1
    WHERE id_batch = ?
"""

AGGIORNA_CONFERMA_RICEZIONE_SENSORE = """
    UPDATE sensore
    SET conferma_ricezione = 1
    WHERE id_sensore = ?
"""


