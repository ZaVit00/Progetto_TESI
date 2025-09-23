import logging
from copy import deepcopy
from typing import List, Dict, Any

# Funzione per serializzare un dizionario in stringa JSON in formato leggibile
from Classi_comuni.utils.dict_utils import serializza_dict_pretty
# Import di funzioni API per richiedere dati dal cloud
from Produttore_verificatore.api_client.api_cloud import (
    richiedi_dati_cloud_batch,
    richiedi_dati_cloud_completi_misurazioni
)
from Produttore_verificatore.config.istanze_globali import gestore_db
from costanti_comuni import TipoServizio
# Modelli dei dati utilizzati
from modelli_dati import (
    DatiBatch,
    DatiMisurazioneSensorePayload, DatiMisurazione, DatiSensore,
)
# Utility per l’elaborazione e il confronto dei dati
from recupero_dati_utils import (
    carica_payload_batch,
    estrai_lista_id_sensori_dal_payload,
    estrai_dati_sensori_locali,
    filtra_misurazioni_alterate,
    ricostruisci_misurazioni_sensore,
    confronta_dati_batch,
    confronta_dati_misurazioni_sensori
)
from registro_log import setup_logger
from verificatore import Verificatore
from verificatore_utils import ottieni_report_differenze

logger = setup_logger(TipoServizio.PRODUTTORE_VERIFICATORE, module=__name__, level=logging.DEBUG)


