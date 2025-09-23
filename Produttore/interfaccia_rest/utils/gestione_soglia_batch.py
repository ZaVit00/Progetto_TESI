import logging
import math
from costanti_comuni import TipoServizio
from costanti_produttore import SOGLIA_BATCH_MINIMA, FATTORE_SCALAMENTO_FREQUENZA, K_BATCH_SCALING
from istanze_globali_produttore import gestore_db
from registro_log import setup_logger

logger = setup_logger(TipoServizio.PRODUTTORE, module=__name__, level=logging.DEBUG)

""" FATTORE_SCALAMENTO_FREQUENZA (non necessariamente potenza di due)-> 
- Agisce sul dato reale (frequenza dei sensori). 
- Permette un adattamento dinamico al carico, regolando quanto aggressivamente vuoi aumentare 
  la soglia in base ai sensori collegati. 
- È un parametro continuo, puoi usare anche valori non potenze di due (es. 8.5 se volessi). 

K_BATCH_SCALING (potenza di due obbligatoria) -> 
- È un fattore discreto pensato solo per la compatibilità strutturale del Merkle Tree. 
- Ti permette di "saltare" a batch più  grandi senza toccare la logica dinamica e senza 
  perdere la proprietà 2^𝑛 − 1 """

def aggiorna_soglia_chiusura_batch() -> None:
    """
    Calcola e aggiorna dinamicamente la soglia di chiusura dei batch.

    Pipeline logica:
    1. Recupera la frequenza media dei sensori dal DB
    2. Applica un fattore di scalamento continuo (elasticità rispetto al carico)
    3. Arrotonda alla potenza di due immediatamente superiore (compatibilità binaria)
    4. Applica uno scaling discreto opzionale (K_BATCH_SCALING, potenza di due)
    5. Applica il -1 finale per avere (2^n - 1) misurazioni + 1 tupla batch (compatibilità Merkle Tree)
    6. Applica un valore minimo configurato per evitare batch troppo piccoli
    7. Aggiorna la soglia nel DB
    """

    # --- 0. Verifica che K_BATCH_SCALING sia valido ---
    if K_BATCH_SCALING <= 0 or (K_BATCH_SCALING & (K_BATCH_SCALING - 1)) != 0:
        logger.error(f"[Soglia Batch] K_BATCH_SCALING={K_BATCH_SCALING} non è una potenza di due.")
        raise ValueError

    # --- 1. Frequenza media dal DB ---
    frequenza_media: float = gestore_db.ottieni_frequenza_media_sensori()
    logger.debug(f"[Soglia Batch] Frequenza media rilevata: {frequenza_media:.2f} Hz")

    if frequenza_media <= 0.0:
        logger.warning("[Soglia Batch] Frequenza media non valida: impossibile calcolare la soglia.")
        raise ValueError

    # --- 2. Adattamento al carico ---
    frequenza_scalata = frequenza_media * FATTORE_SCALAMENTO_FREQUENZA
    logger.debug(f"[Soglia Batch] Frequenza scalata (x{FATTORE_SCALAMENTO_FREQUENZA}): {frequenza_scalata:.2f}")

    # --- 3. Quantizzazione a potenza di due ---
    esponente = math.ceil(math.log2(frequenza_scalata))
    potenza_due = 2 ** esponente
    logger.debug(f"[Soglia Batch] Potenza di due più vicina: 2^{esponente} = {potenza_due}")

    # --- 4. Scaling discreto (opzionale, potenza di due) ---
    soglia_scalata = potenza_due * K_BATCH_SCALING
    logger.debug(f"[Soglia Batch] Dopo scaling discreto (x{K_BATCH_SCALING}): {soglia_scalata}")

    # --- 5. Compatibilità Merkle Tree ---
    nuova_soglia = soglia_scalata - 1
    logger.debug(f"[Soglia Batch] Forma compatibile con Merkle Tree: {nuova_soglia} = ({soglia_scalata} - 1)")

    # --- 6. Fallback minimo ---
    soglia_finale = max(nuova_soglia, SOGLIA_BATCH_MINIMA)
    logger.debug(f"[Soglia Batch] Soglia finale (min {SOGLIA_BATCH_MINIMA}): {soglia_finale}")

    # --- 7. Aggiornamento DB ---
    esito_aggiornamento: bool = gestore_db.aggiorna_soglia_batch(soglia_finale)

    if esito_aggiornamento:
        logger.info(f"[Soglia Batch] Soglia batch aggiornata con successo: {soglia_finale}")
    else:
        logger.error("[Soglia Batch] Errore durante l'aggiornamento della soglia batch.")
