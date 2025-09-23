import logging
from costanti_comuni import TipoServizio
from main_verificatore import verifica_batch, ottieni_scelta_id_batch_da_utente
from registro_log import setup_logger
from verificatore_esteso import VerificatoreEsteso

logger = setup_logger(TipoServizio.PRODUTTORE_VERIFICATORE, module=__name__, level=logging.DEBUG)


def main():
    id_batch: int = ottieni_scelta_id_batch_da_utente()
    logger.info(f"Avvio verifica integrità profonda/estesa (con differenze) per il batch ID {id_batch}")
    # Istanza della classe Verificatore Esteso che ha l'accesso ai dati in locale del DB
    verificatore = VerificatoreEsteso(id_batch)
    verifica_batch(id_batch, verificatore, base_dir="Produttore_verificatore/verifica/verifiche_estese")

if __name__ == "__main__":
    main()
