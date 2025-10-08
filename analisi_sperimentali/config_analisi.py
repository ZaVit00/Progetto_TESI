import os
from pathlib import Path

# cartella in cui si trova questo script (analisi_sperimentali)
SCRIPT_DIR = Path(__file__).resolve().parent
# percorso assoluto alla cartella merkle_paths
PERCORSO_CARTELLA = SCRIPT_DIR / "merkle_paths_sperimentali"
#bucket per ipfs
BUCKET_TEST = "merkle-path-batch-sperimentale"
#dizionario dei cid utilizzato per analizzare il costo di memorizzazione di IPFS
PERCORSO_FILE_DIZ_CID = str(PERCORSO_CARTELLA / "dizionario_cid.json")

NUM_RUN = 5  # numero di run eseguite per ogni dimensione
OUTPUT_DIR = os.path.join(os.getcwd(), "merkle_paths_sperimentali")
# cartella di output nella dir corrente
os.makedirs(OUTPUT_DIR, exist_ok=True)