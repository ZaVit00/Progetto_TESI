# costanti di errore durante l'elaborazione del batch
from typing import Final

ERRORE_MERKLE_INVALIDO = "MERKLE_INVALIDO"
ERRORE_PAYLOAD_INVALIDO = "PAYLOAD_INVALIDO"

SOGLIA_BATCH : int = 63

# Costanti con valori ammissibili
TIPO_SENSORE_JOYSTICK: Final = "joystick"
TIPO_SENSORE_TEMPERATURA: Final = "temperatura"

ENDPOINT_CLOUD_STORAGE = "http://localhost:8080/ricevi_batch"

#BUCKET FILEBASE
BUCKET_MERKLE_PATH = "merkle-path-batch"