# costanti di errore durante l'elaborazione del batch
import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()


API_KEY_PRODUTTORE = os.getenv("API_KEY_PRODUTTORE")
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")


# Configurazioni produttore blockchain:
PRIVATE_KEY_BLOCKCHAIN = os.getenv("PRIVATE_KEY_BLOCKCHAIN")
ACCOUNT_ADDRESS_BLOCKCHAIN = os.getenv("ACCOUNT_ADDRESS_BLOCKCHAIN")


ERRORE_IPFS = "ERRORE_IPFS"
ERRORE_BLOCKCHAIN= "ERRORE_BLOCKCHAIN"
ERRORE_HTTP = "ERRORE_HTTP"

#soglia potenza di due - 1
SOGLIA_BATCH : int = 4095

# Costanti con valori ammissibili
TIPO_SENSORE_JOYSTICK: Final = "JOYSTICK"
TIPO_SENSORE_TEMPERATURA: Final = "TEMPERATURA"
TIPO_SENSORE_UMIDITA: Final = "UMIDITA"

ENDPOINT_CLOUD_SENSORI = "http://localhost:8080/sensori"
ENDPOINT_CLOUD_BATCH = "http://localhost:8080/batch"

#BUCKET FILEBASE
BUCKET_MERKLE_PATH = "merkle-path-batch"

#COSTANTI DB SQLITE
# Trova la directory root del progetto (2 livelli sopra gestore_db.py)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DBPATH = os.path.join(BASE_DIR, "dati_fog_node.sqlite")

#MAPPING ID_SENSORE -> TIPO
MAPPING_PREFISSO_TIPO_SENSORE = {
    "JOY": "joystick",
    "TEMP": "temperatura",
    "HUM": "umidità",
    "PRESS": "pressione"
}

# Prefissi validi che identificano le principali categorie di sensori.
# Ogni ID sensore deve iniziare con uno di questi prefissi (in lettere maiuscole).
# Esempi: JOY001 → joystick, TEMP042 → temperatura, HUM123 → umidità, PRESS999 → pressione
PREFIX_VALIDI_SENSORE = ("JOY", "TEMP", "HUM", "PRESS")

# Espressione regolare per validare l'ID del sensore.
# La stringa deve:
# - iniziare con uno dei prefissi elencati in PREFIX_VALIDI_SENSORE
# - essere seguita da esattamente tre cifre numeriche (0–9)
# Esempi validi: JOY001, TEMP123, HUM045, PRESS999
REGEX_ID_SENSORE = r"(" + "|".join(PREFIX_VALIDI_SENSORE) + r")\d{3}"

