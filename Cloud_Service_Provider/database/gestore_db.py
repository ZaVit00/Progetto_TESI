import json
import logging
import psycopg2
from psycopg2 import Error as Psycopg2Error
from psycopg2.extras import RealDictCursor
from Classi_comuni.entita.modelli_dati import DatiSensore, DatiMisurazione, DatiBatch, MetaDatiBatch
from Cloud_Service_Provider.database.query import (
    CREA_TABELLA_SENSORE,
    CREA_TABELLA_BATCH,
    CREA_TABELLA_MISURAZIONE,
    INSERISCI_SENSORE,
    INSERISCI_MISURAZIONE,
    INSERISCI_BATCH,
    ESTRAI_DATI_BATCH_MISURAZIONI_SENSORI, ESTRAI_METADATA_MISURAZIONE, ESTRAI_METADATA_BATCH,
    ESTRAI_DATI_MISURAZIONI_SENSORI
)
from modelli_dati import MetaDatiMisurazione

logger = logging.getLogger(__name__)

class GestoreDatabase:
    def __init__(self, db_config: dict):
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


    def inserisci_sensore(self, sensore: DatiSensore) -> bool:
        """
        Inserisce un nuovo sensore nel database.
        """
        try:
            self.cursor.execute(
                INSERISCI_SENSORE,
                (sensore.id_sensore, sensore.descrizione, sensore.tipo)
            )
            logger.info(f"Sensore inserito: {sensore.id_sensore}")
            return True
        except Psycopg2Error as e:
            logger.error(f"Errore inserimento sensore {sensore.id_sensore}: {e}")
            return False

    def inserisci_batch(self, batch: DatiBatch) -> bool:
        """
        Inserisce un nuovo batch nel database.
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

    def inserisci_misurazione(self, misurazione: DatiMisurazione, id_batch: int) -> bool:
        """
        Inserisce una singola misurazione nel database.
        """
        try:
            self.cursor.execute(
                INSERISCI_MISURAZIONE,
                (
                    misurazione.id_misurazione,
                    id_batch,
                    misurazione.id_sensore,
                    misurazione.timestamp,
                    #misurazione.dati è un Dict (ad esempio: {"x": 10, "y": 5, "pressed": True})
                    # json.dumps(...) lo trasforma in una stringa JSON: '{"x": 10, "y": 5, "pressed": true}'
                    #questa stringa può essere salvata in PostgreSQL in una colonna JSON o TEXT
                    json.dumps(misurazione.dati)
                )
            )
            logger.info(f"Misurazione inserita: {misurazione.id_misurazione}")
            return True
        except Psycopg2Error as e:
            logger.error(f"Errore inserimento misurazione {misurazione.id_misurazione}: {e}")
            return False

    def estrai_dati_batch_misurazioni_sensori(self, id_batch: int) -> list[dict]:
        """
        Estrae tutte le misurazioni associate a un batch ordinandole per ID.
        Utile per la verifica dell'integrità e la costruzione del Merkle Tree.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(ESTRAI_DATI_BATCH_MISURAZIONI_SENSORI, (id_batch,))
            righe = cursor.fetchall()
            #.fetchall() restituisce una lista di Row, che sembrano dizionari, ma non lo sono al 100%.
            # Se ti serve una lista di dizionari veri,
            # fai righe = [dict(r) for r in cursor.fetchall()].
            return [dict(riga) for riga in righe]
        except Psycopg2Error as e:
            logger.error(f"QUERY - ESTRAZIONE DATI BATCH] {e}")
            return []

    def estrai_metadata_misurazione(self, id_misurazione: int) -> MetaDatiMisurazione | None:
        """
        Estrae i metadati associati a una singola misurazione, potenzialmente manomessi.
        Restituisce un dizionario oppure None se la riga non esiste o in caso di errore.
        """

        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(ESTRAI_METADATA_MISURAZIONE, (id_misurazione,))
            riga = cursor.fetchone()
            if not riga:
                raise ValueError(f"Nessuna misurazione trovata con ID {id_misurazione}")
            return MetaDatiMisurazione(**riga)

        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE METADATI MISURAZIONE] {e}")
            return None

    def estrai_metadata_batch(self, id_batch) -> MetaDatiBatch | None:
        """
        Estrae i metadata associati alla tupla del batch, potenzialmente manomesso.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(ESTRAI_METADATA_BATCH, (id_batch,))
            riga = cursor.fetchone()
            if not riga:
                raise ValueError(f"Nessuna tupla batch trovata con ID {id_batch}")
            return MetaDatiBatch(**riga)

        except Psycopg2Error as e:
            logger.error(f"[QUERY - ESTRAZIONE METADATI BATCH] {e}")
            return None

    from typing import Tuple
    from modelli_dati import DatiMisurazione, DatiSensore

    def estrai_dati_misurazione_sensore(self, id_misurazione: int) -> Tuple[DatiMisurazione, DatiSensore] | None:
        """
        Restituisce una tupla (DatiMisurazione, DatiSensore) corrispondente a una misurazione specifica.
        """
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(ESTRAI_DATI_MISURAZIONI_SENSORI, (id_misurazione,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Nessuna tupla misurazione trovata con ID {id_misurazione}")

        except Psycopg2Error as e:
            logger.error(f"[QUERY - JOIN MISURAZIONE + SENSORE] {e}")
            return None

        # Parsing del campo "dati"
        try:
            dati_dict = json.loads(row["dati"]) if isinstance(row["dati"], str) else row["dati"]
        except json.JSONDecodeError as e:
            logger.error(f"[ERRORE JSON - CAMPO 'dati' MISURAZIONE] {e}")
            return None

        # Costruzione degli oggetti
        mis = DatiMisurazione(
            id_misurazione=row["id_misurazione"],
            id_batch=row["id_batch"],
            id_sensore=row["id_sensore"],
            dati=dati_dict,
            timestamp=row["timestamp"]
        )

        sens = DatiSensore(
            id_sensore=row["m.id_sensore"],
            tipo=row["tipo"],
            descrizione=row["descrizione"],
        )

        return mis, sens

    def chiudi_connessione(self):
        """
        Chiude la connessione al database PostgreSQL in modo sicuro.
        Da chiamare durante la fase di shutdown dell'applicazione.
        """
        try:
            # Verifica che l'attributo esista prima di tentare la chiusura,
            # per evitare errori se la connessione non è mai stata creata correttamente
            if hasattr(self, "cursor") and self.cursor:
                self.cursor.close()
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
            logger.info("Connessione al database chiusa correttamente.")
        except Psycopg2Error as e:
            logger.error(f"Errore durante la chiusura della connessione: {e}")






