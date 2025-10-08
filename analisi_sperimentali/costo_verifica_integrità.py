import os
import random
import string
import time
import statistics
from matplotlib import pyplot as plt
from tabulate import tabulate
from Classi_comuni.utils.formatta_campi import formatta_tempo
from analisi_sperimentali.config_analisi import PERCORSO_CARTELLA
from hashing_utils import Hashing
from merkle_tree import MerkleTree
from verificatore_utils import carica_merkle_paths_da_stringa_json, estrai_contenuto_merkle_path_file


def confronta_costi_verifica_integrita():
    """
    Richiama la funzione di confronto, ma invece di stampare direttamente
    la tabella, raccoglie i risultati come lista di tuple.
    """
    dati = []

    for nome_file in os.listdir(PERCORSO_CARTELLA):
        # estrazione del contenuto testuale
        risultato : tuple [int,str] | None = estrai_contenuto_merkle_path_file(nome_file, str(PERCORSO_CARTELLA))
        if risultato is None:
            continue #salta il file

        numero_foglie, stringa_json = risultato

        # estrazione del JSON
        merkle_paths = carica_merkle_paths_da_stringa_json(stringa_json)

        merkle_root_fittizia = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"

        tempi = []
        for path in merkle_paths.values():
            rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            foglia_hash = Hashing.calcola_hash(rnd)
            t0 = time.perf_counter() #avvio timer
            #processo di verifica dell'integrità
            _ = MerkleTree.verifica_integrita_foglia(foglia_hash, path, merkle_root_fittizia)
            t1 = time.perf_counter() #fine timer
            tempi.append(t1 - t0)

        #statistiche totali
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