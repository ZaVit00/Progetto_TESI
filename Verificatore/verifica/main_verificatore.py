import logging
from IO.input import acquisisci_input_id_batch
from IO.output import stampa_tabella_batch, stampa_risultato_verifica, stampa_anomalie
from Verificatore.api_client.api_cloud import richiedi_tutti_metadata_batch
from Verificatore.verifica.verificatore import Verificatore
from Classi_comuni.utils.file_utils import salva_risultato_verifica_su_file
from modelli_metadati import MetaDatiBatch
from verificatore_esteso import VerificatoreEsteso

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.DEBUG)


def verifica_batch(id_batch, verificatore : Verificatore) -> tuple[int, bool, str, str, str]:
    """
    Esegue la verifica di integrità su un batch specifico.

    Parametri:
        id_batch (int): Identificativo del batch da verificare.
        verificatore (Verificatore): Oggetto che incapsula la logica di verifica
                                       (può essere anche una sottoclasse come VerificatoreEsteso).
    Restituisce:
        Tuple contenente:
        - ID del batch analizzato
        - Esito globale della verifica (True/False)
        - JSON con anomalie rilevate
        - JSON con metadati delle anomalie (vuoto se non presenti)
        - JSON con differenze tra dati locali e cloud (solo se VerificatoreEsteso, altrimenti stringa vuota)
  """
    metadati_json: str = ""
    differenze_json : str = ""

    try:
        #esegui il processo di verifica dell'integrità
        anomalie_json: str = verificatore.esegui_verifica_integrita()
        esito = verificatore.ottieni_esito_globale()
        if not esito:
            # Se il verificatore è un VerificatoreEsteso, esegue anche la verifica profonda
            if isinstance(verificatore, VerificatoreEsteso):
                logger.info("🔎 Verifica estesa attivata (con confronto cloud)")
                differenze_json : str = verificatore.esegui_verifica_estesa()
                logger.debug(f"Differenze dettagliate trovate:\n{differenze_json}")
            else:
                # Se il verificatore è istanza solo della classe Verificatore richiedi solo
                # i metadati delle anomalie
                metadati_json: str = verificatore.recupera_metadata_anomalie()

    except Exception as e:
        logger.error(f"❌ Errore durante la verifica del batch ID {id_batch}: {e}")
        raise

    return id_batch, esito, anomalie_json, metadati_json, differenze_json

def ottieni_scelta_id_batch_da_utente() -> int:
    lista_dati_batch: list[MetaDatiBatch] = richiedi_tutti_metadata_batch()
    stampa_tabella_batch(lista_dati_batch)
    id_batch: int = acquisisci_input_id_batch([b.id_batch for b in lista_dati_batch])
    return id_batch

def main():
    id_batch : int = ottieni_scelta_id_batch_da_utente()

    logger.info(f"🔍 Avvio verifica integrità per il batch ID {id_batch}")

    verificatore = Verificatore(id_batch)

    #differenze_json sarà una stringa vuota se il verificatore non è una istanza di VerificatoreEsteso
    id_batch, esito, anomalie_json, metadata_json, differenze_json = verifica_batch(id_batch, verificatore)

    #visualizza l'Output dell'analisi del processo di integrità
    stampa_risultato_verifica(esito)

    if not esito:
        stampa_anomalie(anomalie_json)
        stampa_anomalie(metadata_json)
        # Salva su file il risultato della verifica effettuata + metadati
        try:
            salva_risultato_verifica_su_file(id_batch,
                                             contenuto_json=anomalie_json,
                                             esito=esito,
                                             base_dir="verifiche_leggere",
                                             metadati_anomalie_json=metadata_json)
            logger.info("✅ Risultato verifica salvato correttamente su file.")
        except Exception as e:
            logger.error(f"❌ Errore durante il salvataggio del file di verifica: {e}")
            raise


if __name__ == "__main__":
    main()
