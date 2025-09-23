import math
import matplotlib.pyplot as plt
import numpy as np

# Parametri
SOGLIA_BATCH_MINIMA = 31
SOGLIA_BATCH_MASSIMA = 2**12 - 1  # esempio limite
TARGET_WINDOW_S = 15.0
EMA_ALPHA = 0.3
K_BATCH_SCALING = 1

def _ceil_pow2_minus1(x: float) -> int:
    return (2 ** math.ceil(math.log2(x))) - 1

def calcola_soglia_dinamica(rate_tot: float, soglia_precedente=None) -> int:
    """Versione semplificata: senza EMA per grafico statico."""
    n_atteso = rate_tot * TARGET_WINDOW_S
    n_atteso *= K_BATCH_SCALING
    soglia = _ceil_pow2_minus1(n_atteso + 1.0)
    soglia = max(SOGLIA_BATCH_MINIMA, min(soglia, SOGLIA_BATCH_MASSIMA))

    if soglia_precedente is not None and soglia < soglia_precedente:
        soglia = soglia_precedente

    return soglia

# Intervallo di rate totali (0.1 Hz fino a 100 Hz)
rate_totali = np.linspace(0.1, 100, 500)
soglie = [calcola_soglia_dinamica(r) for r in rate_totali]
potenze = [2**n - 1 for n in range(5, 13)]  # da 2^5-1=31 a 2^12-1=4095

# Plot
plt.figure(figsize=(10, 6))
plt.plot(rate_totali, soglie, drawstyle="steps-post", label="Soglia finale (2^n - 1)")
plt.xlabel("Rate totale di arrivo (Hz)")
plt.ylabel("Soglia batch")
plt.title("Comportamento della soglia dinamica (quantizzata a 2^n - 1)")
plt.yticks(potenze)
plt.legend()
plt.grid(True, which="both", linestyle="--", alpha=0.6)
plt.show()