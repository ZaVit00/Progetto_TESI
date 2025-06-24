import logging
from typing import Tuple

from Classi_comuni.costruttore_payload import CostruttorePayload
from Classi_comuni.entita.modelli_dati import DatiPayload, DatiListaSensori, MetaDatiMisurazione, DatiMisurazione
from Cloud_Service_Provider.database.gestore_db import GestoreDatabase
from modelli_dati import DatiSensore

logger = logging.getLogger(__name__)

def elabora_payload(payload: DatiPayload, gestore_db: GestoreDatabase) -> bool:
    """
    Riceve un oggetto DatiPayload contenente:
    - Un batch (DatiBatch)
    - Una lista di misurazioni (DatiMisurazione)
    Esegue:
    1. Inserimento del batch nel database
    2. Inserimento di ogni misurazione associata

    Ritorna:
    - True se tutte le operazioni vanno a buon fine
    - False se una qualsiasi operazione fallisce
    """
    batch = payload.batch
    #lista di misurazioni
    misurazioni = payload.misurazioni

    # Prima l'inserimento del batch e poi delle misurazioni associate
    if not gestore_db.inserisci_batch(batch):
        logger.error(f"Inserimento batch {batch.id_batch} fallito.")
        return False

    # Inserisce le misurazioni
    for m in misurazioni:
        if not gestore_db.inserisci_misurazione(m, batch.id_batch):
            logger.error(f"Inserimento misurazione {m.id_misurazione} fallito.")
            return False

    #entrambe le operazioni sono andate a buon fine
    return True


def costruisci_mappa_id_hash_batch(id_batch: int, gestore_db : GestoreDatabase) -> dict[int, str]:
    risultati_query = gestore_db.estrai_dati_batch_misurazioni_sensori(id_batch)
    if not risultati_query:
        raise ValueError(f"Nessun batch trovato con ID {id_batch}")

    payload = CostruttorePayload()
    payload.estrai_dati_da_query(risultati_query)
    return payload.ottieni_mappa_id_foglie()

def elabora_lista_sensori(payload: DatiListaSensori, gestore_db: GestoreDatabase) -> list[str]:
    """
    Tenta di inserire nel database tutti i sensori contenuti nel payload.
    Restituisce una lista degli ID dei sensori inseriti con successo.
    """
    id_sensori_inseriti = []
    for sensore in payload.sensori:
        successo = gestore_db.inserisci_sensore(sensore)
        if successo:
            logger.info(f"[SENSORI] Sensore registrato: {sensore.id_sensore}")
            id_sensori_inseriti.append(sensore.id_sensore)
        else:
            logger.warning(f"[SENSORI] Registrazione fallita per: {sensore.id_sensore}")

    return id_sensori_inseriti

def recupera_metadata_misurazioni(lista_id: list[int], gestore_db : GestoreDatabase) -> list[MetaDatiMisurazione]:
    """
    Recupera i metadata delle misurazioni dati gli ID. Solleva ValueError se una misurazione non esiste.
    """
    metadata = []
    for id_misurazione in lista_id:
        record : MetaDatiMisurazione = gestore_db.estrai_metadata_misurazione(id_misurazione)
        if not record:
            raise ValueError(f"Misurazione con ID {id_misurazione} non trovata")
        metadata.append(record)
    return metadata

def recupera_dati_misurazioni(lista_id: list[int], gestore_db: GestoreDatabase):
    """
    Recupera i dati completi delle misurazioni dati gli ID. Solleva ValueError se una misurazione non esiste.
    """
    risultato = []
    for id_misurazione in lista_id:
        record: Tuple[DatiMisurazione, DatiSensore] = gestore_db.estrai_dati_misurazione_sensore(id_misurazione)
        if not record:
            raise ValueError(f"Misurazione con ID {id_misurazione} non trovata")
        risultato.append(record)
    return risultato