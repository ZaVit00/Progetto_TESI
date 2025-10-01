import logging
from typing import List
import psycopg2
from psycopg2 import Error as Psycopg2Error
from psycopg2.extras import RealDictCursor
from Classi_comuni.entita.modelli_dati import DatiSensore, DatiMisurazione
from Cloud_provider.database.query import (
    CREA_TABELLA_SENSORE,
    CREA_TABELLA_BATCH,
    CREA_TABELLA_MISURAZIONE,
    INSERISCI_SENSORE,
    INSERISCI_MISURAZIONE,
    INSERISCI_BATCH,
    OTTIENI_DATI_BATCH_MISURAZIONI_SENSORI,
    OTTIENI_METADATA_MISURAZIONE_SENSORE,
    OTTIENI_METADATA_BATCH,
    OTTIENI_DATI_MISURAZIONE_SENSORE,
    OTTIENI_DATA_BATCH,
    OTTIENI_TUTTI_METADATA_BATCH
)
from costanti_comuni import TipoServizio
from dict_utils import serializza_dict
from modelli_dati import DatiBatch
from modelli_metadati import MetadatiBatchPayload
from registro_log import setup_logger

logger = setup_logger(TipoServizio.CLOUD, module=__name__, level=logging.DEBUG)


class GestoreDatabase:
    """
    Classe responsabile della connessione al database PostgreSQL e delle operazioni CRUD
    relative a sensori, misurazioni e batch.
    """

    def __init__(self, db_config: dict):
        """
        Inizializza la connessione al database e crea le tabelle se non esistono.
        """
        try:
            self.conn = psycopg2.connect(**db_config)
            self.conn.autocommit = True
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Connessione a PostgreSQL stabilita.")
            self._crea_tabelle()
        except Psycopg2Error as e:
            logger.error(f"Errore di connessione al database: {e}")
            raise

    def _crea_tabelle(self):
        """
        Metodo privato per creare le tabelle necessarie al sistema.
        Viene invocato automaticamente al momento della connessione.
        """
        try:
            self.cursor.execute(CREA_TABELLA_SENSORE)
            self.cursor.execute(CREA_TABELLA_BATCH)
            self.cursor.execute(CREA_TABELLA_MISURAZIONE)
            logger.info("Tabelle create (se non esistenti).")
        except Psycopg2Error as e:
            logger.error(f"Errore nella creazione delle tabelle: {e}")
            raise

    def inserisci_lista_sensori(self, lista_sensori: List[DatiSensore]) -> List[str]:
        """
        Inserisce una lista di sensori nel database in un'unica operazione.
        Durante l'inserimento, blocca anche le tabelle batch e misurazione.
        In questo modo si aspetta che tutti gli inserimenti di tuple vadano
        a buon fine. Evita problemi di integrità referenziale
        Restituisce gli ID dei sensori elaborati (nuovi o già presenti).
        """
        valori = [(s.id_sensore.upper(), s.descrizione, s.tipo) for s in lista_sensori]

        try:
            # Inizio transazione esplicita con blocco
            self.conn.autocommit = False
            self.cursor.execute("LOCK TABLE sensore, batch, misurazione IN EXCLUSIVE MODE")
            self.cursor.executemany(INSERISCI_SENSORE, valori)
            self.conn.commit()  # Commit esplicito
            logger.info(f"{len(valori)} sensori elaborati.")
            return [s.id_sensore for s in lista_sensori]

        except Psycopg2Error as e:
            self.conn.rollback()  # Rollback se errore
            logger.error(f"Errore nell'inserimento batch dei sensori: {e}")
            return []

        finally:
            self.conn.autocommit = True  # Riattiva autocommit

    def inserisci_dati_batch(self, batch: DatiBatch) -> bool:
        """
        Inserisce un nuovo batch nel database.
        Restituisce True se l'inserimento ha avuto successo, False altrimenti.
        #Questa è la tupla del batch
        """
        try:
            self.cursor.execute(
                INSERISCI_BATCH,
                (batch.id_batch, batch.timestamp_creazione, batch.numero_misurazioni)
            )
            logger.info(f"Batch inserito: {batch.id_batch}")
            return True
        except Psycopg2Error as e:
            logger.error(f"Errore inserimento batch {batch.id_batch}: {e}")
            return False

    def inserisci_dati_misurazioni(self, lista_misurazioni: List[DatiMisurazione]) -> bool:
        """
        Inserisce una lista di misurazioni nel database in un'unica operazione.
        I dati effettivi (campo dati) viene serializzato in JSON prima di essere salvate.
        """
        # Serializzazione dei dati in formato JSON
        valori = [
            (m.id_misurazione, m.id_batch, m.id_sensore, m.timestamp, serializza_dict(m.dati))
            for m in lista_misurazioni
        ]
        try:
            self.cursor.executemany(INSERISCI_MISURAZIONE, valori)
            logger.info(f"{len(valori)} misurazioni inserite per il batch.")
            return True
        except Psycopg2Error as e:
            logger.error(f"Errore nell'inserimento batch delle misurazioni: {e}")
            return False

    def ottieni_dati_batch(self, id_batch) -> DatiBatch | None:
        """
        Estrae la riga completa del batch indicato (potenzialmente manomesso).
        Restituisce un oggetto DatiBatch o None se non trovato.
        #Tupla del batch
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(OTTIENI_DATA_BATCH, (id_batch,))
            riga = cursor.fetchone()
            return DatiBatch(**riga) if riga else None
        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE DATA BATCH] {e}")
            return None

    def ottieni_dati_misurazione_sensore(self, lista_id_mis: List[int]) -> List[dict]:
        """
        Recupera i dati completi (con campo 'dati' già parsato) relativi a una lista di ID misurazione.
        Restituisce una lista di dizionari.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(OTTIENI_DATI_MISURAZIONE_SENSORE, (lista_id_mis,))
            righe = cursor.fetchall()
            logger.info(f"[DB] Richieste {len(lista_id_mis)} misurazioni, recuperate {len(righe)} righe.")
            return righe
        except Psycopg2Error as e:
            logger.error(f"[QUERY - JOIN MULTIPLA] Errore: {e}")
            return []

    def ottieni_dati_batch_misurazioni_sensori(self, id_batch: int) -> list[dict]:
        """
        Recupera tutte le misurazioni associate al batch specificato, ordinate per ID.
        Utilità: ricostruzione merkle tree.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(OTTIENI_DATI_BATCH_MISURAZIONI_SENSORI, (id_batch,))
            righe = cursor.fetchall()
            return [dict(riga) for riga in righe]
        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE DATI BATCH] {e}")
            return []

    def ottieni_metadata_batch(self, id_batch) -> MetadatiBatchPayload | None:
        """
        Estrae i metadati del batch richiesto.
        Restituisce un oggetto MetadatiBatchPayload o None.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(OTTIENI_METADATA_BATCH, (id_batch,))
            riga = cursor.fetchone()
            return MetadatiBatchPayload(**riga) if riga else None
        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE METADATI BATCH] {e}")
            return None

    def ottieni_tutti_metadata_batch(self) -> list[MetadatiBatchPayload]:
        """
        Estrae i metadati di TUTTI i batch presenti nel sistema.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(OTTIENI_TUTTI_METADATA_BATCH)
            righe = cursor.fetchall()
            return [MetadatiBatchPayload(**r) for r in righe]
        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE METADATI TUTTI BATCH] {e}")
            return []

    def ottieni_metadata_misurazione_sensore(self, lista_id_mis: list[int]) -> List[dict] | None:
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            # Costruisci la parte IN con tanti placeholder %s quanti sono gli ID
            placeholders = ','.join(['%s'] * len(lista_id_mis))
            # Prepara la query completa con WHERE IN
            query = f"{OTTIENI_METADATA_MISURAZIONE_SENSORE} WHERE id_misurazione IN ({placeholders})"
            # Esegui la query passando la lista di ID come parametri
            cursor.execute(query, lista_id_mis)
            righe = cursor.fetchall()
            logger.info(f"[DB] Richieste {len(lista_id_mis)} misurazioni, recuperate {len(righe)} righe.")
            return righe

        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE METADATI MISURAZIONE] {e}")
            return None

    def chiudi_connessione(self):
        """
        Chiude in modo sicuro la connessione al database.
        Da chiamare alla fine del ciclo di vita dell’applicazione.
        """
        try:
            if hasattr(self, "cursor") and self.cursor:
                self.cursor.close()
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
            logger.info("Connessione al database chiusa correttamente.")
        except Psycopg2Error as e:
            logger.error(f"Errore durante la chiusura della connessione: {e}")
