# Import dei moduli necessari
import logging
from copy import deepcopy
from typing import List, Dict, Any

# Funzione per serializzare un dizionario in stringa JSON
from Classi_comuni.utils.dict_utils import serializza_dict
# Gestore locale del database in sola lettura
# Import di funzioni API per richiedere dati dal cloud
from Produttore_verificatore.api_client.api_cloud import (
    richiedi_dati_cloud_batch,
    richiedi_dati_cloud_completi_misurazioni
)
from Produttore_verificatore.config.istanze_globali import gestore_db
# Modelli dei dati utilizzati
from modelli_dati import (
    DatiBatch,
    DatiMisurazioneSensore, DatiMisurazione, DatiSensore,
)
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
# Classe base del verificatore
from verificatore import Verificatore

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

    @classmethod
    def from_verificatore(cls, verificatore: Verificatore) -> "VerificatoreEsteso":
        """
        Crea un VerificatoreEsteso partendo da un oggetto Verificatore,
        copiando tutti gli attributi rilevanti.
        Utile in futuro
        """
        esteso = cls(verificatore.id_batch)

        # Copia esplicita degli attributi
        esteso.mappa_id_hash = verificatore.mappa_id_hash.copy()
        esteso.merkle_root_immutabile = verificatore.merkle_root_immutabile
        esteso.cid_merkle_path = verificatore.cid_merkle_path
        esteso.merkle_paths = verificatore.merkle_paths.copy()
        esteso.risultato = deepcopy(verificatore.risultato)

        return esteso

    def _recupera_dati_cloud_batch(self) -> DatiBatch:
        """
        Recupera dal cloud i dati del batch, ma solo se è stato rilevato come alterato.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch non risulta alterato. Nessun dato da recuperare.")

        logger.info("Recupero dati batch alterato dal cloud")
        batch: DatiBatch = richiedi_dati_cloud_batch(self.id_batch)
        logger.debug(f"Dati batch cloud ricevuti: {batch}")
        return batch

    def _recupera_dati_locali_batch(self) -> DatiBatch:
        """
        Recupera localmente dal database i dati del batch alterato.
        """
        if not self.batch_alterato():
            raise ValueError("Il batch risulta integro. Nessun dato da recuperare.")
        logger.info("Recupero dati batch alterato dal database locale")
        batch: DatiBatch = gestore_db.ottieni_dati_batch(self.id_batch)
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

        #ottieni gli id delle misurazioni che risultano alterare
        id_alterati = set(self.ottieni_id_misurazioni_alterate())
        logger.info("Caricamento payload locale e ricostruzione misurazioni alterate")

        # Carica il payload JSON dal database
        # il payload del batch è il pacchetto Batch + Misurazioni inviato al cloud per la memorizzazione
        # contiene i dati del batch e i dati della misurazione.
        payload_dict : dict = carica_payload_json(self.id_batch)

        # Estrae solo le misurazioni alterate dal payload
        lista_dati_misurazioni : list[DatiMisurazione]= filtra_misurazioni_alterate(payload_dict, id_alterati)

        # Estrae gli ID dei sensori coinvolti nelle misurazioni e recupera i dati associati
        lista_id_sensori : list[str] = estrai_lista_id_sensori_dal_payload(payload_dict)
        lista_dati_sensori : list[DatiSensore] = estrai_dati_sensori_locali(lista_id_sensori)

        logger.debug(f"ID misurazioni alterate: {id_alterati}")
        logger.debug(f"ID sensori estratti: {lista_id_sensori}")

        # Ricostruisce le misurazioni complete (dati + sensore)
        misurazioni_ricostruite : list[DatiMisurazioneSensore] = ricostruisci_misurazioni_sensore(lista_dati_misurazioni, lista_dati_sensori)
        logger.debug(f"Misurazioni ricostruite localmente: {misurazioni_ricostruite}")
        return misurazioni_ricostruite

    def esegui_verifica_estesa(self) -> str:
        """
        Esegue una verifica approfondita sui dati del batch, confrontando i contenuti
        locali con quelli ottenuti dal cloud, **solo in caso di alterazione rilevata**.

        Il confronto copre due livelli:
        1. Dati del batch (metadati generali)
        2. Misurazioni associate (incluse informazioni sui sensori)

        Ritorna:
            Una stringa JSON contenente le differenze riscontrate tra i dati locali e cloud.
            Se non ci sono alterazioni, restituisce un JSON vuoto "{}".
        """
        differenze_totali: Dict[str, Any] = {}
        logger.info("Avvio confronto dati locali e cloud")

        # ➤ Verifica e confronto dei dati del batch
        if self.batch_alterato():
            logger.info("Batch alterato rilevato: avvio confronto tra batch locale e cloud")
            batch_locale: DatiBatch = self._recupera_dati_locali_batch()
            batch_cloud: DatiBatch = self._recupera_dati_cloud_batch()
            diff_batch = confronta_dati_batch(batch_locale, batch_cloud)

            if diff_batch:
                logger.debug(f"Differenze rilevate nel batch: {diff_batch}")
                differenze_totali["dati_batch"] = diff_batch

        # ➤ Verifica e confronto delle misurazioni alterate (e relativi sensori)
        if self.misurazioni_alterate():
            logger.info("Misurazioni alterate rilevate: avvio confronto tra dati locali e cloud")
            id_mis_alterati: list[int] = self.ottieni_id_misurazioni_alterate()

            # Recupera le versioni locali e cloud delle sole misurazioni alterate
            mis_locale: list[DatiMisurazioneSensore] = self._recupera_dati_locali_misurazione_sensore()
            mis_cloud: list[DatiMisurazioneSensore] = self._recupera_dati_cloud_misurazione_sensore(id_mis_alterati)

            # Confronta ogni misurazione + sensore associato
            diff_misurazioni_sensori: dict = confronta_dati_misurazioni_sensori(
                id_mis_alterati, mis_locale, mis_cloud
            )

            if diff_misurazioni_sensori:
                logger.debug(f"Differenze rilevate nelle misurazioni: {diff_misurazioni_sensori}")
                differenze_totali["dati_misurazioni_alterate"] = diff_misurazioni_sensori

        # ➤ Log finale: nessuna differenza o riepilogo delle anomalie
        if not differenze_totali:
            logger.info("✅ Nessuna differenza rilevata: i dati locali e cloud sono coerenti")
        else:
            logger.debug(f"❌ Differenze complessive rilevate: {differenze_totali}")

        # ➤ Serializza il risultato del confronto in formato JSON
        return serializza_dict(differenze_totali)

