import logging
import math

from istanze_globali import gestore_db

logger = logging.getLogger(__name__)


# Soglia (numero massimo di misurazioni) per determinare la chiusura automatica di un batch.
# Deve essere una potenza di due meno uno (es. 2^12 - 1 = 4095) per garantire compatibilità
# con la struttura binaria del Merkle Tree impostata nel progetto

# Costante moltiplicativa per scalare la dimensione del batch
# serve per aumentare la dimensione del batch
K_BATCH_SCALING: int = 32  # Puoi modificare questo valore a piacere 2^5
SOGLIA_BATCH_MINIMA: int = 127 # soglia minima del batch 2^n - 1

def aggiorna_soglia_batch() -> None:
    frequenza_media: float = gestore_db.ottieni_frequenza_media_sensori()
    logger.debug(f"valore attuale della frequenza media {frequenza_media}")

    if frequenza_media <= 0.0:
        logger.warning("Frequenza media non valida: impossibile aggiornare la soglia.")
        return

    esponente = math.ceil(math.log2(frequenza_media))
    #(potenza di due elevato a esponente * k batch scaling) - 1
    nuova_soglia = ((2 ** esponente) * K_BATCH_SCALING) - 1
    # scegli il massimo tra i due per garantire una soglia di una certa dimensione prefissata
    soglia_finale = max(nuova_soglia, SOGLIA_BATCH_MINIMA)

    # verificare se esiste attualmente un batch attivo nel sistema
    esito_aggiornamento : bool = gestore_db.aggiorna_soglia(soglia_finale)
    logger.debug(f"Esito del processo di aggiornamento {esito_aggiornamento}")


    logger.debug(f"Soglia aggiornata: {soglia_finale} "
                f"(frequenza media: {frequenza_media}, potenza: 2^{esponente}, "
                f"K = {K_BATCH_SCALING})")