# costanti di errore durante l'elaborazione del batch
from typing import Final

ERRORE_IPFS = "ERRORE_IPFS"
ERRORE_BLOCKCHAIN= "ERRORE_BLOCKCHAIN"
ERRORE_HTTP = "ERRORE_HTTP"

#soglia potenza di due - 1
SOGLIA_BATCH : int = 1023

# Costanti con valori ammissibili
TIPO_SENSORE_JOYSTICK: Final = "JOYSTICK"
TIPO_SENSORE_TEMPERATURA: Final = "TEMPERATURA"

ENDPOINT_CLOUD_STORAGE = "http://localhost:8080/ricevi_batch"

#BUCKET FILEBASE
BUCKET_MERKLE_PATH = "merkle-path-batch"