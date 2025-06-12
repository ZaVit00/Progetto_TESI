import os
import sqlite3
import json
from datetime import datetime
from typing import List

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
        self.crea_tabelle()
        self.soglia_batch = soglia_batch

    def crea_tabelle(self):
        """
        Crea le tabelle sensore, batch e misurazione_in_ingresso nel database, se non esistono.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.PRAGMA_FK)
            cursor.execute(query.CREA_TABELLA_SENSORE)
            cursor.execute(query.CREA_TABELLA_BATCH)
            cursor.execute(query.CREA_TABELLA_MISURAZIONE)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - CREAZIONE TABELLE] {e}")

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
            print(f"[ERRORE QUERY - INSERIMENTO SENSORE] {e}")
            return False

    def inserisci_misurazione(self, id_sensore: str, dati: dict) -> tuple[bool, int | None]:
        """
        Inserisce una misurazione_in_ingresso associata al batch attivo.
        Se non esiste un batch non completato, ne crea uno.
        Restituisce (True, id_batch_chiuso) se tutto va a buon fine,
        altrimenti (False, None).
        """
        id_batch_chiuso = None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.BATCH_ATTIVO)
            risultato = cursor.fetchone()

            if risultato:
                id_batch = risultato["id_batch"]
                num_misurazione_attuale = risultato["numero_misurazioni"]
            else:
                id_batch = self._crea_batch()
                num_misurazione_attuale = 0

            json_dati = json.dumps(dati)
            timestamp_locale = datetime.now().isoformat()

            cursor.execute(query.INSERISCI_MISURAZIONE,
                (id_sensore, id_batch, json_dati, timestamp_locale)
            )

            nuovo_num_misurazione = num_misurazione_attuale + 1
            cursor.execute(
                query.AGGIORNA_BATCH_NUM_MISURAZIONI,
                (nuovo_num_misurazione, id_batch)
            )

            if nuovo_num_misurazione >= self.soglia_batch:
                cursor.execute(query.CHIUDI_BATCH, (id_batch,))
                id_batch_chiuso = id_batch

            self.conn.commit()
            return True, id_batch_chiuso

        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - INSERIMENTO MISURAZIONE] {e}")
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
            print(f"[ERRORE QUERY - CREAZIONE BATCH] {e}")
            return -1

    def estrai_dati_batch_misurazioni(self, id_batch: int) -> list[dict]:
        """
        Estrae tutte le misurazioni associate a un batch ordinandole per ID.
        Utile per la verifica dell'integrità e la costruzione del Merkle Tree.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.ESTRAI_DATI_BATCH_MISURAZIONI, (id_batch,))
            righe = cursor.fetchall()
            return [dict(riga) for riga in righe]
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - ESTRAZIONE DATI BATCH] {e}")
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
            print(f"[ERRORE QUERY - AGGIORNAMENTO PAYLOAD JSON IN BATCH] {e}")
            return False

    def aggiorna_payload_json_batch(self, id_batch: int, payload_json: str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                query.AGGIORNA_PAYLOAD_JSON_BATCH,
                (payload_json, id_batch)  # << ordine corretto dei parametri
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - AGGIORNAMENTO PAYLOAD JSON IN BATCH] {e}")
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
            print(f"[ERRORE QUERY - ELIMINAZIONE MISURAZIONI] {e}")
            return False

    def imposta_batch_conferma_ricezione(self, id_batch: int) -> bool:
        """
        Imposta il flag 'inviato' del batch a 1 dopo l'invio riuscito.
        ATTENZIONE: solo un batch completato può essere segnato come confermato
        dalla destinazione. Se il batch non è stato ancora completato non può essere
        stato inviato
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.IMPOSTA_BATCH_CONFERMA_RICEZIONE, (id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - AGGIORNAMENTO STATO INVIO BATCH] {e}")
            return False

    def get_payload_batch_non_inviati(self) -> list[dict]:
        """
        Restituisce tutti i batch completati (completato = 1) ma non ancora inviati (inviato = 0).
        Se la connessione al database non è disponibile, restituisce una lista vuota
        senza sollevare eccezioni.
        """
        if not self.conn:
            print("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.BATCH_NON_INVIATI)
            risultati = cursor.fetchall()
            return [riga["payload_json"] for riga in risultati]
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - LETTURA BATCH NON INVIATI] {e}")
            return []

    def segna_batch_errore(self, id_batch: int, messaggio_errore: str, tipo_errore: str) -> None:
        """
        Segna un batch come impossibile da elaborare in seguito a errore grave
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.IMPOSTA_ERRORE_ELABORAZIONE_BATCH, (messaggio_errore, tipo_errore, id_batch))
            self.conn.commit()
            print(f"[INFO] Batch {id_batch} marcato come non elaborabile. Errore: {tipo_errore}")
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - SEGNA BATCH ERRORE] {e}")

    def estrai_batch_incompleti(self) -> List[int]:
        """
        Restituisce gli ID dei batch completati ma interrotti (mancano Merkle Root e payload),
        che possono essere rielaborati perché ancora marcati come elaborabili.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.BATCH_ELABORALABILI_NON_COMPLETATI)
            #estrai l'id del batch elaborabile, ma senza merkle root e payload JSON
            #Gestisci casi in cui si verificano eccezioni con il database
            return [riga["id_batch"] for riga in cursor.fetchall()]
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - BATCH INCOMPLETI] {e}")
            return []


    #DEBUG ONLY
    def svuota_tabelle(self):
        """
        Elimina tutti i dati da tutte le tabelle del database (reset completo).
        L'ordine delle DELETE è importante per rispettare i vincoli di chiave esterna.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM misurazione_in_ingresso")
            cursor.execute("DELETE FROM batch")
            cursor.execute("DELETE FROM sensore")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='misurazione_in_ingresso'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='batch'")
            self.conn.commit()
            print("[INFO] Tabelle svuotate e contatori ID resettati.")
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - SVUOTAMENTO TABELLE] {e}")

    def drop_tabelle(self):
        """
        Elimina tutte le tabelle del database.
        ATTENZIONE: Questa operazione è distruttiva e irreversibile.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS misurazione_in_ingresso")
            cursor.execute("DROP TABLE IF EXISTS batch")
            cursor.execute("DROP TABLE IF EXISTS sensore")
            self.conn.commit()
            print("[INFO] Tutte le tabelle sono state eliminate.")
        except sqlite3.Error as e:
            print(f"[ERRORE QUERY - DROP TABELLE] {e}")

    def chiudi_connessione(self) -> None:
        """Chiude la connessione al database, se ancora aperta."""
        try:
            if self.conn:
                self.conn.close()
                print("[INFO] Connessione al database chiusa correttamente.")
        except Exception as e:
            print(f"[ERRORE] Errore durante la chiusura della connessione al database: {e}")
