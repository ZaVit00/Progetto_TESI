# costanti di errore durante l'elaborazione del batch
import os
from typing import Final

from dotenv import load_dotenv

load_dotenv()

API_KEY_PRODUTTORE = os.getenv("API_KEY_PRODUTTORE")
AWS_ACCESS_KEY_ID=os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")

ERRORE_IPFS = "ERRORE_IPFS"
ERRORE_BLOCKCHAIN= "ERRORE_BLOCKCHAIN"
ERRORE_HTTP = "ERRORE_HTTP"

#soglia potenza di due - 1
SOGLIA_BATCH : int = 1023

# Costanti con valori ammissibili
TIPO_SENSORE_JOYSTICK: Final = "JOYSTICK"
TIPO_SENSORE_TEMPERATURA: Final = "TEMPERATURA"

ENDPOINT_CLOUD_SENSORI = "http://localhost:8080/sensori"
ENDPOINT_CLOUD_BATCH = "http://localhost:8080/batch"

#BUCKET FILEBASE
BUCKET_MERKLE_PATH = "merkle-path-batch"