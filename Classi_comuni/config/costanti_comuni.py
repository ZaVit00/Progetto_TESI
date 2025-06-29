#MEMORIZZA LE COSTANTI
from pathlib import Path

ID_BATCH_LOGICO = 0

# Percorso assoluto alla radice del progetto (es. Progetto_TESI)
ROOT_DIR = Path(__file__).resolve().parents[2]
# Percorsi dei file ABI e indirizzo contratto
PERCORSO_ABI = ROOT_DIR / "Classi_comuni" / "blockchain" / "build" / "abi.json"
PERCORSO_INDIRIZZO_CONTRATTO = ROOT_DIR / "Classi_comuni" / "blockchain" / "build" / "indirizzo.txt"

#indirizzo ip + porta default di GANACHE locale
PROVIDER_URL = "http://127.0.0.1:8545"