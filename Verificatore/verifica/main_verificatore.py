import json
import logging

from Verificatore.verifica.verificatore import Verificatore
from verificatore import RisultatoVerifica

# Configura il logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)
logging.getLogger("urllib3").setLevel(logging.WARNING)

def main():
    id_batch = 2 # ← cambia questo valore a piacimento
    verificatore = Verificatore(id_batch)
    differenze : str = verificatore.esegui_verifica_completa()

    logger.info("\n=== RISULTATO VERIFICA ===")

    if verificatore.ottieni_esito_globale():
        logger.info("\n✅ Il batch è integro.")
    else:
        logger.info("\n❌ Il batch presenta alterazioni.")
        logger.info("\n=== ANALISI DELLE ANOMALIE DETTAGLIATA ===")
        print(differenze)


if __name__ == "__main__":
    main()
