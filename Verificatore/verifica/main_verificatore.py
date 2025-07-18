import logging
from IO.input import acquisisci_input_id_batch
from IO.output import stampa_tabella_batch, stampa_risultato_verifica, stampa_anomalie
from Verificatore.api_client.api_cloud import richiedi_tutti_metadata_batch
from Verificatore.verifica.verificatore import Verificatore
from Classi_comuni.utils.file_utils import salva_risultato_verifica_su_file
from modelli_metadati import MetaDatiBatch

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.DEBUG)


def verifica_batch() -> tuple[bool, int, str, Verificatore]:
    """
    Esegue la procedura di verifica di un batch selezionato.
    Restituisce:
        - esito globale della verifica (True/False)
        - ID del batch analizzato
        - JSON con anomalie rilevate
        - istanza del Verificatore
    """
    lista_dati_batch: list[MetaDatiBatch] = richiedi_tutti_metadata_batch()
    stampa_tabella_batch(lista_dati_batch)

    id_batch: int = acquisisci_input_id_batch([b.id_batch for b in lista_dati_batch])
    verificatore = Verificatore(id_batch)

    try:
        anomalie_json: str = verificatore.esegui_verifica_integrita()
    except Exception as e:
        logger.error(f"❌ Errore durante la verifica del batch ID {id_batch}: {e}")
        raise

    esito = verificatore.ottieni_esito_globale()
    stampa_risultato_verifica(esito)

    if not esito:
        stampa_anomalie(anomalie_json)

    return esito, id_batch, anomalie_json, verificatore

if __name__ == "__main__":
    esito, id_batch, anomalie_json, verificatore = verifica_batch()
    # Recupera e stampa i metadati delle anomalie (se presenti)
    try:
        # TODO POSSIBILE FIX QUI
        metadata_json = verificatore.recupera_metadata_anomalie()
        stampa_anomalie(metadata_json)
    except Exception as e:
        logger.warning(f"⚠ Impossibile recuperare i metadati delle anomalie: {e}")

    # Salva su file il risultato della verifica effettuata.
    try:
        salva_risultato_verifica_su_file(id_batch, anomalie_json, esito, "verifiche_leggere")
        logger.info("✅ Risultato verifica salvato correttamente su file.")
    except Exception as e:
        logger.error(f"❌ Errore durante il salvataggio del file di verifica: {e}")