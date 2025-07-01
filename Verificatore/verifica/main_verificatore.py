import logging

from Verificatore.verifica.verificatore import Verificatore
from Verificatore.api_client.api_cloud import richiedi_tutti_metadata_batch
from file_utils import salva_risultato_verifica_su_file
from modelli_metadati import MetaDatiBatch
from Verificatore.input.selezione_batch import acquisisci_input_id_batch
from Verificatore.output.visualizza_output import stampa_tabella_batch, stampa_risultato_verifica, stampa_anomalie

# Configura il logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def verifica():
    lista_dati_batch: list[MetaDatiBatch] = richiedi_tutti_metadata_batch()
    stampa_tabella_batch(lista_dati_batch) #visualizza su console i dati del batch batch
    id_batch : int = acquisisci_input_id_batch([b.id_batch for b in lista_dati_batch])
    verificatore = Verificatore(id_batch)
    anomalie_integrita: str = verificatore.esegui_verifica_integrita()

    # Stampa esito
    esito = verificatore.ottieni_esito_globale()
    stampa_risultato_verifica(esito)
    if not esito:
        stampa_anomalie(anomalie_integrita)

    return esito, id_batch, anomalie_integrita, verificatore

if __name__ == "__main__":
    esito, id_batch, anomalie , verificatore = verifica()

    #raccoglie i metadata delle anomalie e le visualizza
    metadata_anomalie = verificatore.recupera_metadata_anomalie()
    stampa_anomalie(metadata_anomalie)


    try:
        salva_risultato_verifica_su_file(id_batch, anomalie, esito, "verifiche_leggere")
        logger.info("File salvato correttamente")
    except Exception as e:
        logger.error(f"Errore nel salvataggio del file {e}")
