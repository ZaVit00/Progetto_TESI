import psycopg2
import logging
import query

logger = logging.getLogger(__name__)

class DbManager:
    def __init__(self, db_config):
        self.conn = psycopg2.connect(**db_config)
        self.conn.autocommit = True

    def inserisci_sensore(self, id_sensore : str, descrizione : str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                query.INSERISCI_SENSORE,
                (id_sensore, descrizione)
            )
            self.conn.commit()
            return True
        except psycopg2.Error as e:
            logger.error(f"[QUERY - INSERIMENTO SENSORE] {e}")
            return False
