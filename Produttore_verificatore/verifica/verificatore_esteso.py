import logging
from typing import List

from Produttore_verificatore.api_client.api_cloud import (
    richiedi_dato_cloud_batch,
    richiedi_dati_cloud_completi_misurazioni
)
from modelli_dati import (
    DatiBatch,
    DatiMisurazioneSensore,
)
from verificatore import Verificatore
from Produttore.database.gestore_db import GestoreDatabase
from recupero_dati_utils import (
    carica_payload_json,
    estrai_lista_id_sensori_dal_payload,
    estrai_dati_sensori_locali,
    filtra_misurazioni_alterate,
    ricostruisci_misurazioni_sensore,
    confronta_dati_batch,
    confronta_dati_misurazioni_sensori
)

# Configurazione logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VerificatoreEsteso(Verificatore):
    """
    Estensione del verificatore base per confrontare i dati locali e cloud
    in caso di rilevata alterazione.
    """

    def __init__(self, id_batch: int):
        logger.info(f"Inizializzazione VerificatoreEsteso per batch ID {id_batch}")
        super().__init__(id_batch)
        self.gestore_db = GestoreDatabase(sola_lettura=True)

    def _recupera_dati_cloud_batch(self) -> DatiBatch:
        """
        Recupera i dati del batch dal cloud solo se il batch è alterato.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch non risulta alterato. Nessun dato da recuperare.")
        logger.info("Recupero dati batch alterato dal cloud")
        batch = richiedi_dato_cloud_batch(self.id_batch)
        logger.debug(f"Dati batch cloud ricevuti: {batch}")
        return batch

    def _recupera_dati_locali_batch(self) -> DatiBatch:
        """
        Recupera i dati del batch dal database locale.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch risulta integro. Nessun dato da recuperare.")
        logger.info("Recupero dati batch alterato dal database locale")
        batch = self.gestore_db.ottieni_dati_batch(self.id_batch)
        if not batch:
            raise ValueError(f"Nessun batch trovato nel database locale con ID {self.id_batch}")
        logger.debug(f"Dati batch locale ottenuti: {batch}")
        return batch

    def _recupera_dati_cloud_misurazioni_sensore(
            self, id_mis_alterati: List[int]
    ) -> List[DatiMisurazioneSensore]:
        """
        Recupera le misurazioni alterate (e relativi dati sensore) dal cloud.
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione alterata. Nessun dato da recuperare.")
        logger.info("Recupero misurazioni alterate + dati sensori dal cloud")
        misurazioni = richiedi_dati_cloud_completi_misurazioni(id_mis_alterati)
        logger.debug(f"Misurazioni cloud ricevute: {misurazioni}")
        return misurazioni

    def _recupera_dati_locali_misurazioni(self) -> List[DatiMisurazioneSensore]:
        """
        Ricostruisce localmente le misurazioni alterate dal payload JSON e dal database.
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione alterata. Nessun dato da recuperare.")

        id_alterati = set(self.ottieni_id_misurazioni_alterate())
        logger.info("Caricamento payload locale e ricostruzione misurazioni alterate")

        payload_dict = carica_payload_json(self.gestore_db, self.id_batch)
        lista_misurazioni = filtra_misurazioni_alterate(payload_dict, id_alterati)
        lista_id_sensori = estrai_lista_id_sensori_dal_payload(payload_dict)
        lista_dati_sensori = estrai_dati_sensori_locali(lista_id_sensori, self.gestore_db)

        logger.debug(f"ID misurazioni alterate: {id_alterati}")
        logger.debug(f"ID sensori estratti: {lista_id_sensori}")

        ricostruite = ricostruisci_misurazioni_sensore(lista_misurazioni, lista_dati_sensori)
        logger.debug(f"Misurazioni ricostruite localmente: {ricostruite}")
        return ricostruite

    def esegui_verifica_profonda(self) -> dict:
        """
        Confronta i dati locali e quelli cloud per batch e misurazioni alterate.
        Restituisce un dizionario con le differenze riscontrate.
        """
        differenze_totali = {}
        logger.info("Avvio confronto dati locali e cloud")

        # Confronto dati batch
        if self.batch_alterato():
            logger.info("Batch alterato rilevato, confronto in corso")
            batch_locale = self._recupera_dati_locali_batch()
            batch_cloud = self._recupera_dati_cloud_batch()
            diff_batch = confronta_dati_batch(batch_locale, batch_cloud)

            if diff_batch:
                #solo se non è vuoto
                logger.debug(f"Differenze batch: {diff_batch}")
                differenze_totali["dati_batch"] = diff_batch

        # Confronto misurazioni alterate
        if self.misurazioni_alterate():
            logger.info("Misurazioni alterate rilevate, confronto in corso")
            id_mis_alterati = self.ottieni_id_misurazioni_alterate()

            mis_locale = self._recupera_dati_locali_misurazioni()
            mis_cloud = self._recupera_dati_cloud_misurazioni_sensore(id_mis_alterati)
            diff_misurazioni = confronta_dati_misurazioni_sensori(id_mis_alterati, mis_locale, mis_cloud)

            if diff_misurazioni:
                logger.debug(f"Differenze misurazioni: {diff_misurazioni}")
                differenze_totali["dati_misurazioni_alterate"] = diff_misurazioni

        if not differenze_totali:
            logger.info("Nessuna differenza riscontrata tra i dati locali e cloud")
        else:
            logger.info(f"Differenze trovate: {differenze_totali}")

        return differenze_totali
