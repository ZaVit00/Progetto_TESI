import threading
import random
import time
import requests

import costanti_produttore

ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"

def simula_sensore(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0, ripetizioni: int = 300, intervallo: float = 1.0):

    time.sleep(ritardo_iniziale)
    try:
        response = requests.post(ENDPOINT_SENSORE, json={"id_sensore": id_sensore.upper(), "descrizione": descrizione})
        response.raise_for_status()
        print(f"[OK] Sensore registrato: {id_sensore}")
    except requests.RequestException as e:
        print(f"[ERRORE] Registrazione sensore {id_sensore}: {e}")

    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": costanti_produttore.TIPO_SENSORE_JOYSTICK,
            "x": round(random.uniform(-1, 1), 2),
            "y": round(random.uniform(-1, 1), 2),
            "pressed": random.choice([True, False])
        }
        try:
            response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
            response.raise_for_status()
            print(f"[OK] {id_sensore}: misurazione {i+1} inviata")
        except requests.RequestException as e:
            print(f"[ERRORE] Invio misurazione {id_sensore}: {e}")

        time.sleep(intervallo)

# Avvia 3 sensori in parallelo usando thread
sensori = [
    ("joy001", "Joystick A", 0),
    ("joy002", "Joystick B", 1),
    ("joy003", "Joystick C", 2),
    ("joy004", "Joystick D", 3),
    ("joy005", "Joystick E", 4),
    ("joy005", "Joystick F", 5),
    ("joy006", "Joystick G", 6),
    ("joy007", "Joystick H", 7),
    ("joy008", "Joystick I", 8),
    ("joy009", "Joystick II", 9),
    ("joy010", "Joystick III", 10),
]

for id_sensore, descrizione, ritardo in sensori:
    threading.Thread(target=simula_sensore, args=(id_sensore, descrizione, ritardo)).start()