class VerificatoreEsteso(Verificatore):
    """
    Classe che estende il verificatore base per permettere il confronto dettagliato
    tra i dati locali e quelli del cloud, utile quando viene rilevata un'alterazione
    per consentire di determinare esattamente cosa è cambiato.
    """
    def __init__(self, id_batch: int):
        """
        Inizializza il verificatore esteso con ID batch specificato
        """
        logger.info(f"Inizializzazione VerificatoreEsteso per batch ID {id_batch}")
        super().__init__(id_batch)

    @classmethod
    def from_verificatore(cls, verificatore: Verificatore) -> "VerificatoreEsteso":
        """
        Crea un VerificatoreEsteso partendo da un oggetto Verificatore,
        copiando tutti gli attributi rilevanti.
        Utile in futuro per estensioni
        """
        esteso = cls(verificatore.id_batch)

        # Copia esplicita degli attributi
        esteso.mappa_id_hash = verificatore.mappa_id_hash.copy()
        esteso.merkle_root_immutabile = verificatore.merkle_root_immutabile
        esteso.cid_merkle_path = verificatore.cid_merkle_path
        esteso.merkle_paths = verificatore.merkle_paths.copy()
        esteso.risultato_verifica = deepcopy(verificatore.risultato_verifica)

        return esteso

    def ottieni_differenze_anomalie(self) -> tuple[str, str]:
        #Avvio del processo di verifica estesa
        #Entry point per la verifica estesa
        differenze = self._esegui_verifica_estesa()
        return (
            ottieni_report_differenze(differenze),
            serializza_dict_pretty(differenze),
        )

    def _esegui_verifica_estesa(self) -> dict:
        """
        Esegue una verifica approfondita sui dati del batch, confrontando i contenuti
        locali con quelli ottenuti dal cloud, **solo in caso di alterazione rilevata**.

        Il confronto copre due livelli:
        1. Dati del batch
        2. Misurazione + Sensore che l'ha prodotta (incluse informazioni sui sensori)
        Ritorna:
            Una stringa JSON contenente le differenze riscontrate tra i dati locali e cloud.
            Se non ci sono alterazioni, restituisce un JSON vuoto "{}".
        La procedura è effettuata campo per campo utilizzando la libreria deepdiff
        """
        differenze_totali: Dict[str, Any] = {}
        logger.info("Avvio confronto dati ottenuti da DB locale 'dati_nodo_fog' e"
                    "dati provenienti dal cloud provider storage")

        # ➤ Verifica e confronto dei dati della tupla batch
        if self.batch_alterato():
            #Batch alterato procedo a calcolare la differenza tra le due istanze
            logger.info("Batch alterato rilevato: avvio confronto tra tupla batch"
                        "memorizzato in locale e tupla batch proveniente da cloud")
            batch_locale: DatiBatch = self._recupera_dati_locali_batch()
            batch_cloud: DatiBatch = self._recupera_dati_cloud_batch()
            diff_batch = confronta_dati_batch(batch_locale, batch_cloud)

            if diff_batch:
                logger.debug(f"Differenze rilevate nel batch: {diff_batch}")
                differenze_totali["dati_batch"] = diff_batch

        # ➤ Verifica e confronto delle misurazioni alterate (e relativi sensori associati)
        if self.misurazioni_alterate():
            logger.info("Misurazioni alterate rilevate: avvio confronto tra tuple"
                        "misurazione inner join sensore proveniente da DB locale"
                        "e tuple misurazione inner join sensore proveniente da cloud")
            id_mis_alterati: list[int] = self.ottieni_id_misurazioni_alterate()

            # Recupera le versioni locali e cloud delle sole misurazioni alterate
            mis_locale: list[DatiMisurazioneSensorePayload] = self._recupera_dati_locali_misurazione_sensore()
            mis_cloud: list[DatiMisurazioneSensorePayload] = self._recupera_dati_cloud_misurazione_sensore(
                id_mis_alterati)

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

        return differenze_totali



    def _recupera_dati_cloud_batch(self) -> DatiBatch:
        """
        Recupera dal cloud i dati del batch
        """
        logger.info("Recupero tupla del batch alterato dal cloud")
        #il batch esiste perché lo abbiamo selezionato dalla finestra di Input.
        batch: DatiBatch = richiedi_dati_cloud_batch(self.id_batch)
        logger.debug(f"Dati batch cloud ricevuti: {batch}")
        return batch

    def _recupera_dati_locali_batch(self) -> DatiBatch:
        """
        Recupera localmente dal database i dati del batch alterato.
        """
        logger.info(f"[BATCH {self.id_batch}] Recupero tupla del batch alterato dal database locale")
        batch: DatiBatch = gestore_db.ottieni_dati_batch(self.id_batch)
        if not batch:
            # Potenziale manomissione: l'ID del batch potrebbe essere stato alterato nel cloud
            msg = (f"[COMPROMISSIONE - TUPLA - BATCH {self.id_batch}] "
                   f"Nessun batch trovato nel database locale. "
                   f"ID ALTERATO nel cloud o alterato.")
            logger.error(msg)
            raise RuntimeError(msg)

        return batch

    def _recupera_dati_cloud_misurazione_sensore(self, id_mis_alterati: List[int]) -> List[DatiMisurazioneSensorePayload]:
        """
        Recupera dal cloud tutte le misurazioni alterate (insieme ai dati del sensore associato).
        """
        if not self.misurazioni_alterate():
            raise ValueError("Nessuna misurazione alterata. Nessun dato da recuperare.")

        logger.info("Recupero misurazioni alterate + dati sensori dal cloud")
        misurazioni_sensori: List[DatiMisurazioneSensorePayload] = (
            richiedi_dati_cloud_completi_misurazioni(id_mis_alterati)
        )
        logger.debug(f"Misurazioni + sensore associato ricevuti dal cloud \n: {misurazioni_sensori}")
        return misurazioni_sensori

    def _recupera_dati_locali_misurazione_sensore(self) -> List[DatiMisurazioneSensorePayload]:
        """
        Ricostruisce localmente solo le misurazioni alterate,
        combinando il payload salvato e i dati dei sensori dal database.
        """
        #ottieni gli id delle misurazioni che risultano alterare
        id_alterati = set(self.ottieni_id_misurazioni_alterate())
        logger.info("Caricamento payload locale e ricostruzione misurazioni alterate")

        # Carica il payload JSON dal database
        # il payload del batch è il pacchetto Batch + Misurazioni inviato al cloud per la memorizzazione
        # contiene i dati del batch e i dati della misurazione.
        payload_dict : dict = carica_payload_batch(self.id_batch)

        # Estrae solo le misurazioni alterate dal payload
        lista_dati_misurazioni : list[DatiMisurazione]= filtra_misurazioni_alterate(payload_dict, id_alterati)

        # Estrae gli ID dei sensori coinvolti nelle misurazioni e recupera i dati associati
        lista_id_sensori : list[str] = estrai_lista_id_sensori_dal_payload(payload_dict)
        lista_dati_sensori : list[DatiSensore] = estrai_dati_sensori_locali(lista_id_sensori)

        logger.debug(f"ID misurazioni alterate: {id_alterati}")
        logger.debug(f"ID sensori estratti: {lista_id_sensori}")

        # Ricostruisce le misurazioni complete (dati + sensore)
        misurazioni_ricostruite : list[DatiMisurazioneSensorePayload] = ricostruisci_misurazioni_sensore(lista_dati_misurazioni, lista_dati_sensori)
        logger.debug(f"Misurazioni ricostruite localmente: {misurazioni_ricostruite}")
        return misurazioni_ricostruite

