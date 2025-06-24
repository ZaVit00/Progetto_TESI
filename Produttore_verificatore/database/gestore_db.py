import os
import json
import sqlite3
import logging

from database.query import RECUPERA_DATI_BATCH
from modelli_dati import DatiBatch, DatiMisurazione
from query import ESTRAI_METADATA_MISURAZIONE

logger = logging.getLogger(__name__)

class GestoreDatabase:
    """
    Gestore DB solo per operazioni in sola lettura su dati del produttore.
    """
    def __init__(self):
        # Percorso dinamico: sali di uno, entra in 'produttore', poi apri il DB
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "produttore"))
        db_path = os.path.join(base_dir, "dati_fog_node.sqlite")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def recupera_dati_batch(self, id_batch: int) -> DatiBatch | None:
        """
        Recupera la tupla batch
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(RECUPERA_DATI_BATCH,(id_batch,))
            riga = cursor.fetchone()
            if riga is None:
                return None
            return DatiBatch(**dict(riga))
        except sqlite3.Error as e:
            logger.error(f"[QUERY - RECUPERO DATI BATCH] {e}")
            return None

    def recupera_dati_misurazione(self, id_misurazione: int) -> DatiMisurazione | None:
        """
        Recupera la tupla misurazione + campo dati già deserializzato.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(ESTRAI_METADATA_MISURAZIONE, (id_misurazione,))
            riga = cursor.fetchone()
            if riga is None:
                return None
            dati_dict = json.loads(riga["dati"])
            return DatiMisurazione(
                id_misurazione=riga["id_misurazione"],
                id_batch=riga["id_batch"],
                id_sensore=riga["id_sensore"],
                dati=dati_dict,
                timestamp=riga["timestamp"],
            )
        except sqlite3.Error as e:
            logger.error(f"[QUERY - RECUPERO DATI MISURAZIONE] {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"[ERRORE JSON - DATI MISURAZIONE] {e}")
            return None

    def chiudi(self):
        """
        Chiude la connessione al database, se ancora aperta.
        """
        try:
            if self.conn:
                self.conn.close()
        except sqlite3.Error as e:
            logger.error(f"[ERRORE CHIUSURA CONNESSIONE] {e}")
