import os
import random
import string
import time
import statistics
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from tabulate import tabulate
from Classi_comuni.utils.hashing_utils import Hashing
from Classi_comuni.merkle_tree import MerkleTree
from Classi_comuni.utils.file_utils import salva_file_generico
from Classi_comuni.utils.formatta_campi import formatta_tempo
from analisi_sperimentali.config_analisi import NUM_RUN, OUTPUT_DIR


def genera_foglie_fittizie(num_foglie: int) -> tuple[list[int], list[str]]:
    """
    Genera due liste parallele:
    - lista degli id (0..n-1)
    - lista degli hash corrispondenti
    I Merkle Tree lavorano solo su hash di dati (prescindono dal contenuto effettivo).
    """
    ids = list(range(num_foglie))
    valori_hash = []
    for _ in ids:
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        valori_hash.append(Hashing.calcola_hash(random_str)) #hash
    return ids, valori_hash


def misura_tempo_costruzione(dimensioni: list[int], num_run: int = 5):
    """
    Misura il tempo di costruzione del Merkle Tree per diverse dimensioni.
    Per ogni dimensione ripete l'esperimento num_run volte e calcola media, mediana e deviazione standard.
    Inoltre salva i Merkle Path in file JSON (una sola volta per dimensione).
    Restituisce tre liste parallele.
    """
    tempi_medi = []
    tempi_median = []
    tempi_std = []

    # nested function per salvare i Merkle Path
    def salva_merkle_path(tree, n: int):
        try:
            merkle_path_json = tree.ottieni_merkle_paths_json()
            output_file = os.path.join(OUTPUT_DIR, f"merkle_path_{n}.json")
            salva_file_generico(output_file, merkle_path_json)
            return True
        except Exception as e:
            print(f"Errore nel salvataggio dei Merkle path ({n} foglie): {e}")
            raise ValueError(f"Errore nella costruzione dei merkle path ({n} foglie): {e}")

    # ciclo principale
    for n in dimensioni:
        tempi = []
        merkle_path_salvato = False

        for run in range(num_run):
            ids, foglie_hash = genera_foglie_fittizie(n)
            merkle_tree = MerkleTree(foglie_hash, ids)

            # misura tempo costruzione albero
            t_iniziale = time.perf_counter() #timer avvio
            merkle_tree.costruisci_albero()
            t_finale = time.perf_counter() #timer stop
            tempi.append(t_finale - t_iniziale)

            # salvo Merkle Path solo al primo run della specifica dimensione
            if not merkle_path_salvato:
                merkle_path_salvato = salva_merkle_path(merkle_tree, n)

        # statistiche finali
        media = statistics.mean(tempi)
        mediana = statistics.median(tempi)
        deviazione_std = statistics.stdev(tempi) if len(tempi) > 1 else 0.0

        tempi_medi.append(media)
        tempi_median.append(mediana)
        tempi_std.append(deviazione_std)

    return tempi_medi, tempi_median, tempi_std

def stampa_tabella(dimensioni, tempi_medi, tempi_median, tempi_std):
    """
    Stampa una tabella con media, mediana e deviazione standard per ogni dimensione usando tabulate.
    I tempi vengono sempre formattati automaticamente:
    - < 1 secondo → in millisecondi
    - >= 1 secondo → in secondi
    """

    rows = []
    for d, m, md, s in zip(dimensioni, tempi_medi, tempi_median, tempi_std):
        rows.append([
            d,
            formatta_tempo(m),
            formatta_tempo(md),
            formatta_tempo(s)
        ])

    headers = ["# Foglie", "Media", "Mediana", "Dev Std"]
    table = tabulate(rows, headers=headers, tablefmt="grid")
    print(table)

    return table


def plot_risultati(dimensioni, tempi_s, usa_ms=True):
    """
    Grafico semplice e leggibile.
    - Se usa_ms=True → tempi mostrati in millisecondi
    - Se usa_ms=False → tempi mostrati in secondi
    """
    if usa_ms:
        valori = [t * 1000 for t in tempi_s]
        unita = "ms"
    else:
        valori = tempi_s
        unita = "s"

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(dimensioni, valori, marker="o")

    ax.set_xscale("log", base=2)
    ax.set_xlabel("Numero di foglie (shards)")
    ax.set_ylabel(f"Tempo medio di costruzione ({unita})")
    ax.set_title("Numero di foglie vs Latenza costruzione Merkle Tree + Path")

    ax.yaxis.set_major_locator(MaxNLocator(nbins=8))
    ax.grid(True, which="major", alpha=0.5)
    plt.show()


def plot_soglie_iniziale(dimensioni, tempi_s, usa_ms=True, max_foglie=2**9, usa_scala_log_y=True):
    """
    Grafico zoomato solo sulla parte iniziale (fino a max_foglie).
    Mostra i tempi in millisecondi o secondi, con scala lineare o logaritmica.
    max foglie = 2**9 = 512
    """
    if usa_ms:
        valori = [t * 1000 for t in tempi_s]
        unita = "ms"
    else:
        valori = tempi_s
        unita = "s"

    dim_filtrate = [d for d in dimensioni if d <= max_foglie]
    tempi_filtrati = valori[:len(dim_filtrate)]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(dim_filtrate, tempi_filtrati, marker="o", color="orange")

    ax.set_xscale("log", base=2)
    ax.set_xlabel("Numero di foglie (shards)")
    ax.set_ylabel(f"Tempo medio di costruzione ({unita})")

    # specifico se l'asse Y è log o lineare nel titolo
    scala_y = "logaritmica" if usa_scala_log_y else "lineare"
    ax.set_title(f"Andamento iniziale (fino a {max_foglie} foglie) - scala Y {scala_y}")

    if usa_scala_log_y:
        ax.set_yscale("log")
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=8))

    ax.grid(True, which="major", alpha=0.5)
    plt.show()


def main():
    potenze_due = [2**i for i in range(2, 15)]  # da 2^2 fino a 2^14 = 16384 foglie
    print("Avvio esperimenti di costruzione Merkle tree...\n")
    print(f"Statistiche calcolate su numero run {NUM_RUN} per potenze:\n{potenze_due}\n")

    tempi_medi, tempi_median, tempi_std = misura_tempo_costruzione(potenze_due, num_run=NUM_RUN)

    # grafici (con le medie)
    plot_risultati(potenze_due, tempi_medi, usa_ms=True)
    plot_soglie_iniziale(potenze_due, tempi_medi)

    # stampa tabella con media, mediana, dev std
    stampa_tabella(potenze_due, tempi_medi, tempi_median, tempi_std)

if __name__ == "__main__":
    main()
