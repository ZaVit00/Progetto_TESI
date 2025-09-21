import logging
from Classi_comuni.costruttore_payload import CostruttorePayload
from Classi_comuni.entita.modelli_dati import BatchPayload
from Cloud_service_provider.config.istanze_globali import gestore_db
from costanti_comuni import TipoServizio
from costruttore_modelli_da_query import CostruttoreModelliDaQuery
from modelli_dati import DatiMisurazioneSensorePayload
from modelli_metadati import MetaDatiMisurazioneSensorePayload
from registro_log import setup_logger

logger = setup_logger(TipoServizio.CLOUD, module=__name__, level=logging.DEBUG)


def elabora_pacchetto_batch_misurazioni(payload: BatchPayload) -> bool:
    """
    Riceve un oggetto `BatchPayload` contenente:
    - Un oggetto `DatiBatch` con i dati del batch.
    - Una lista di `DatiMisurazione` con i dati delle N misurazioni associate.

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

    if not gestore_db.inserisci_dati_misurazioni(misurazioni):
        logger.error(f"[ERRORE] Inserimento delle misurazioni per il batch {batch.id_batch} fallito.")
        return False

    return True


def costruisci_mappa_id_hash_foglie(id_batch: int) -> dict[int, str]:
    """
    Estrae i dati relativi a un batch e costruisce la mappa id_misurazione → hash foglia.
    Args:
        id_batch: ID del batch da elaborare.
    Returns:
        Un dizionario che mappa l'ID della misurazione (e della tupla del batch) al relativo hash foglia.
    Raises:
        ValueError: se il batch non esiste o non contiene misurazioni.
    """
    risultati_query = gestore_db.ottieni_dati_batch_misurazioni_sensori(id_batch)
    if not risultati_query:
        raise ValueError(f"Nessuna misurazione trovata per il batch {id_batch}.")

    payload = CostruttorePayload()
    payload.estrai_dati_da_query(risultati_query)
    return payload.ottieni_mappa_id_foglie()


def recupera_dati_misurazione_sensore(lista_id: list[int]) -> list[DatiMisurazioneSensorePayload]:
    """
    Recupera i dati completi (misurazione + sensore) per una lista di ID misurazione.
    Args:
        lista_id: Lista degli ID delle misurazioni da recuperare.
    Returns:
        Lista di oggetti `DatiMisurazioneSensorePayload` pronti per la verifica.
    Raises:
        ValueError: se non viene trovata alcuna riga corrispondente.
    """
    righe: list[dict] = gestore_db.ottieni_dati_misurazione_sensore(lista_id)
    risultato: list[DatiMisurazioneSensorePayload] = []

    if not righe:
        raise ValueError(f"Nessuna misurazione trovata per gli ID richiesti: {lista_id}")

    for riga in righe:
        dati_misurazione = CostruttoreModelliDaQuery.costruisci_dati_misurazione_da_query(riga)
        dati_sensore = CostruttoreModelliDaQuery.costruisci_dati_sensore_da_query(riga)

        # Combinazione finale
        risultato.append(DatiMisurazioneSensorePayload(
            dati_sensore=dati_sensore.model_dump(),
            dati_misurazione=dati_misurazione.model_dump()
        ))

    return risultato


def recupera_metadati_misurazione_sensore(lista_id_mis: list[int]) -> list[MetaDatiMisurazioneSensorePayload]:
    """
    Recupera i soli metadati (non sensibili) relativi a misurazioni e sensori compromessi.

    Questo metodo è pensato per fornire un set di informazioni non sensibili
    relative a una lista di ID di misurazioni che risultano potenzialmente manomesse.
    A differenza del metodo `recupera_dati_misurazione_sensore`, qui non vengono recuperati
    i dati completi, ma solo i metadati associati per permettere al verificatore di identificare
    le misurazioni alterate senza accedere al contenuto originale.
    È utile in fase di audit o visualizzazione dei dati compromessi, quando non si vuole (o non si può)
    mostrare l'intero contenuto originale della misurazione.

    Attenzione: anche questi dati potrebbero essere stati
    potenzialmente manomessi.
    Args:
        lista_id_mis: Lista di ID misurazione richieste

    Returns:
        Lista di oggetti `MetaDatiMisurazioneSensorePayload`

    Raises:
        ValueError: se nessuna delle misurazioni è presente nel database.

    Separare i metadati, dai dati effettivi mi consente di estendere in futuro
    con nuovi attributi.
    """
    righe: list[dict] = gestore_db.ottieni_metadata_misurazione_sensore(lista_id_mis)
    metadati: list[MetaDatiMisurazioneSensorePayload] = []

    if not righe:
        raise ValueError(f"Nessun metadata trovato per le misurazioni: {lista_id_mis}")

    for riga in righe:
        # Parsing dei metadati singoli
        metadati_misurazione = CostruttoreModelliDaQuery.costruisci_metadati_misurazione_da_query(riga)
        metadati_sensore = CostruttoreModelliDaQuery.costruisci_metadati_sensore_da_query(riga)

        # Combinazione finale
        metadati.append(MetaDatiMisurazioneSensorePayload(
            metadati_misurazione=metadati_misurazione.model_dump(),
            metadati_sensore=metadati_sensore.model_dump()
        ))

    return metadati
