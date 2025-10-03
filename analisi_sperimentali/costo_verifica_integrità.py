import os
import random
import re
import string
import time
import statistics
from pathlib import Path

from tabulate import tabulate

from file_utils import carica_file_testuale
from hashing_utils import Hashing
from merkle_tree import MerkleTree
from verificatore_utils import carica_merkle_paths_da_stringa_json

# cartella in cui si trova questo script (analisi_sperimentali)
SCRIPT_DIR = Path(__file__).resolve().parent

# percorso assoluto alla cartella merkle_paths
PERCORSO_CARTELLA = SCRIPT_DIR / "merkle_paths"

import matplotlib.pyplot as plt

def confronta_costi_verifica_integrita():
    """
    Richiama la funzione di confronto, ma invece di stampare direttamente
    la tabella, raccoglie i risultati come lista di tuple.
    """
    def formatta_tempo(sec: float) -> str:
        if sec < 1:
            return f"{sec * 1000:.3f} ms"
        else:
            return f"{sec:.2f} s"

    dati = []

    for nome_file in os.listdir(PERCORSO_CARTELLA):
        if not nome_file.endswith(".json"):
            continue
        match = re.match(r"merkle_path_(\d+)\.json", nome_file)
        if not match:
            continue

        numero_foglie = int(match.group(1))
        percorso_file = str(PERCORSO_CARTELLA / nome_file)

        stringa_json = carica_file_testuale(percorso_file)
        merkle_paths = carica_merkle_paths_da_stringa_json(stringa_json)

        merkle_root_fittizia = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

        tempi = []
        for path in merkle_paths.values():
            rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            foglia_hash = Hashing.calcola_hash(rnd)
            t0 = time.perf_counter()
            _ = MerkleTree.verifica_integrita_foglia(foglia_hash, path, merkle_root_fittizia)
            t1 = time.perf_counter()
            tempi.append(t1 - t0)

        tempo_totale = sum(tempi)
        tempo_medio = statistics.mean(tempi)
        dev_std = statistics.pstdev(tempi)
        lunghezza_path = len(merkle_paths[0].ottieni_hash_fratelli())

        dati.append((numero_foglie, tempo_totale, tempo_medio, dev_std, lunghezza_path))

    dati = sorted(dati, key=lambda x: x[0])

    # stampa tabella finale
    tabella = [
        [foglie, lunghezza,
         formatta_tempo(totale),
         formatta_tempo(medio),
         formatta_tempo(dev)]
        for foglie, totale, medio, dev, lunghezza in dati
    ]

    print(tabulate(
        tabella,
        headers=["Foglie", "Lunghezza path", "Tempo totale", "Tempo medio/foglia", "Dev std"],
        tablefmt="grid"
    ))

    return dati

def plot_costi_verifica(dati: list):
    foglie = [d[0] for d in dati]
    tempi_totali_ms = [d[1] * 1000 for d in dati]  # conversione in ms

    plt.figure(figsize=(8, 5))
    plt.plot(foglie, tempi_totali_ms, marker="o", label="Tempo totale di verifica per batch")
    plt.xscale("log", base=2)
    plt.xlabel("Numero foglie (scala log2)")
    plt.ylabel("Tempo totale (ms)")
    plt.title("Costo di verifica integrità in funzione del numero di foglie")
    plt.grid(True, which="both", linestyle="--", alpha=0.6)

    # Etichette sopra i punti in ms
    for x, y in zip(foglie, tempi_totali_ms):
        plt.annotate(f"{y:.3f}",
                     (x, y),
                     textcoords="offset points",
                     xytext=(0, 6),
                     ha="center", fontsize=8)

    plt.legend()
    plt.tight_layout()
    plt.show()



def main():
    dati : list = confronta_costi_verifica_integrita()
    plot_costi_verifica(dati)

if __name__ == "__main__":
    main()