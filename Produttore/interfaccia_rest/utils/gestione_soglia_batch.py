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
   dei sensori registrati.
   Logica di calcolo:
   1. Si stima la frequenza media dei sensori.
   2. Si applica un fattore di scalamento continuo (FATTORE_SCALAMENTO_FREQUENZA) per
      aumentare l'argomento di log2 e ottenere batch più capienti al crescere del carico.
   3. Si moltiplica 2^risultato del logaritmo per K_BATCH_SCALING, che è una potenza di due,
      così da garantire che la soglia finale sia della forma (2^n * K) - 1, compatibile con la struttura
      binaria del Merkle Tree utilizzata. Il - 1 è necessario perché ogni batch contiene sempre
      (2^n - 1) misurazioni + 1 che sono i dati del batch stesso che viene coinvolto nel processo di
      costruzione del merkle tree.
   4. Si applica un fallback minimo (SOGLIA_BATCH_MINIMA) per evitare batch troppo piccoli.
       """

    # --- 0. Verifica che K_BATCH_SCALING sia potenza di due ---
    if K_BATCH_SCALING <= 0 or (K_BATCH_SCALING & (K_BATCH_SCALING - 1)) != 0:
        logger.error(f"[Soglia Batch] K_BATCH_SCALING={K_BATCH_SCALING} non è una potenza di due.")
        raise ValueError

    # 1. Ottieni la frequenza media corrente di tutti i sensori registrati
    frequenza_media: float = gestore_db.ottieni_frequenza_media_sensori()
    logger.debug(f"[Soglia Batch] Frequenza media rilevata: {frequenza_media:.2f} Hz")

    # 2. Se la frequenza media non è valida, interrompi il processo
    if frequenza_media <= 0.0:
        logger.warning("[Soglia Batch] Frequenza media non valida: impossibile calcolare la soglia.")
        raise ValueError

    # 3. Scala la frequenza con un fattore configurabile
    #   serve ad aumentare l'esponente log2 in modo proporzionale al carico dei sensori.
    frequenza_scalata = frequenza_media * FATTORE_SCALAMENTO_FREQUENZA
    logger.debug(f"[Soglia Batch] Frequenza scalata (fattore x{FATTORE_SCALAMENTO_FREQUENZA}): {frequenza_scalata:.2f}")

    # 4. Calcola l'esponente per ottenere la potenza di due più vicina in alto
    esponente = math.ceil(math.log2(frequenza_scalata))
    potenza_due = 2 ** esponente

    # 5. Applica K_BATCH_SCALING (sempre potenza di due) per aumentare la capacità
    #    del batch senza modificare l'esponente log2 calcolato sopra.
    #    Risultato finale = (2^esponente * K) - 1 → compatibile con Merkle Tree binario.
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



"""
FATTORE_SCALAMENTO_FREQUENZA (non necessariamente potenza di due)->
- Agisce sul dato reale (frequenza dei sensori).
- Permette un adattamento dinamico al carico, regolando quanto aggressivamente vuoi aumentare la soglia in base ai sensori collegati.
- È un parametro continuo, puoi usare anche valori non potenze di due (es. 8.5 se volessi).

K_BATCH_SCALING (potenza di due obbligatoria) ->
- È un fattore discreto pensato solo per la compatibilità strutturale del Merkle Tree.
- Ti permette di "saltare" a batch più grandi senza toccare
  la logica dinamica e senza perdere la proprietà 2^𝑛 − 1
"""