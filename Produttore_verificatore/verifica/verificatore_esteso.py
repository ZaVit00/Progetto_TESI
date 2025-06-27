# Import dei moduli necessari
import logging
from typing import List

# Import di funzioni API per richiedere dati dal cloud
from Produttore_verificatore.api_client.api_cloud import (
    richiedi_dato_cloud_batch,
    richiedi_dati_cloud_completi_misurazioni
)

# Modelli dei dati utilizzati
from modelli_dati import (
    DatiBatch,
    DatiMisurazioneSensore, DatiMisurazione, DatiSensore,
)

# Funzione per serializzare un dizionario in stringa JSON
from Classi_comuni.utils import serializza_dict

# Classe base del verificatore
from verificatore import Verificatore

# Gestore locale del database in sola lettura
from Produttore.database.gestore_db import GestoreDatabase

# Utility per l’elaborazione e il confronto dei dati
from recupero_dati_utils import (
    carica_payload_json,
    estrai_lista_id_sensori_dal_payload,
    estrai_dati_sensori_locali,
    filtra_misurazioni_alterate,
    ricostruisci_misurazioni_sensore,
    confronta_dati_batch,
    confronta_dati_misurazioni_sensori
)

# Configurazione del logger per registrare informazioni ed errori
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class VerificatoreEsteso(Verificatore):
    """
    Classe che estende il verificatore base per permettere il confronto dettagliato
    tra i dati locali e quelli del cloud, utile quando viene rilevata un'alterazione.
    """

    def __init__(self, id_batch: int):
        """
        Inizializza il verificatore esteso con ID batch specificato
        e apre il database locale in modalità sola lettura.
        """
        logger.info(f"Inizializzazione VerificatoreEsteso per batch ID {id_batch}")
        super().__init__(id_batch)
        self.gestore_db = GestoreDatabase(sola_lettura=True)

    def _recupera_dati_cloud_batch(self) -> DatiBatch:
        """
        Recupera dal cloud i dati del batch, ma solo se è stato rilevato come alterato.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch non risulta alterato. Nessun dato da recuperare.")
        logger.info("Recupero dati batch alterato dal cloud")
        batch: DatiBatch = richiedi_dato_cloud_batch(self.id_batch)
        logger.debug(f"Dati batch cloud ricevuti: {batch}")
        return batch

    def _recupera_dati_locali_batch(self) -> DatiBatch:
        """
        Recupera localmente dal database i dati del batch alterato.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch risulta integro. Nessun dato da recuperare.")
        logger.info("Recupero dati batch alterato dal database locale")
        batch: DatiBatch = self.gestore_db.ottieni_dati_batch(self.id_batch)
        if not batch:
            raise ValueError(f"Nessun batch trovato nel database locale con ID {self.id_batch}")
        logger.debug(f"Dati batch locale ottenuti: {batch}")
        return batch

    def _recupera_dati_cloud_misurazione_sensore(self, id_mis_alterati: List[int]) -> List[DatiMisurazioneSensore]:
        """
        Recupera dal cloud tutte le misurazioni alterate (insieme ai dati del sensore associato).
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione alterata. Nessun dato da recuperare.")

        logger.info("Recupero misurazioni alterate + dati sensori dal cloud")
        misurazioni_sensori: List[DatiMisurazioneSensore] = (
            richiedi_dati_cloud_completi_misurazioni(id_mis_alterati)
        )
        logger.debug(f"Misurazioni + sensore associato ricevuti dal cloud \n: {misurazioni_sensori}")
        return misurazioni_sensori

    def _recupera_dati_locali_misurazione_sensore(self) -> List[DatiMisurazioneSensore]:
        """
        Ricostruisce localmente solo le misurazioni alterate,
        combinando il payload salvato e i dati dei sensori dal database.
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione alterata. Nessun dato da recuperare.")

        id_alterati = set(self.ottieni_id_misurazioni_alterate())
        logger.info("Caricamento payload locale e ricostruzione misurazioni alterate")

        # Carica il payload JSON dal database
        payload_dict : dict = carica_payload_json(self.gestore_db, self.id_batch)

        # Estrae solo le misurazioni alterate dal payload
        lista_dati_misurazioni : list[DatiMisurazione]= filtra_misurazioni_alterate(payload_dict, id_alterati)

        # Estrae gli ID dei sensori coinvolti nelle misurazioni e recupera i dati associati
        lista_id_sensori : list[str] = estrai_lista_id_sensori_dal_payload(payload_dict)
        lista_dati_sensori : list[DatiSensore] = estrai_dati_sensori_locali(lista_id_sensori, self.gestore_db)

        logger.debug(f"ID misurazioni alterate: {id_alterati}")
        logger.debug(f"ID sensori estratti: {lista_id_sensori}")

        # Ricostruisce le misurazioni complete (dati + sensore)
        ricostruite : list[DatiMisurazioneSensore] = ricostruisci_misurazioni_sensore(lista_dati_misurazioni, lista_dati_sensori)
        logger.debug(f"Misurazioni ricostruite localmente: {ricostruite}")
        return ricostruite

    def esegui_verifica_profonda(self) -> str:
        """
        Esegue un confronto completo tra dati locali e cloud per batch e misurazioni alterate.
        Restituisce un JSON con tutte le differenze trovate.
        """
        differenze_totali : dict = {}
        logger.info("Avvio confronto dati locali e cloud")

        # Verifica se il batch è stato alterato e lo confronta
        if self.batch_alterato():
            logger.info("Batch alterato rilevato, confronto in corso")
            batch_locale : DatiBatch = self._recupera_dati_locali_batch()
            batch_cloud : DatiBatch = self._recupera_dati_cloud_batch()
            diff_batch = confronta_dati_batch(batch_locale, batch_cloud)

            if diff_batch:
                logger.debug(f"Differenze batch: {diff_batch}")
                differenze_totali["dati_batch"] = diff_batch

        # Verifica se ci sono misurazioni alterate e le confronta
        if self.misurazioni_alterate():
            logger.info("Misurazioni alterate rilevate, confronto in corso")
            id_mis_alterati : list[int] = self.ottieni_id_misurazioni_alterate()

            # Recupera le misurazioni locali e cloud
            mis_locale : list[DatiMisurazioneSensore] = self._recupera_dati_locali_misurazione_sensore()
            mis_cloud : list[DatiMisurazioneSensore] = self._recupera_dati_cloud_misurazione_sensore(id_mis_alterati)
            diff_misurazioni_sensori : dict = confronta_dati_misurazioni_sensori(id_mis_alterati, mis_locale, mis_cloud)

            if diff_misurazioni_sensori:
                logger.debug(f"Differenze misurazioni: {diff_misurazioni_sensori}")
                differenze_totali["dati_misurazioni_alterate"] = diff_misurazioni_sensori

        # Log finale con o senza differenze
        if not differenze_totali:
            logger.info("Nessuna differenza riscontrata tra i dati locali e cloud")
        else:
            logger.debug(f"Differenze trovate: {differenze_totali}")

        # Serializza il risultato in JSON (stringa)
        return serializza_dict(differenze_totali)
