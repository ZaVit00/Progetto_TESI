import logging

from IO.output import stampa_anomalie, stampa_risultato_verifica
from Verificatore.verifica.main_verificatore import verifica_batch, ottieni_scelta_id_batch_da_utente
from Classi_comuni.utils.file_utils import salva_risultato_verifica_su_file
from verificatore_esteso import VerificatoreEsteso

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def main():
    id_batch : int = ottieni_scelta_id_batch_da_utente()
    verificatore_esteso = VerificatoreEsteso(id_batch)
    id_batch, esito, anomalie_json, metadata_json, differenze_json = verifica_batch(id_batch, verificatore_esteso)
    #visualizza il risultato dell'analisi del processo di integrità
    stampa_risultato_verifica(esito)

    if not esito:
        stampa_anomalie(anomalie_json)
        stampa_anomalie(differenze_json)
        # Salva su file il risultato della verifica effettuata + differenze trovate
        try:
            salva_risultato_verifica_su_file(id_batch,
                                             contenuto_json=anomalie_json,
                                             esito=esito,
                                             base_dir="verifiche_estese",
                                             differenze = differenze_json)
            logger.info("✅ Risultato verifica salvato correttamente su file.")

        except Exception as e:
            logger.error(f"❌ Errore durante il salvataggio del file di verifica: {e}")
            raise

if __name__ == "__main__":
    main()
