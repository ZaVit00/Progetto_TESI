# Abilita i vincoli di integrità referenziale in SQLite (obbligatorio per usare FOREIGN KEY)
PRAGMA_FK = "PRAGMA foreign_keys = ON"


#----------------------- QUERY DI CREAZIONE TABELLA -----------------------#

# Crea la tabella dei sensori registrati localmente.
CREA_TABELLA_SENSORE = """
    CREATE TABLE IF NOT EXISTS sensore (
        id_sensore TEXT PRIMARY KEY,
        descrizione TEXT NOT NULL,
        tipo TEXT NOT NULL,
        frequenza_hz REAL NOT NULL,
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
# Messaggio_errore e tipo_errore: info per il debug in caso di errore.
# Transazione_hash utilizzato per determinare a quale transazione corrisponde un certo batch (scopi di debug/log)

CREA_TABELLA_BATCH = """
    CREATE TABLE IF NOT EXISTS batch (
        id_batch INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp_creazione TEXT NOT NULL,
        numero_misurazioni INTEGER NOT NULL DEFAULT 0,
        soglia_misurazioni INTEGER NOT NULL DEFAULT 0,
        completo INTEGER NOT NULL DEFAULT 0,
        conferma_ricezione INTEGER NOT NULL DEFAULT 0,
        elaborabile INTEGER NOT NULL DEFAULT 1,
        merkle_root TEXT DEFAULT NULL,
        cid_merkle_path TEXT DEFAULT NULL,
        transazione_hash TEXT DEFAULT NULL,
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

# ------------------------- QUERY DI LETTURA -------------------------

# Controlla se esiste già un sensore con l'id specificato
VERIFICA_ESISTENZA_SENSORE = """
SELECT 1 FROM sensore 
WHERE id_sensore = ?
"""

# Restituisce l’ultimo batch attivo (non ancora completo), da usare per associare nuove misurazioni
OTTIENI_BATCH_ATTIVO = """
    SELECT id_batch, numero_misurazioni, soglia_misurazioni
    FROM batch
    WHERE completo = 0
    ORDER BY id_batch DESC
    LIMIT 1
"""

# Estrae tutte le misurazioni di un batch, includendo anche i metadata del batch stesso
OTTIENI_DATI_BATCH_MISURAZIONI_SENSORI = """
    SELECT
        m.id_misurazione,
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
    INNER JOIN sensore AS s ON m.id_sensore = s.id_sensore
    WHERE b.id_batch = ?
    ORDER BY m.id_misurazione ASC;
"""

# Estrae i dati di un sensore (tipo, descrizione) dato il suo ID.
OTTIENI_DATI_SENSORI = """
    SELECT id_sensore, tipo, descrizione
    FROM sensore
    WHERE id_sensore = ?
"""

#  Estrae metadati principali di un batch: ID, timestamp di creazione e numero di misurazioni.
OTTIENI_DATI_BATCH = """
    SELECT id_batch, timestamp_creazione, numero_misurazioni
    FROM batch
    WHERE id_batch = ?
"""

"""
Estrae il payload JSON associato a un batch, solo se presente.
È la forma aggregata pronta per essere inviata al cloud provider.
Viene utilizzata nei retry o nei task di invio periodico.
"""
OTTIENI_PAYLOAD_BATCH = """
    SELECT payload_json
    FROM batch
    WHERE id_batch = ? AND payload_json IS NOT NULL
"""

OTTIENI_FREQUENZA_MEDIA_SENSORI = """
   SELECT ROUND(AVG(frequenza_hz), 2) AS freq_media
   from sensore
"""
# ------------------------- QUERY DI UPDATE -------------------------

# Aggiorna l'hash della transazione di un batch quando avviene il salvataggio su blockchain del merkle root e
# cid ipfs
AGGIORNA_TRANSAZIONE_HASH_BATCH = """
    UPDATE batch
    SET transazione_hash = ?
    WHERE id_batch = ?
"""

# Chiude un batch (completo = 1)
CHIUDI_BATCH = """
    UPDATE batch
    SET completo = 1
    WHERE id_batch = ?
"""

# Segna un batch come ricevuto dal cloud (conferma_ricezione = 1)
# verifica se il batch è stato marcato come completo in precedenza
AGGIORNA_BATCH_CONFERMA_RICEZIONE = """
    UPDATE batch
    SET conferma_ricezione = 1
    WHERE id_batch = ? AND completo = 1
"""

# Aggiorna il numero di misurazioni presenti in un batch
AGGIORNA_BATCH_NUM_MISURAZIONI = """
    UPDATE batch
    SET numero_misurazioni = ?
    WHERE id_batch = ?
"""


# In caso di errore grave durante l’elaborazione del batch lo segna come non elaborabile
# CASI DI ERRORE: IPFS e BLOCKCHAIN
AGGIORNA_ERRORE_ELABORAZIONE_BATCH = """
    UPDATE batch
    SET elaborabile = 0,
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


"""
Segna un batch come ricevuto dal cloud.
Questa query viene eseguita dopo che il payload JSON è stato correttamente ricevuto e processato dal cloud.
Serve a evitare retry inutili: se `conferma_ricezione = 1`, il batch non verrà più inviato.
"""
AGGIORNA_CONFERMA_RICEZIONE_BATCH = """
    UPDATE batch
    SET conferma_ricezione = 1
    WHERE id_batch = ?
"""

"""
Segna un sensore come confermato dal cloud.
Questa conferma garantisce che tutte le future misurazioni di questo sensore possano essere inviate
al cloud senza violare vincoli di integrità referenziale.
È fondamentale che ogni sensore sia confermato prima dell'invio delle misurazioni.
"""
AGGIORNA_CONFERMA_RICEZIONE_SENSORI = """
    UPDATE sensore
    SET conferma_ricezione = 1
    WHERE id_sensore IN ({placeholders})
"""

# ------------------------- QUERY DI INSERIMENTO -------------------------

# Inserisce un nuovo sensore, ignorando la richiesta se l'ID è già presente
INSERISCI_SENSORE = """
    INSERT OR IGNORE INTO sensore (id_sensore, descrizione, tipo, frequenza_hz)
    VALUES (?, ?, ?, ?)
"""
# Inserisce una nuova misurazione associata a sensore e batch
INSERISCI_MISURAZIONE = """
    INSERT INTO misurazione (id_sensore, id_batch, dati, timestamp)
    VALUES (?, ?, ?, ?)
"""

# Crea un nuovo batch inizializzato con 0 misurazioni
INSERISCI_BATCH = """
    INSERT INTO batch (timestamp_creazione, numero_misurazioni, completo, conferma_ricezione, soglia_misurazioni)
    VALUES (?, 0, 0, 0, ?)
"""

# ------------------------- QUERY DI ELIMINAZIONE -------------------------

# Elimina tutte le misurazioni associate a un batch (dopo invio al cloud e conferma ricezione)
ELIMINA_MISURAZIONI = """
    DELETE FROM misurazione WHERE id_batch = ?
"""


#--------------------------------#
# QUERY ESEGUITE DA TASK DI RETRY
#--------------------------------#
"""
Seleziona il primo batch completo e marcato come elaborabile (elaborabile = 1),
che non è ancora stato elaborato (merkle_root e payload_json nulli o vuoti),
e non è stato ancora inviato al cloud (conferma_ricezione = 0).
Questo batch deve ancora passare attraverso la pipeline di elaborazione.
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
Restituisce i batch pronti per l’invio al cloud. Un batch è considerato pronto se:
- `payload_json` è presente (quindi il batch è stato elaborato correttamente)
- `conferma_ricezione = 0` (il batch non è ancora stato confermato dal cloud)
- `elaborabile = 1` (non sono avvenuti errori gravi durante la pipeline)

La pipeline di elaborazione può fallire in due punti critici:
1. Durante il salvataggio del Merkle Path su IPFS
2. Durante il salvataggio della Merkle Root e del CID IPFS su blockchain

Se si verifica un errore in uno di questi passaggi, il batch viene marcato come **non elaborabile**
(`elaborabile = 0`). In questo caso, l'invio del payload viene automaticamente bloccato da questa query,
evitando che vengano propagati dati inconsistenti.

Inoltre, per garantire l'integrità referenziale nel database del cloud provider,
la query seleziona solo i batch i cui sensori associati sono già stati confermati 
(conferma_ricezione = 1). Questo previene errori a cascata legati a riferimenti 
verso sensori non ancora presenti nel database remoto.
Nota: eventuali errori di integrità (es. chiave esterna non trovata) non sono 
da considerarsi errori applicativi, ma possono derivare da ritardi fisiologici 
nella sincronizzazione tra il nodo produttore e il cloud, non completamente controllabili.
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
    LIMIT 3
"""

"""
Restituisce un elenco dei sensori registrati localmente ma non ancora confermati dal cloud.
Questa informazione è utile per eseguire un retry dell'invio dei dati sensore al cloud provider.
"""
OTTIENI_SENSORI_NON_CONFERMA_RICEZIONE = """
    SELECT id_sensore, descrizione, tipo
    FROM sensore
    WHERE conferma_ricezione = 0
    ORDER BY id_sensore ASC
"""

