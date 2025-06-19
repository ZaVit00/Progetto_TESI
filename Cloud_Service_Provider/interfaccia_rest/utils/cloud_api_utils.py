import logging

from Classi_comuni.costruttore_payload import CostruttorePayload
from Classi_comuni.entita.modelli_dati import DatiPayload
from Cloud_Service_Provider.database.gestore_db import GestoreDatabase

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


def costruisci_payload_per_batch(id_batch: int, gestore_db : GestoreDatabase) -> DatiPayload:
    risultati_query = gestore_db.estrai_dati_batch_misurazioni(id_batch)
    if not risultati_query:
        raise ValueError(f"Nessun batch trovato con ID {id_batch}")

    payload = CostruttorePayload()
    payload.estrai_dati_da_query(risultati_query)
    print("ciao vito")
    return payload.costruisci_payload()
