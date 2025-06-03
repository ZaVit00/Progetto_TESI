import os
import sqlite3
import json
from datetime import datetime
from database import query

class GestoreDatabase:
    # Trova la directory root del progetto (2 livelli sopra gestore_db.py)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _DBPATH = os.path.join(BASE_DIR, "dati_temporanei.sqlite")
    _STRING_MAX_LENGTH = 12

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
        #print("[DEBUG] Creo tabelle sensore, batch, misurazione...")
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.PRAGMA_FK)
            cursor.execute(query.CREA_TABELLA_SENSORE)
            cursor.execute(query.CREA_TABELLA_BATCH)
            cursor.execute(query.CREA_TABELLA_MISURAZIONE)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[ERRORE DATABASE] {e}")

    def inserisci_dati_sensore(self, id_sensore: str, descrizione: str) -> bool:
        """
        Inserisce un nuovo sensore solo se non già presente.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.INSERISCI_SENSORE, (id_sensore, descrizione))
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
            cursor.execute(query.BATCH_ATTIVO)
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
            cursor.execute(query.INSERISCI_MISURAZIONE,
                (id_sensore, id_batch, json_dati, timestamp_locale)
            )

            # 4. Aggiorna batch
            nuovo_num_misurazione = num_misurazione_attuale + 1
            cursor.execute(
                query.AGGIORNA_BATCH_NUM_MISURAZIONI,
                (nuovo_num_misurazione, id_batch)
            )

            # 5. Chiudi batch se necessario
            if nuovo_num_misurazione >= self.soglia_batch:
                cursor.execute(query.CHIUDI_BATCH, (id_batch,))
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
            timestamp_locale = datetime.now().isoformat()
            cursor.execute(query.CREA_BATCH, (timestamp_locale,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[ERRORE CREAZIONE BATCH] {e}")
            return -1

    def estrai_dati_batch(self, id_batch: int) -> list[dict]:
        """
        Estrae tutte le misurazioni associate a un batch ordinandole per ID.
        Utile per la verifica dell'integrità e la costruzione del Merkle Tree.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.ESTRAI_DATI_BATCH, (id_batch,))
            righe = cursor.fetchall()
            #converti le righe in dizionari
            #ogni elemento del dict è una riga estratta
            return [dict(riga) for riga in righe]
        except sqlite3.Error as e:
            print(f"[ERRORE ESTRAZIONE DATI BATCH] {e}")
            return []

    def aggiorna_merkle_root_batch(self, id_batch_chiuso, merkle_root) -> bool:
        """
           Aggiorna la Merkle Root del batch una volta completato.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_MERKLE_ROOT_BATCH, (merkle_root, id_batch_chiuso))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE AGGIORAMENTO MERKLE ROOT IN BATCH] {e}")
            return False

    def elimina_misurazioni_batch(self, id_batch: int) -> bool:
        """
        Elimina tutte le misurazioni associate a un determinato
        batch, solo quando il batch è stato chiuso ed è pronto
        per l'invio
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.ELIMINA_MISURAZIONI, (id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE ELIMINAZIONE MISURAZIONI] {e}")
            return False

    def imposta_batch_inviato(self, id_batch: int) -> bool:
        """
        Imposta il flag 'inviato' del batch a 1 dopo l'invio riuscito.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.IMPOSTA_BATCH_INVIATO, (id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE AGGIORNAMENTO STATO INVIO BATCH] {e}")
            return False

    def get_batch_non_inviati(self) -> list[dict]:
        """
        Restituisce tutti i batch completati (completato = 1) ma non ancora inviati (inviato = 0).
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.BATCH_NON_INVIATI)
            risultati = cursor.fetchall()
            return [dict(riga) for riga in risultati]
        except sqlite3.Error as e:
            print(f"[ERRORE LETTURA BATCH NON INVIATI] {e}")
            return []

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


