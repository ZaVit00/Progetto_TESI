import logging
from typing import cast

from IO.input import acquisisci_input_id_batch
from IO.output import stampa_tabella_batch, stampa_risultato_verifica, visualizza_output
from Verificatore.api_client.api_cloud import richiedi_tutti_metadata_batch
from Verificatore.verifica.verificatore import Verificatore
from Classi_comuni.utils.file_utils import salva_risultato_verifica_su_file
from Verificatore.entita.modelli_verificatore import RisultatoMetadatiAnomalie, RisultatoVerifica
from modelli_metadati import MetaDatiBatch
from verificatore_esteso import VerificatoreEsteso
from verificatore_utils import ottieni_report_anomalie, ottieni_report_metadati_anomalie, ottieni_report_differenze
from Classi_comuni.utils.dict_utils import serializza_dict
logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)


def verifica_batch(id_batch: int, verificatore: Verificatore) -> None:
    report_anomalie = ""
    report_metadati = ""
    report_differenze = ""

    try:
        risultato: RisultatoVerifica = verificatore.esegui_verifica_integrita()
        esito = verificatore.ottieni_esito_globale()

        if not esito:
            anomalie_serializzate = serializza_dict(cast(dict, risultato))
            report_anomalie = ottieni_report_anomalie(risultato)

            # Estrae info metadati o differenze secondo la classe concreta
            report_differenze, differenze_serializzate = verificatore.ottieni_output_differenze()
            report_metadati, metadati_serializzati = verificatore.ottieni_output_metadati()

            kwargs_salvataggio = {
                "id_batch": id_batch,
                "anomalie_trovate": anomalie_serializzate,
                "esito": esito,
                "base_dir": "verifiche_leggere",
            }

            if metadati_serializzati:
                kwargs_salvataggio["metadati_anomalie"] = metadati_serializzati

            if differenze_serializzate:
                kwargs_salvataggio["differenze"] = differenze_serializzate

            salva_risultato_verifica_su_file(**kwargs_salvataggio)

    except Exception as e:
        logger.error(f"❌ Errore durante la verifica del batch ID {id_batch}: {e}")
        raise

    visualizza_esiti(
        esito=esito,
        report_anomalie=report_anomalie,
        report_metadati=report_metadati,
        report_differenze=report_differenze,
        verifica_estesa=isinstance(verificatore, VerificatoreEsteso)
    )

def ottieni_scelta_id_batch_da_utente() -> int:
    lista_dati_batch: list[MetaDatiBatch] = richiedi_tutti_metadata_batch()
    stampa_tabella_batch(lista_dati_batch)
    id_batch: int = acquisisci_input_id_batch([b.id_batch for b in lista_dati_batch])
    return id_batch

def visualizza_esiti(esito, report_anomalie, report_metadati, report_differenze, verifica_estesa : bool = False ):
    stampa_risultato_verifica(esito)

    if not esito:
        visualizza_output(report_anomalie)
        if verifica_estesa:
            visualizza_output(report_differenze)
        else:
            visualizza_output(report_metadati)

def main():
    id_batch: int = ottieni_scelta_id_batch_da_utente()
    logger.info(f"🔍 Avvio verifica integrità leggera integrità per il batch ID {id_batch}")
    verificatore = Verificatore(id_batch)
    verifica_batch(id_batch, verificatore)

if __name__ == "__main__":
    main()
