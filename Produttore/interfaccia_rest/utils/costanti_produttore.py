# costanti di errore durante l'elaborazione del batch
from typing import Final

ERRORE_MERKLE_INVALIDO = "MERKLE_INVALID"
ERRORE_PAYLOAD_INVALIDO = "PAYLOAD_INVALID"

SOGLIA_BATCH : int = 63

# Costanti con valori ammissibili
TIPO_SENSORE_JOYSTICK: Final = "joystick"
TIPO_SENSORE_TEMPERATURA: Final = "temperatura"

ENDPOINT_CLOUD = "http://localhost:8080/ricevi_batch"