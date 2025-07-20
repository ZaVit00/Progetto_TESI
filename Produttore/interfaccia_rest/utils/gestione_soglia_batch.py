import logging
import math
from costanti_produttore import SOGLIA_BATCH_MINIMA, FATTORE_SCALAMENTO_FREQUENZA, K_BATCH_SCALING
from istanze_globali import gestore_db

logger = logging.getLogger(__name__)


# Soglia (numero massimo di misurazioni) per determinare la chiusura automatica di un batch.
# Deve essere una potenza di due meno uno (es. 2^12 - 1 = 4095) per garantire compatibilità
# con la struttura binaria del Merkle Tree impostata nel progetto

def aggiorna_soglia_batch() -> None:
    """
    Calcola e aggiorna dinamicamente la soglia del batch in base alla frequenza media
    dei sensori registrati. La soglia è calcolata come una potenza di due scalata,
    con un limite minimo configurabile, per garantire batch sufficientemente capienti.
    """
    # 1. Ottieni la frequenza media corrente di tutti i sensori registrati
    frequenza_media: float = gestore_db.ottieni_frequenza_media_sensori()
    logger.debug(f"[Soglia Batch] Frequenza media rilevata: {frequenza_media:.2f} Hz")

    # 2. Se la frequenza media non è valida, interrompi il processo
    if frequenza_media <= 0.0:
        logger.warning("[Soglia Batch] Frequenza media non valida: impossibile calcolare la soglia.")
        return

    # 3. Scala la frequenza con un fattore configurabile
    frequenza_scalata = frequenza_media * FATTORE_SCALAMENTO_FREQUENZA
    logger.debug(f"[Soglia Batch] Frequenza scalata (fattore x{FATTORE_SCALAMENTO_FREQUENZA}): {frequenza_scalata:.2f}")

    # 4. Calcola l'esponente per ottenere la potenza di due più vicina in alto
    esponente = math.ceil(math.log2(frequenza_scalata))
    potenza_due = 2 ** esponente

    # 5. Calcola la nuova soglia come: (2^esponente * K) - 1
    nuova_soglia = (potenza_due * K_BATCH_SCALING) - 1
    logger.debug(f"[Soglia Batch] Soglia calcolata: {nuova_soglia} (2^{esponente} * {K_BATCH_SCALING} - 1)")

    # 6. Applica un valore minimo configurato, se necessario
    soglia_finale = max(nuova_soglia, SOGLIA_BATCH_MINIMA)
    logger.debug(f"[Soglia Batch] Soglia finale (dopo controllo minimo {SOGLIA_BATCH_MINIMA}): {soglia_finale}")

    # 7. Aggiorna il batch attivo (se esiste) con la nuova soglia
    esito_aggiornamento: bool = gestore_db.aggiorna_soglia(soglia_finale)

    # 8. Log di esito finale
    if esito_aggiornamento:
        logger.info(f"[Soglia Batch] Soglia batch aggiornata con successo: {soglia_finale}")
    else:
        logger.error(f"[Soglia Batch] Errore durante l'aggiornamento della soglia batch.")

