import logging

from Classi_comuni.costruttore_payload import CostruttorePayload
from Classi_comuni.entita.modelli_dati import PacchettoBatchMisurazioni
from Cloud_Service_Provider.config.istanze_globali import gestore_db
from modelli_dati import DatiMisurazioneSensore
from modelli_metadati import MetaDatiMisurazioneSensore

logger = logging.getLogger(__name__)

def elabora_pacchetto_batch_misurazioni(payload: PacchettoBatchMisurazioni) -> bool:
    """
    Riceve un oggetto `PacchettoBatchMisurazioni` contenente:
    - Un oggetto `DatiBatch` con i metadati del batch.
    - Una lista di `DatiMisurazione` con le misurazioni associate.

    Esegue:
    1. Inserimento del batch nel database.
    2. Inserimento delle misurazioni associate.

    Restituisce:
        True se entrambe le operazioni vanno a buon fine, False altrimenti.
    """
    batch = payload.batch
    misurazioni = payload.misurazioni

    if not gestore_db.inserisci_dati_batch(batch):
        logger.error(f"[ERRORE] Inserimento del batch {batch.id_batch} fallito.")
        return False

    if not gestore_db.inserisci_dati_misurazione(misurazioni):
        logger.error(f"[ERRORE] Inserimento delle misurazioni per il batch {batch.id_batch} fallito.")
        return False

    return True


def costruisci_mappa_id_hash_foglie(id_batch: int) -> dict[int, str]:
    """
    Estrae i dati relativi a un batch e costruisce la mappa id_misurazione → hash foglia.

    Args:
        id_batch: ID del batch da elaborare.

    Returns:
        Un dizionario che mappa l'ID della misurazione al relativo hash foglia.

    Raises:
        ValueError: se il batch non esiste o non contiene misurazioni.
    """
    risultati_query = gestore_db.ottieni_dati_batch_misurazioni_sensori(id_batch)
    if not risultati_query:
        raise ValueError(f"Nessuna misurazione trovata per il batch {id_batch}.")

    payload = CostruttorePayload()
    payload.estrai_dati_da_query(risultati_query)
    return payload.ottieni_mappa_id_foglie()


def recupera_dati_misurazione_sensore(lista_id: list[int]) -> list[DatiMisurazioneSensore]:
    """
    Recupera i dati completi (misurazione + sensore) per una lista di ID misurazione.

    Args:
        lista_id: Lista degli ID delle misurazioni da recuperare.

    Returns:
        Lista di oggetti `DatiMisurazioneSensore` pronti per la verifica.

    Raises:
        ValueError: se non viene trovata alcuna riga corrispondente.
    """
    righe: list[dict] = gestore_db.ottieni_dati_misurazione_sensore(lista_id)
    risultato: list[DatiMisurazioneSensore] = []

    if not righe:
        raise ValueError(f"Nessuna misurazione trovata per gli ID richiesti: {lista_id}")

    for riga in righe:
        # Parsing dei dati singoli
        dati_misurazione = CostruttorePayload.costruisci_dati_misurazione_da_query(riga)
        dati_sensore = CostruttorePayload.costruisci_dati_sensore_da_query(riga)

        # Combinazione finale
        risultato.append(DatiMisurazioneSensore(
            dati_sensore=dati_sensore.model_dump(),
            dati_misurazione=dati_misurazione.model_dump()
        ))

    return risultato


def recupera_metadati_misurazione_sensore(lista_id_mis: list[int]) -> list[MetaDatiMisurazioneSensore]:
    """
    Recupera i metadati completi (sensore + misurazione) per una lista di ID.

    Args:
        lista_id_mis: Lista di ID misurazione.

    Returns:
        Lista di oggetti `MetaDatiMisurazioneSensore` per la verifica strutturale.

    Raises:
        ValueError: se nessuna delle misurazioni è presente nel database.
    """
    righe: list[dict] = gestore_db.ottieni_metadata_misurazione_sensore(lista_id_mis)
    metadati: list[MetaDatiMisurazioneSensore] = []

    if not righe:
        raise ValueError(f"Nessun metadata trovato per le misurazioni: {lista_id_mis}")

    for riga in righe:
        # Parsing dei metadati singoli
        metadati_misurazione = CostruttorePayload.costruisci_metadati_misurazione_da_query(riga)
        metadati_sensore = CostruttorePayload.costruisci_metadati_sensore_da_query(riga)

        # Combinazione finale
        metadati.append(MetaDatiMisurazioneSensore(
            metadati_misurazione=metadati_misurazione.model_dump(),
            metadati_sensore=metadati_sensore.model_dump()
        ))

    return metadati
