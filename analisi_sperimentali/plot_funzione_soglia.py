import math
from matplotlib import pyplot as plt

def plot_funzione_soglia_batch(
    durata_finestra_sec: int = 60,
    soglia_minima: int = 255,
    soglia_massima: int = 4095,
    max_somma_frequenze: int = 200
) -> None:
    """
    Plotta l'andamento della soglia batch (2^n - 1) in funzione della somma delle frequenze dei sensori.
    Mostra inoltre una legenda con i valori di soglia minima e massima.

    :param durata_finestra_sec: Finestra temporale usata per il calcolo (es. 60s)
    :param soglia_minima: valore minimo accettabile per la soglia
    :param soglia_massima: valore massimo accettabile per la soglia
    :param max_somma_frequenze: massimo valore simulato della somma delle frequenze
    """
    frequenze_totali = list(range(1, max_somma_frequenze + 1))
    soglie_batch = []

    for somma_freq in frequenze_totali:
        misure_attese = somma_freq * durata_finestra_sec
        potenza_due = 2 ** math.ceil(math.log2(misure_attese))
        soglia = max(potenza_due - 1, soglia_minima)
        soglia = min(soglia, soglia_massima)
        soglie_batch.append(soglia)

    plt.figure(figsize=(10, 5))
    plt.plot(frequenze_totali, soglie_batch, linestyle='-', label="Soglia dinamica")

    # Linee orizzontali per soglia min e max
    plt.axhline(y=soglia_minima, color='green', linestyle='--', linewidth=1.2, label=f"Soglia minima = {soglia_minima}")
    plt.axhline(y=soglia_massima, color='red', linestyle='--', linewidth=1.2, label=f"Soglia massima = {soglia_massima}")

    plt.title(f"Andamento soglia batch (finestra = {durata_finestra_sec}s)")
    plt.xlabel("Somma frequenze sensori [Hz]")
    plt.ylabel("Soglia batch (2^n - 1)")
    plt.yticks([2**n - 1 for n in range(8, 13)])  # da 255 a 4095
    plt.grid(True, linestyle='--', linewidth=0.5)

    # Legenda accanto al grafico
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_funzione_soglia_batch()