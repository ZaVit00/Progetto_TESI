import logging
import math

SOGLIA_BATCH: int = 4095
K_BATCH_SCALING: int = 4  # Puoi modificare questo valore a piacere

logger = logging.getLogger(__name__)

def aggiorna_soglia_batch(frequenza_media: float) -> None:
    """
    Aggiorna la soglia batch globale in base alla frequenza media osservata.
    Ogni qualvolta viene registrato un sensore nel sistema locale,
    la soglia viene modificata in modo dinamico secondo la funzione.
    Logica applicata:
    0. La frequenza media viene estratta dal database e passata come argomento alla funzione
    1. Calcola il logaritmo in base 2 della frequenza media.
    2. Arrotonda all'intero più vicino
    3. Eleva 2 alla potenza arrotondata → potenza di due più vicina.
    4. Aggiorna la variabile globale `SOGLIA_BATCH_DINAMICA`.

    Se la frequenza è nulla o negativa, l’aggiornamento viene ignorato.
    """
    global SOGLIA_BATCH_DINAMICA

    if frequenza_media <= 0:
        logger.warning("Frequenza media non valida: impossibile aggiornare la soglia.")
        return

    potenza = math.ceil(math.log2(frequenza_media))
    #potenza di due - 1
    nuova_soglia = ((2 ** potenza) * K_BATCH_SCALING) - 1
    SOGLIA_BATCH_DINAMICA = nuova_soglia

    logger.debug(f"Soglia aggiornata: {SOGLIA_BATCH_DINAMICA} "
                f"(frequenza media: {frequenza_media}, potenza: 2^{potenza}, "
                f"K = {K_BATCH_SCALING})")

def ottieni_soglia_batch() -> int:
    return SOGLIA_BATCH