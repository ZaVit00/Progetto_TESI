import logging
import math
logger = logging.getLogger(__name__)


# Soglia (numero massimo di misurazioni) per determinare la chiusura automatica di un batch.
# Deve essere una potenza di due meno uno (es. 2^12 - 1 = 4095) per garantire compatibilità
# con la struttura binaria del Merkle Tree impostata nel progetto
SOGLIA_BATCH: int = 4095

# Costante moltiplicativa per scalare la dimensione del batch
# serve per aumentare la dimensione del batch
K_BATCH_SCALING: int = 32  # Puoi modificare questo valore a piacere 2^5
SOGLIA_BATCH_MINIMA: int = 127 # soglia minima del batch 2^n - 1

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
    global SOGLIA_BATCH

    logger.debug(f"valore attuale della frequenza media {frequenza_media}")
    if frequenza_media <= 0.0:
        logger.warning("Frequenza media non valida: impossibile aggiornare la soglia.")
        return

    esponente = math.ceil(math.log2(frequenza_media))
    #potenza di due - 1
    nuova_soglia = ((2 ** esponente) * K_BATCH_SCALING) - 1

    # scegli il massimo tra i due per garantire una soglia di una certa dimensione prefissata
    soglia_finale = max(nuova_soglia, SOGLIA_BATCH_MINIMA)
    SOGLIA_BATCH = soglia_finale

    logger.debug(f"Soglia aggiornata: {SOGLIA_BATCH} "
                f"(frequenza media: {frequenza_media}, potenza: 2^{esponente}, "
                f"K = {K_BATCH_SCALING})")

def ottieni_soglia_batch() -> int:
    return SOGLIA_BATCH