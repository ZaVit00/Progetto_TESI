import logging
from Verificatore.verifica.main_verificatore import verifica_batch, ottieni_scelta_id_batch_da_utente
from verificatore_esteso import VerificatoreEsteso

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def main():
    id_batch: int = ottieni_scelta_id_batch_da_utente()
    logger.info(f"🔍 Avvio verifica integrità leggera integrità per il batch ID {id_batch}")
    # Istanza della classe Verificatore Esteso che ha l'accesso ai dati in locale del DB
    verificatore = VerificatoreEsteso(id_batch)
    verifica_batch(id_batch, verificatore, base_dir="verifiche_estese")

if __name__ == "__main__":
    main()
