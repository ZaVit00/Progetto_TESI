import logging
import sqlite3
from datetime import datetime

from costanti_comuni import TipoServizio
from costanti_produttore import DBPATH, SOGLIA_BATCH_MINIMA
from database import query
from database.query import AGGIORNA_CONFERMA_RICEZIONE_SENSORI
from dati_sensore_in_ingresso import DatiSensoreInIngresso
from modelli_dati import DatiSensore, DatiListaSensoriPayload, DatiBatch

from registro_log import setup_logger

logger = setup_logger(TipoServizio.PRODUTTORE, level=logging.DEBUG)


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
            # time out per le transazioni
            self.conn = sqlite3.connect(DBPATH, timeout=10)
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
    def aggiorna_soglia_batch(self, nuova_soglia: int) -> bool:
        """
        “Il sistema consente solo upgrade della soglia e blocca i downgrade.
        Questa scelta architetturale garantisce consistenza dei dati: un batch non può trovarsi in uno
        stato incoerente in cui il numero di misurazioni già raccolte superi la nuova soglia inferiore.
        Tale decisione segue un principio conservativo: meglio rifiutare un’operazione potenzialmente
        dannosa che introdurre complessità e casi ambigui nella logica di gestione dei batch.”
        """
        if not isinstance(nuova_soglia, int) or nuova_soglia <= 0:
            #controllo di sicurezza
            raise ValueError("La soglia deve essere un intero positivo.")

        try:
            cursor = self.conn.cursor()
            cursor.execute("BEGIN IMMEDIATE") # inizio della transazione

            # Verifica se esiste un batch attivo (non completo)
            cursor.execute(query.OTTIENI_BATCH_ATTIVO)
            risultato = cursor.fetchone()
            if risultato:
                #esiste un batch attivo
                soglia_attuale = risultato["soglia_misurazioni"] #soglia attuale del batch attivo
                num_mis_attuale = risultato["numero_misurazioni"] #numero misurazioni attuale

                #caso uguale
                if soglia_attuale == nuova_soglia:
                    #le soglie sono uguali quindi non necessito di fare modifiche
                    logger.debug(f"La soglia è già impostata a {nuova_soglia}, nessuna modifica necessaria.")
                    return True  # niente da modificare

                #caso downgrade
                if nuova_soglia < soglia_attuale:
                    #Problema serio in caso di downgrade della soglia.
                    #Evento possibile e per precauzione vietato.
                    logger.warning(
                        f"Richiesto downgrade della soglia da {soglia_attuale} a {nuova_soglia}. "
                        "Operazione ignorata per garantire consistenza."
                    )
                    return True #niente da modificare

                # Caso upgrade: nuova soglia > soglia_attuale
                # Nessun problema di inconsistenza tra i blocchi di misurazioni
                if nuova_soglia > soglia_attuale:
                    # Aggiorna la soglia del batch attivo
                    cursor.execute("""
                                   UPDATE batch
                                   SET soglia_misurazioni = ?
                                   WHERE completo = 0
                                   """, (nuova_soglia,))

                self.conn.commit()
                logger.info(f"Soglia aggiornata a {nuova_soglia} e batch eventualmente chiuso.")
            else:
                # Nessun batch attivo presente → creane uno nuovo con la soglia indicata
                self.inserisci_batch_se_necessario(nuova_soglia)
                logger.debug(f"Nessun batch attivo: creata nuova tupla con soglia {nuova_soglia}")

            return True

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"Errore durante l'aggiornamento della soglia: {e}")
            return False

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
    def inserisci_batch_se_necessario(self, soglia_misurazioni: int) -> int:
        """
        Crea un nuovo batch solo se non ne esiste già uno attivo (cioè non ancora completo).
        Restituisce l'ID del batch attivo esistente oppure dell'eventuale nuovo batch creato.

        Questo metodo copre due situazioni:
        1) Il batch precedente è stato chiuso -> esiste almeno una tupla esistente nel database
        (che ha raggiunto la soglia).
        2) Il sistema è stato appena avviato e non esiste alcuna tupla nella tabella batch ->
            la tupla del batch va creata all'atto iniziale.

        Nota: la soglia viene aggiornata prima dell'arrivo della prima misurazione,
        perché è calcolata durante la registrazione del sensore quando il sensore
        comunica la propria frequenza di invio. Questo garantisce che
        esista già una soglia valida anche in fase iniziale, prima ancora di accogliere la
        prima misurazione nel sistema.
        """
        try:
            cursor = self.conn.cursor()
            # Verifica se esiste già un batch attivo (completo = 0)
            cursor.execute(query.OTTIENI_BATCH_ATTIVO)
            risultato = cursor.fetchone()

            if risultato:
                # Batch attivo già presente → restituisci l'ID
                id_batch = risultato["id_batch"]
                logger.debug(f"[BATCH ATTIVO] ID esistente: {id_batch}")
            else:
                # Nessun batch attivo → creane uno nuovo
                timestamp_locale = datetime.now().isoformat()
                cursor.execute(query.INSERISCI_BATCH, (timestamp_locale, soglia_misurazioni))
                id_batch = cursor.lastrowid
                logger.info(f"[BATCH NUOVO] Creato batch ID: {id_batch} con soglia: {soglia_misurazioni}")

            self.conn.commit()
            return id_batch

        except sqlite3.Error as e:
            self.conn.rollback()
            logger.error(f"[ERRORE CREAZIONE BATCH] {e}")
            return -1

    def inserisci_misurazione(self, id_sensore: str, dati: str) -> bool:
        """
        Inserisce una nuova misurazione associandola al batch attivo.
        Se la soglia è raggiunta, chiude il batch corrente e ne crea uno nuovo
        con la stessa soglia, continuando l'inserimento.
        :param id_sensore: ID del sensore che ha generato la misurazione.
        :param dati: Dati effettivi della misurazione normalizzata in formato JSON compatto
        """
        timestamp_locale = datetime.now().isoformat()
        try:
            cursor = self.conn.cursor()
            # 1. Verifica l'esistenza del sensore associato alla misurazione
            # Se assente il sensore, vi è una violazione di foreign key
            if not self.verifica_esistenza_sensore(id_sensore):
                logger.warning(f"[MISURAZIONE RIFIUTATA] Sensore '{id_sensore}' non registrato.")
                self.conn.rollback()
                return False

            # 2. Recupera batch attivo; se assente, crea nuovo batch con la soglia più recente
            cursor.execute(query.OTTIENI_BATCH_ATTIVO)
            batch_attivo = cursor.fetchone()

            #non ci sono batch attivi quindi dobbiamo crearlo
            #può accadere perché l'ultima misurazione inserita ha comportato la chisura del batch attivo
            if not batch_attivo:
                logger.info("[NO BATCH ATTIVO] Nessun batch attivo, ne creo uno nuovo.")
                # Recupera la soglia dell’ultimo batch inserito (fallback su soglia minima)
                cursor.execute(query.OTTIENI_SOGLIA_ULTIMO_BATCH)
                risultato = cursor.fetchone()
                #fallback in caso di errori logici da parte del programmatore
                soglia_attuale = risultato["soglia_misurazioni"] if risultato else SOGLIA_BATCH_MINIMA

                #crea il nuovo batch
                id_batch = self.inserisci_batch_se_necessario(soglia_attuale)
                if id_batch == -1:
                    self.conn.rollback()
                    return False

                num_mis_attuali = 0

            else:
                # Batch attivo esistente → estrazione parametri
                id_batch = batch_attivo["id_batch"]
                num_mis_attuali = batch_attivo["numero_misurazioni"]
                soglia_attuale = batch_attivo["soglia_misurazioni"]

            # 3. Se il batch ha raggiunto la soglia, chiudilo e apri un nuovo batch
            if num_mis_attuali >= soglia_attuale:
                cursor.execute(query.CHIUDI_BATCH, (id_batch,))
                logger.info(f"[BATCH CHIUSO] ID batch: {id_batch}")

                id_batch = self.inserisci_batch_se_necessario(soglia_attuale)
                if id_batch == -1:
                    self.conn.rollback()
                    return False
                num_mis_attuali = 0

            # 4. Inserisci la misurazione nel batch attivo
            cursor.execute(
                query.INSERISCI_MISURAZIONE,
                (id_sensore.upper(), id_batch, dati, timestamp_locale)
            )

            # 5. Aggiorna il contatore di misurazioni del batch
            cursor.execute(query.AGGIORNA_BATCH_NUM_MISURAZIONI, (num_mis_attuali + 1, id_batch))
            self.conn.commit()

            logger.info(f"[MISURAZIONE INSERITA] Batch {id_batch} ({num_mis_attuali + 1}/{soglia_attuale})")
            return True

        except sqlite3.OperationalError as e:
            if "cannot start a transaction within a transaction" in str(e):
                logger.error("[LOCK] Transazione già aperta. Potenziale sequenza di chiamate errata.")
            else:
                logger.error(f"[ERRORE INSERIMENTO MISURAZIONE] {e}")
            #self.conn.rollback()
            return False

    def inserisci_dati_sensore(self, sensore : DatiSensoreInIngresso) -> bool:
        """
        Inserisce un nuovo sensore solo se non già presente.
        """
        try:
            cursor = self.conn.cursor()
            #cursor.execute("BEGIN IMMEDIATE")
            cursor.execute(query.INSERISCI_SENSORE, (sensore.id_sensore.upper(),
                                                     sensore.descrizione,
                                                     sensore.tipo,
                                                     sensore.frequenza_hz))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"QUERY - INSERIMENTO SENSORE] {e}")
            return False

    # ------------------------- METODI DI LETTURA -------------------------
    def verifica_esistenza_sensore(self, id_sensore: str) -> bool:
        """
        Verifica se il sensore con l'ID specificato è registrato nel database.
        Restituisce True se esiste, False altrimenti.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.VERIFICA_ESISTENZA_SENSORE, (id_sensore.upper(),))
            if cursor.fetchone() is None:
                logger.warning(f"[MISURAZIONE RIFIUTATA] Sensore '{id_sensore}' non registrato.")
                return False
            else:
                return True

        except sqlite3.Error as e:
            logger.error(f"[ERRORE DB] Verifica esistenza sensore '{id_sensore}': {e}")
            return False

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
            #gestisce un POTENZIALE problema di race condition all'avvio del sistema
            logger.warning("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_ID_BATCH_COMPLETI_DA_ELABORARE)
            risultati = cursor.fetchall()
            #estrai solo gli id_batch e li inserisci in una lista
            return list(riga["id_batch"] for riga in risultati)
        except sqlite3.Error as e:
            logger.error(f"QUERY - LETTURA BATCH NON INVIATI] {e}")
            return []

    def ottieni_sensori_non_conferma_ricezione(self) -> DatiListaSensoriPayload:
        """
        Estrae i sensori registrati localmente che non hanno ancora ricevuto
        conferma di ricezione da parte del cloud provider.
        Restituisce un oggetto DatiListaSensoriPayload.
        """
        if not self.conn:
            #Gestisce un POTENZIALE problema di race condition all'avvio del sistema
            logger.warning("[AVVISO] Connessione al database non attiva. Nessuna query di retry eseguita.")
            return DatiListaSensoriPayload(sensori=[])
        try:
            cursor = self.conn.cursor()
            cursor.execute(query.OTTIENI_SENSORI_NON_CONFERMA_RICEZIONE)
            righe = cursor.fetchall()
            lista = [DatiSensore(**r) for r in righe]
            return DatiListaSensoriPayload(sensori=lista)
        except sqlite3.Error as e:
            logger.error(f"LETTURA SENSORI NON CONFERMATI COME RICEVUTI {e}")
            return DatiListaSensoriPayload(sensori=[])

    def ottieni_payload_batch_pronti_per_invio(self) -> list[tuple[int, str]]:
        """
        Metodo che viene utilizzato dalla classe che gestisce
        il reinvio dei batch completi, il cui payload JSON è pronto per l'invio.
        Restituisce solo i payload dei batch completi (completo = 1)
        ma non ancora inviati (inviato = 0).
        Essendo esecuzioni concorrenti la connessione al database
        potrebbe non essere stata ancora stabilita al momento dell'esecuzione del metodo.
        Se la connessione non è stata stabilita restituisce una lista vuota.
        Nota: in questo caso batch denota la singola tupla del database
        """
        if not self.conn:
            #gestisce un POTENZIALE problema di race condition all'avvio del sistema
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
    #Non utilizzato ma previsto
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





