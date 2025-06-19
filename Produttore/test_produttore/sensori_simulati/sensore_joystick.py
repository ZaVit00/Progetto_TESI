import random
import threading
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
sensori_joystick = [
    ("joy001", "Joystick A", 0),
    ("joy002", "Joystick B", 1),
    ("joy003", "Joystick C", 2),
    ("joy004", "Joystick D", 3),
    ("joy005", "Joystick E", 4),
    ("joy006", "Joystick F", 5),
    ("joy007", "Joystick G", 6),
    ("joy008", "Joystick H", 7),
    ("joy009", "Joystick I", 8),
    ("joy010", "Joystick J", 9),
    ("joy011", "Joystick K", 10),
    ("joy012", "Joystick L", 11),
    ("joy013", "Joystick M", 12),
    ("joy014", "Joystick N", 13),
    ("joy015", "Joystick O", 14),
    ("joy016", "Joystick P", 15),
    ("joy017", "Joystick Q", 16),
    ("joy018", "Joystick R", 17),
    ("joy019", "Joystick S", 18),
    ("joy020", "Joystick T", 19),
    ("joy021", "Joystick U", 20),
    ("joy022", "Joystick V", 21),
    ("joy023", "Joystick W", 22),
    ("joy024", "Joystick X", 23),
    ("joy025", "Joystick Y", 24),
    ("joy026", "Joystick Z", 25),
    ("joy027", "Joystick AA", 26),
    ("joy028", "Joystick AB", 27),
    ("joy029", "Joystick AC", 28),
    ("joy030", "Joystick AD", 29),
]


for id_sensore, descrizione, ritardo in sensori_joystick:
    threading.Thread(target=simula_sensore, args=(id_sensore, descrizione, ritardo)).start()
