import logging

from file_utils import salva_risultato_verifica_su_file
from verificatore_esteso import VerificatoreEsteso

# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

def main():
    # 1. Imposta manualmente un id_batch per test
    id_batch = 2

    # 2. Crea il verificatore esteso
    verificatore = VerificatoreEsteso(id_batch)
    print(f"\n🔍 Avvio verifica per batch {id_batch}...")
    anomalie_rilevate = verificatore.esegui_verifica_completa()
    print(anomalie_rilevate)

    # 3. Verifica se ci sono alterazioni e confronta i dati
    try:
        if not verificatore.ottieni_esito_globale():
            #avvio il processo di verifica estesa
            differenze = verificatore.esegui_verifica_estesa()

            salva_risultato_verifica_su_file(id_batch,
                                             anomalie_rilevate,
                                             esito= verificatore.ottieni_esito_globale(),
                                             base_dir="verifiche_estese",
                                             differenze_json=differenze, )

            print("Salvtaggio effettuato correttamente")
        else:
            print("Nessuna anomalia rilevate.")
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")

if __name__ == "__main__":
    main()
