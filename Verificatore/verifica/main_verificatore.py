import logging

from Verificatore.verifica.verificatore import Verificatore
from file_utils import salva_risultato_verifica_su_file

# Configura il logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)



def main():
    id_batch = 1 # ← cambia questo valore a piacimento
    verificatore = Verificatore(id_batch)
    differenze : str = verificatore.esegui_verifica_completa()

    logger.info("\n=== RISULTATO VERIFICA ===")

    if verificatore.ottieni_esito_globale():
        logger.info("\n✅ Il batch è integro.")
    else:
        logger.info("\n❌ Il batch presenta alterazioni.")
        logger.info("\n=== ANALISI DELLE ANOMALIE DETTAGLIATA ===")
        print(differenze)
        try:
            salva_risultato_verifica_su_file(id_batch, differenze, verificatore.ottieni_esito_globale(), "verifiche_profonde")
            logger.info("File salvato correttamente")
        except Exception as e:
            logger.error(f"Errore nel salvataggio del file {e}")

if __name__ == "__main__":
    main()
