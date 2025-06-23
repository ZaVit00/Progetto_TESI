import logging
import json
from Verificatore.verifica.verificatore import Verificatore
from api_cloud import richiedi_metadata_misurazioni, richiedi_metadata_batch
from verificatore import RisultatoVerifica

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
    risultati : RisultatoVerifica = verificatore.esegui_verifica_completa()

    logger.info("\n=== RISULTATO VERIFICA ===")

    if risultati["esito_globale"]:
        logger.info("\n✅ Il batch è integro.")
    else:
        logger.info("\n❌ Il batch presenta alterazioni.")

    logger.info("\n=== ANALISI DELLE ANOMALIE DETTAGLIATA ===")
    print(json.dumps(risultati, indent=2, ensure_ascii=False))
    metadata_str = Verificatore.recupera_metadata_anomalie(risultati)
    print(metadata_str)



if __name__ == "__main__":
    main()
