import os
import sqlite3
import json
from datetime import datetime

class GestoreDatabase:
    # Trova la directory root del progetto (2 livelli sopra gestore_db.py)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _DBPATH = os.path.join(BASE_DIR, "dati_temporanei.sqlite")
    _STRING_MAX_LENGTH = 12

    # Query SQL come costanti di classe
    _SQL_PRAGMA_FK = "PRAGMA foreign_keys = ON"

    _SQL_CREA_TABELLA_SENSORE = """
        CREATE TABLE IF NOT EXISTS sensore (
            id_sensore TEXT PRIMARY KEY,
            descrizione TEXT NOT NULL
        )
    """

    _SQL_CREA_TABELLA_BATCH = """
        CREATE TABLE IF NOT EXISTS batch (
            id_batch INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_creazione TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            numero_misurazioni INTEGER NOT NULL DEFAULT 0,
            completato INTEGER NOT NULL DEFAULT 0,
            merkle_root TEXT DEFAULT NULL
        )
    """

    _SQL_CREA_TABELLA_MISURAZIONE = """
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

    _SQL_INSERISCI_SENSORE = """
        INSERT OR IGNORE INTO sensore (id_sensore, descrizione)
        VALUES (?, ?)
    """

    _SQL_BATCH_ATTIVO = """
        SELECT id_batch, numero_misurazioni
        FROM batch
        WHERE completato = 0
        ORDER BY id_batch DESC
        LIMIT 1
    """

    _SQL_INSERISCI_MISURAZIONE = """
        INSERT INTO misurazione (id_sensore, id_batch, dati, timestamp)
        VALUES (?, ?, ?, ?)
    """

    _SQL_AGGIORNA_BATCH_MISURAZIONI = """
        UPDATE batch
        SET numero_misurazioni = ?
        WHERE id_batch = ?
    """

    _SQL_CHIUDI_BATCH = """
        UPDATE batch
        SET completato = 1
        WHERE id_batch = ?
    """

    _SQL_CREA_BATCH = """
        INSERT INTO batch (numero_misurazioni, completato)
        VALUES (0, 0)
    """

    def __init__(self, soglia_batch: int = 1024):
        self.conn = sqlite3.connect(self._DBPATH)
        #print("[INFO] Usando database:", os.path.abspath(self._DBPATH))
        self.conn.row_factory = sqlite3.Row
        self._crea_tabelle()
        self.soglia_batch = soglia_batch

    def _crea_tabelle(self):
        """
        Crea le tabelle sensore, batch e misurazione nel database, se non esistono.
        """
        print("[DEBUG] Creo tabelle sensore, batch, misurazione...")
        try:
            cursor = self.conn.cursor()
            cursor.execute(self._SQL_PRAGMA_FK)
            cursor.execute(self._SQL_CREA_TABELLA_SENSORE)
            cursor.execute(self._SQL_CREA_TABELLA_BATCH)
            cursor.execute(self._SQL_CREA_TABELLA_MISURAZIONE)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[ERRORE DATABASE] {e}")

    def inserisci_dati_sensore(self, id_sensore: str, descrizione: str) -> bool:
        """
        Inserisce un nuovo sensore solo se non già presente.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(self._SQL_INSERISCI_SENSORE, (id_sensore, descrizione))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE INSERIMENTO SENSORE] {e}")
            return False

    def inserisci_misurazione(self, id_sensore: str, dati: dict) -> tuple[bool, int | None]:
        """
        Inserisce una misurazione associata al batch attivo.
        Se non esiste un batch non completato, ne crea uno.
        Restituisce (True, id_batch_chiuso) se tutto va a buon fine,
        altrimenti (False, None).
        """
        id_batch_chiuso = None
        try:
            cursor = self.conn.cursor()
            # 1. Verifica se esiste un batch aperto/attivo (puo' memorizzare una misurazione)
            cursor.execute(self._SQL_BATCH_ATTIVO)
            risultato = cursor.fetchone()

            if risultato:
                id_batch = risultato["id_batch"]
                num_misurazione_attuale = risultato["numero_misurazioni"]
            else:
                id_batch = self._crea_batch()
                num_misurazione_attuale = 0
            # 2. Prepara dati
            json_dati = json.dumps(dati)
            timestamp_locale = datetime.now().isoformat()
            # 3. Inserisci misurazione
            cursor.execute(
                self._SQL_INSERISCI_MISURAZIONE,
                (id_sensore, id_batch, json_dati, timestamp_locale)
            )

            # 4. Aggiorna batch
            nuovo_num_misurazione = num_misurazione_attuale + 1
            cursor.execute(
                self._SQL_AGGIORNA_BATCH_MISURAZIONI,
                (nuovo_num_misurazione, id_batch)
            )

            # 5. Chiudi batch se necessario
            if nuovo_num_misurazione >= self.soglia_batch:
                cursor.execute(self._SQL_CHIUDI_BATCH, (id_batch,))
                id_batch_chiuso = id_batch

            self.conn.commit()
            return True, id_batch_chiuso

        except sqlite3.Error as e:
            print(f"[ERRORE INSERIMENTO MISURAZIONE] {e}")
            return False, None

    def _crea_batch(self) -> int:
        """
        Crea un nuovo batch e restituisce l'ID generato.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(self._SQL_CREA_BATCH)
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[ERRORE CREAZIONE BATCH] {e}")
            return -1

    # DEBUG ONLY
    def svuota_tabelle(self):
        """
        Elimina tutti i dati da tutte le tabelle del database (reset completo).
        L'ordine delle DELETE è importante per rispettare i vincoli di chiave esterna.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM misurazione")
            cursor.execute("DELETE FROM batch")
            cursor.execute("DELETE FROM sensore")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='misurazione'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='batch'")
            self.conn.commit()
            print("[INFO] Tabelle svuotate e contatori ID resettati.")
        except sqlite3.Error as e:
            print(f"[ERRORE SVUOTAMENTO TABELLE] {e}")

    #DEBUG ONLY
    def drop_tabelle(self):
        """
        Elimina tutte le tabelle del database.
        ATTENZIONE: Questa operazione è distruttiva e irreversibile.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS misurazione")
            cursor.execute("DROP TABLE IF EXISTS batch")
            cursor.execute("DROP TABLE IF EXISTS sensore")
            self.conn.commit()
            print("[INFO] Tutte le tabelle sono state eliminate.")
        except sqlite3.Error as e:
            print(f"[ERRORE DROP TABELLE] {e}")

    def chiudi_connessione(self):
        """Chiude la connessione al database."""
        self.conn.close()
