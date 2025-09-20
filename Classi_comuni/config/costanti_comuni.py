#MEMORIZZA LE COSTANTI
from pathlib import Path
from enum import Enum

#ID del batch logico (necessario per la costruzione dell'albero di merkle)
ID_BATCH_LOGICO = 0

# Percorso assoluto alla radice del progetto (es. Progetto_TESI)
ROOT_DIR = Path(__file__).resolve().parents[2]

# Percorsi dei file ABI e indirizzo contratto
PERCORSO_ABI = ROOT_DIR / "Classi_comuni" / "blockchain" / "build" / "abi.json"
PERCORSO_INDIRIZZO_CONTRATTO = ROOT_DIR / "Classi_comuni" / "blockchain" / "build" / "indirizzo.txt"

#indirizzo IP + porta default di GANACHE locale
PROVIDER_BLOCKCHAIN_URL = "http://127.0.0.1:7545"

#Enumerativo che gestisce le tipologie di servizio (utilizzato nel logger centralizzato)
class TipoServizio(str, Enum):
    PRODUTTORE = "Produttore"
    VERIFICATORE = "Verificatore"
    CLOUD = "Cloud_Service_Provider"
    PRODUTTORE_VERIFICATORE = "Produttore_Verificatore"
