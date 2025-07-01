import logging
from file_utils import salva_risultato_verifica_su_file
from verificatore_esteso import VerificatoreEsteso
from Verificatore.verifica.main_verificatore import verifica
from visualizza_output import stampa_anomalie

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def verifica_estesa():
    try:
        #richiama il processo di verifica standard riutilizzando il metodo
        esito, id_batch, anomalie_integrita, verificatore  = verifica()

        if not esito:
            verificatore_esteso = VerificatoreEsteso.from_verificatore(verificatore) #sfrutta l'oggetto verificatore già creato
            differenze = verificatore_esteso.esegui_verifica_estesa() # ottieni le differenze
            stampa_anomalie(differenze) #visualizza le differenze su console

            #salva l'esito su file
            salva_risultato_verifica_su_file(id_batch, anomalie_integrita, esito,
                                             base_dir="verifiche_estese", differenze=differenze)
    except Exception as e:
        print(f"❌ Errore durante la verifica estesa: {e}")

if __name__ == "__main__":
    verifica_estesa()
