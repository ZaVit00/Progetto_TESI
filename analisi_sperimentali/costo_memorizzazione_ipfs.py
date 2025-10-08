import os
from matplotlib import pyplot as plt
from Classi_comuni.utils.formatta_campi import formatta_dimensione
from analisi_sperimentali.config_analisi import PERCORSO_CARTELLA, BUCKET_TEST, PERCORSO_FILE_DIZ_CID
from dict_utils import serializza_dict_pretty
from elaborazione_batch import carica_merkle_path_ipfs
from file_utils import salva_file_generico, carica_contenuto_json_da_file
from tabulate import tabulate
from Verificatore.api_client.ipfs_client import  ottieni_file_da_ipfs
from verificatore_utils import estrai_contenuto_merkle_path_file



def caricamento_merkle_paths_ipfs(esegui_upload: bool = False) -> dict:
    """
    Se esegui_upload=True:
        carica i file locali su IPFS (compresso e non compresso),
        genera un nuovo dizionario {foglie: (cid_noncompresso, cid_compresso)}.
    Se esegui_upload=False:
        ricarica il dizionario salvato in precedenza.
    """
    risultati = {}

    if not esegui_upload:
        # recupero da file già serializzato
        if not os.path.exists(PERCORSO_FILE_DIZ_CID):
            raise FileNotFoundError("Nessun dizionario CID salvato trovato.")

        return carica_contenuto_json_da_file(str(PERCORSO_FILE_DIZ_CID))

    # --- LOGICA DI UPLOAD ---
    for nome_file in os.listdir(PERCORSO_CARTELLA):
        # estrazione del contenuto testuale
        risultato : tuple [int, str] | None = estrai_contenuto_merkle_path_file(nome_file, str(PERCORSO_CARTELLA))
        if risultato is None:
            continue #salta il file

        numero_foglie, merkle_path_str = risultato

        cid_noncompresso = carica_merkle_path_ipfs(
            merkle_path_str, nome_bucket=BUCKET_TEST, comprimi_dimensione=False
        )
        cid_compresso = carica_merkle_path_ipfs(
            merkle_path_str, nome_bucket=BUCKET_TEST, comprimi_dimensione=True
        )

        risultati[numero_foglie] = (cid_noncompresso, cid_compresso)
        print(f"[OK] {numero_foglie} foglie → Non compresso: {cid_noncompresso}, Compresso: {cid_compresso}")

    # salvo il dizionario in un file interno
    salva_file_generico(PERCORSO_FILE_DIZ_CID, serializza_dict_pretty(risultati))
    print("Salvataggio del file effettuato con successo")
    return risultati



def confronta_dimensioni_file_caricati(dizionario_cid: dict):
    risultati_tabella = []
    dict_dimensioni = {}  # nuovo dict: {foglie: (MB_nc, MB_c)}

    for foglie in sorted(dizionario_cid.keys(), key=lambda x: int(x)):
        cid_nc, cid_c = dizionario_cid[foglie]

        _, dim_nc = ottieni_file_da_ipfs(cid_nc)  # byte
        _, dim_c = ottieni_file_da_ipfs(cid_c)    # byte

        # calcola risparmio %
        risparmio = ((dim_nc - dim_c) / dim_nc) * 100 if dim_nc > 0 else 0.0

        # aggiorno tabella
        risultati_tabella.append([
            int(foglie),
            formatta_dimensione(dim_nc),
            formatta_dimensione(dim_c),
            f"{risparmio:.1f} %"
        ])

        # aggiorno nuovo dict (in MB per plotting)
        dict_dimensioni[int(foglie)] = (
            dim_nc / (1024 * 1024),
            dim_c / (1024 * 1024))

    print("\n\n")
    print(tabulate(
        risultati_tabella,
        headers=["Foglie", "Dim non compresso", "Dim compresso", "Risparmio"],
        tablefmt="grid"
    ))

    return dict_dimensioni


def plot_dimensioni_file(dict_dimensioni: dict):
    foglie = sorted(dict_dimensioni.keys())
    dim_nc = [dict_dimensioni[f][0] for f in foglie]
    dim_c  = [dict_dimensioni[f][1] for f in foglie]

    plt.figure(figsize=(8,5))
    plt.plot(foglie, dim_nc, marker="o", label="Non compresso")
    plt.plot(foglie, dim_c, marker="s", label="Compresso (gzip)")

    plt.xscale("log", base=2)
    plt.xlabel("Numero di foglie (scala log)")
    plt.ylabel("Dimensione file (MB)")
    plt.yscale("log")
    plt.title("Crescita dimensioni: non compresso vs compresso (gzip)")
    plt.legend()
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


def main():
    # qui scegli tu: se vuoi forzare un nuovo upload metti True
    dizionario_cid = caricamento_merkle_paths_ipfs(esegui_upload=False)

    print("\nDizionario CID caricato (numero foglie -> (cid NON compresso; cid compresso):")
    for foglie, (cid_nc, cid_c) in dizionario_cid.items():
        print(f"{foglie} foglie → non compresso={cid_nc}, compresso={cid_c}")

    dict_dimensioni = confronta_dimensioni_file_caricati(dizionario_cid)
    plot_dimensioni_file(dict_dimensioni)

if __name__ == "__main__":
    main()
