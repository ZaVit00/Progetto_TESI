import logging
import sqlite3
from datetime import datetime
from costanti_produttore import DBPATH
from database import query
from database.query import AGGIORNA_CONFERMA_RICEZIONE_SENSORI
from dati_sensore_in_ingresso import DatiSensoreInIngresso
from gestione_soglia_batch import ottieni_soglia_batch
from modelli_dati import DatiSensore, DatiListaSensori, DatiBatch

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

"""
Classe che gestisce tutte le operazioni sul database locale SQLite.
Tutti i metodi catturano internamente le eccezioni e restituiscono
True/False o una lista vuota in caso di errore.
Il chiamante è responsabile nel controllare i valori restituiti.
Tutti gli errori vengono loggati.
"""
class GestoreDatabase:

    def __init__(self, sola_lettura: bool = False):
        if sola_lettura:
            # Connessione in sola lettura (URI necessaria)
            self.conn = sqlite3.connect(f"file:{DBPATH}?mode=ro", uri=True)
        else:
            self.conn = sqlite3.connect(DBPATH)
            self.crea_tabelle()

        self.conn.row_factory = sqlite3.Row

    # ------------------------- CREAZIONE TABELLE -------------------------

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
            logger.error(f"QUERY - CREAZIONE TABELLE] {e}")

    # ------------------------- METODI DI SUPPORTO INTERNI -------------------------
    def _inserisci_batch(self) -> int:
        """
        Crea un nuovo batch e restituisce l'ID associato (campo autoincrement)
        """
        try:
            cursor = self.conn.cursor()
            timestamp_locale = datetime.now().isoformat()
            cursor.execute(query.INSERISCI_BATCH, (timestamp_locale,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"QUERY - CREAZIONE BATCH] {e}")
            return -1

    def chiudi_connessione(self) -> None:
        """
        Chiude la connessione al database, se ancora aperta.
        """
        try:
            if self.conn:
                self.conn.close()
                logger.info("Connessione al database chiusa correttamente.")
        except Exception as e:
            logger.error(f"Errore durante la chiusura della connessione al database: {e}")


    # ------------------------- METODI DI INSERIMENTO -------------------------
    def inserisci_dati_sensore(self, sensore : DatiSensoreInIngresso) -> bool:
        """
        Inserisce un nuovo sensore solo se non già presente.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.INSERISCI_SENSORE, (sensore.id_sensore.upper(),
                                                     sensore.descrizione,
                                                     sensore.tipo,
                                                     sensore.frequenza_hz))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - INSERIMENTO SENSORE] {e}")
            return False

    def inserisci_misurazione(self, id_sensore: str, dati: str) -> bool:
        """
        Inserisce una nuova misurazione in ingresso associandola al batch attivo.

        - Se non esiste alcun batch attivo, ne viene creato uno nuovo.
        - Se il batch corrente ha raggiunto la soglia di completamento, viene chiuso e ne viene creato uno nuovo.
        - La misurazione viene registrata solo se il sensore corrispondente è presente nel sistema.

        Returns:
            bool: True se l'inserimento va a buon fine, False in caso di errore o se il sensore non è registrato.
        """
        try:
            cursor = self.conn.cursor()

            # Verifica preliminare che il sensore associato alla misurazione esista nel database
            cursor.execute(query.VERIFICA_ESISTENZA_SENSORE, (id_sensore,))
            if cursor.fetchone() is None:
                logger.warning(f"[MISURAZIONE RIFIUTATA] Sensore '{id_sensore}' non registrato.")
                return False

            # Recupera il batch attivo (se presente)
            cursor.execute(query.OTTIENI_BATCH_ATTIVO)
            risultato = cursor.fetchone()

            if risultato:
                # Un batch attivo esiste già
                id_batch = risultato["id_batch"]
                num_misurazione_attuale = risultato["numero_misurazioni"]

                # Recupera la soglia attuale per questo batch
                if num_misurazione_attuale >= ottieni_soglia_batch():
                    # Batch già oltre soglia → chiusura immediata
                    cursor.execute(query.CHIUDI_BATCH, (id_batch,))
                    logger.info(f"[BATCH CHIUSO] ID batch: {id_batch}")
                    # Creazione nuovo batch
                    id_batch = self._inserisci_batch()
                    num_misurazione_attuale = 0

            else:
                # Nessun batch attivo → creazione nuovo batch
                id_batch = self._inserisci_batch()
                num_misurazione_attuale = 0
                logger.debug(f"[BATCH NUOVO] Creato batch ID: {id_batch}")

            logger.debug(
                f"[BATCH ATTIVO] ID: {id_batch} - {num_misurazione_attuale}/{ottieni_soglia_batch()} misurazioni")

            # Inserisce la misurazione nel batch corrente
            timestamp_locale = datetime.now().isoformat()
            cursor.execute(
                query.INSERISCI_MISURAZIONE,
                (id_sensore, id_batch, dati, timestamp_locale)
            )

            # Aggiorna il contatore delle misurazioni nel batch
            nuovo_num = num_misurazione_attuale + 1
            cursor.execute(query.AGGIORNA_BATCH_NUM_MISURAZIONI, (nuovo_num, id_batch))

            # Conferma tutte le modifiche nel database
            self.conn.commit()
            return True

        except sqlite3.Error as e:
            logger.error(f"[QUERY - INSERIMENTO MISURAZIONE] {e}")
            return False

    # ------------------------- METODI DI LETTURA -------------------------
    def ottieni_dati_sensore(self, id_sensore) -> DatiSensore | None:
        """
        Recupera i dati associati a un sensore registrato, dato il suo ID.

        - Esegue una query per ottenere tutte le informazioni relative al sensore.
        - Se il sensore non è presente nel database, restituisce `None`.
        - Se trovato, restituisce un oggetto `DatiSensore` costruito dai risultati.

        Returns:
            DatiSensore | None: oggetto con i dati del sensore, oppure None se non trovato o in caso di errore.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_DATI_SENSORI, (id_sensore,))
            ris = cursor.fetchone()
            if ris is None:
                logger.warning(f"Sensore con ID '{id_sensore}' non trovato.")
                return None
            return DatiSensore(**ris)
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA DATI SENSORI] {e}")
            return None

    def ottieni_dati_batch(self, id_batch) -> DatiBatch | None:
        """
       Recupera dal database tutte le informazioni relative a un batch specifico.

       - Esegue una query sulla tabella dei batch utilizzando l'ID fornito.
       - Se il batch non esiste, restituisce `None`.
       - In caso positivo, costruisce e restituisce un oggetto `DatiBatch` con i dati recuperati.

       Returns:
           DatiBatch | None: oggetto rappresentante il batch, oppure None se non trovato o in caso di errore.
       """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_DATI_BATCH, (id_batch,))
            ris = cursor.fetchone()
            if ris is None:
                logger.warning(f"Batch con ID '{id_batch}' non trovato.")
                return None
            return DatiBatch(**ris)
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA FREQUENZA MEDIA BATCH] {e}")
            return None


    def ottieni_frequenza_media_sensori(self) -> float:
        """
        Calcola e restituisce la frequenza media (in Hz) di tutti i sensori registrati nel sistema.
        Utile per stimare il tasso medio di produzione dati nel fog node.

        Returns:
            float: valore medio della frequenza (Hz). Se non ci sono sensori, restituisce 0.0.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_FREQUENZA_MEDIA_SENSORI)
            risultato = cursor.fetchone()
            if risultato is None or risultato[0] is None:
                # logger.warning("Nessuna frequenza trovata nella tabella 'sensore'.")
                return 0.0
            return float(risultato[0])
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA FREQUENZA MEDIA SENSORI] {e}")
            return 0.0

    def ottieni_payload_batch(self, id_batch) -> str | None:
        """
        Recupera il payload JSON completo associato a un determinato batch.

        - Il payload contiene i dati aggregati del batch, già pronti per l'invio al cloud o per la verifica.
        - Se il batch non esiste o non è stato ancora elaborato, restituisce `None`.

        Args:
            id_batch (int): ID del batch di cui si vuole ottenere il payload.

        Returns:
            str | None: Stringa JSON del payload, oppure None se il batch non è presente o si verifica un errore.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_PAYLOAD_BATCH, (id_batch,))
            ris = cursor.fetchone()
            if ris is None:
                logger.warning(f"Payload batch con ID '{id_batch}' non trovato.")
                return None
            return ris["payload_json"]
        except sqlite3.Error as e:
            logger.error(f"[QUERY - LETTURA PAYLOAD BATCH]: {e}")
            return None


    def ottieni_dati_batch_misurazioni_sensori(self, id_batch: int) -> list[dict]:
        """
        Estrae tutte le misurazioni associate a un batch, ordinate per ID crescente.
        Questo metodo è pensato per supportare la verifica dell'integrità e la costruzione del Merkle Tree.
        A causa della complessità e dell'importanza dell'operazione, la creazione degli oggetti Pydantic
        è delegata a un metodo esterno dedicato.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_DATI_BATCH_MISURAZIONI_SENSORI, (id_batch,))
            righe = cursor.fetchall()
            #.fetchall() restituisce una lista di sqlite3.Row, che sembrano dizionari, ma non lo sono al 100%.
            # Se serve una lista di dizionari veri, fai righe = [dict(r) for r in cursor.fetchall()].
            return [dict(riga) for riga in righe]
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA DATI BATCH] {e}")
            return []

    # ------------------------- METODI DI LETTURA UTILIZZATI DA TASK DI RETRY  -------------------------
    def ottieni_id_batch_completi(self) -> list[int]:
        """
        Restituisce tutti i batch completi = 1 che necessitano di elaborazione:
        aggregazione, creazione merkle tree etc, e, che inviato = 0.
        Se la connessione al database non è disponibile, restituisce una lista vuota
        senza sollevare eccezioni. Metodo che viene utilizzato dalla classe che gestisce
        la elaborazione periodica dei batch completi.
        """
        if not self.conn:
            logger.warning("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_ID_BATCH_COMPLETI_DA_ELABORARE)
            risultati = cursor.fetchall()
            #estrai solo i primi elementi e li inserisci in una lista
            return list(riga[0] for riga in risultati)
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA BATCH NON INVIATI] {e}")
            return []

    def ottieni_sensori_non_conferma_ricezione(self) -> DatiListaSensori:
        """
        Estrae i sensori registrati localmente che non hanno ancora ricevuto
        conferma di registrazione da parte del cloud provider.
        Restituisce un oggetto DatiListaSensori.
        """
        if not self.conn:
            logger.warning("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return DatiListaSensori(sensori=[])

        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_SENSORI_NON_CONFERMA_RICEZIONE)
            righe = cursor.fetchall()
            lista = [DatiSensore(**r) for r in righe]
            return DatiListaSensori(sensori=lista)
        except sqlite3.Error as e:
            logger.error(f"LETTURA SENSORI NON CONFERMATI COME RICEVUTI {e}")
            return DatiListaSensori(sensori=[])

    def ottieni_payload_batch_pronti_per_invio(self) -> list[tuple[int, str]]:
        """
        Metodo che viene utilizzato dalla classe che gestisce
        il reinvio dei batch completi, il cui payload JSON è pronto per l'invio.
        Restituisce solo i payload dei batch completi (completo = 1)
        ma non ancora inviati (inviato = 0). Essendo esecuzioni concorrenti la connessione al database
        potrebbe non essere stata ancora stabilita al momento dell'esecuzione del metodo.
        Se la connessione non è stata stabilita restituisce una lista vuota.
        """
        if not self.conn:
            logger.warning("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_PAYLOAD_BATCH_PRONTI_PER_INVIO)
            risultati = cursor.fetchall()
            return [(r["id_batch"], r["payload_json"]) for r in risultati]
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA BATCH NON INVIATI] {e}")
            return []

    # ------------------------- METODI DI AGGIORNMENTO -------------------------
    def aggiorna_metadata_batch(self, id_batch : int, merkle_root : str,
                                cid_merkle_path : str, payload_json : str) -> bool:
        """
        Aggiorna la Merkle Root, CID_IPFS e payload JSON del batch una volta
        che è stato elaborato correttamente durante la pipeline.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_METADATA_BATCH, (
                merkle_root, cid_merkle_path, payload_json, id_batch))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - AGGIORNAMENTO METADATI IN BATCH] {e}")
            return False

    def aggiorna_batch_conferma_ricezione(self, id_batch: int) -> bool:
        """
        Imposta il flag 'inviato' del batch a 1 dopo l'invio riuscito.
        ATTENZIONE: solo un batch completato può essere segnato come confermato
        dalla destinazione. Se il batch non è stato ancora completato non può essere
        stato inviato
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_BATCH_CONFERMA_RICEZIONE, (id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - AGGIORNAMENTO STATO INVIO BATCH] {e}")
            return False

    def aggiorna_batch_errore_elaborazione(self, id_batch: int, messaggio_errore: str, tipo_errore: str) -> bool:
        """
        Segna un batch come impossibile da elaborare in seguito a errore grave
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_ERRORE_ELABORAZIONE_BATCH, (
                messaggio_errore, tipo_errore, id_batch))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - SEGNA BATCH NON ELABORABILE ERRORE] {e}")
            return False

    def aggiorna_conferma_ricezione_batch(self, id_batch: int) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_CONFERMA_RICEZIONE_BATCH, (id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - AGGIORNA CONFERMA RICEZIONE BATCH] {e}")
            return False

    def aggiorna_transazione_hash_batch(self, id_batch: int, tx_hash : str) -> bool:
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.AGGIORNA_TRANSAZIONE_HASH_BATCH, (tx_hash, id_batch,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - AGGIORNA HASH TRANSAZIONE BATCH] {e}")
            return False

    def aggiorna_conferma_ricezione_sensori(self, id_sensori: list[str]) -> bool:
        """
        Aggiorna il campo 'conferma_ricezione' per una lista di sensori.
        Costruisce dinamicamente la query con i placeholder necessari.
        """
        if not id_sensori:
            return False

        try:
            cursor = self.conn.cursor()
            # Genera i placeholder SQL (?, ?, ?, ...) per il numero di sensori
            placeholders = ", ".join("?" for _ in id_sensori)
            # Inserisce i placeholder nella query predefinita
            query_sql = AGGIORNA_CONFERMA_RICEZIONE_SENSORI.format(placeholders=placeholders)
            # Esegue la query con tutti gli ID
            cursor.execute(query_sql, id_sensori)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"[QUERY - AGGIORNA CONFERMA RICEZIONE SENSORI MULTIPLI] {e}")
            return False

    # ------------------------- METODI DI ELIMINAZIONE -------------------------
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
            logger.error(f"QUERY - ELIMINAZIONE MISURAZIONI] {e}")
            return False





