import threading
import random
import time
import requests

import costanti_produttore

ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"

def simula_sensore_temperatura(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0,
                                ripetizioni: int = 300, intervallo: float = 1.0):
    time.sleep(ritardo_iniziale)
    try:
        response = requests.post(ENDPOINT_SENSORE, json={"id_sensore": id_sensore, "descrizione": descrizione})
        response.raise_for_status()
        print(f"[OK] Sensore registrato: {id_sensore}")
    except requests.RequestException as e:
        print(f"[ERRORE] Registrazione sensore {id_sensore}: {e}")

    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": costanti_produttore.TIPO_SENSORE_TEMPERATURA,
            "valore": round(random.uniform(20.0, 30.0), 2),  # temperatura in °C
            "unita": "°C"
        }

        try:
            response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
            response.raise_for_status()
            print(f"[OK] {id_sensore}: misurazione {i + 1} inviata")
        except requests.RequestException as e:
            print(f"[ERRORE] Invio misurazione {id_sensore}: {e}")

        time.sleep(intervallo)


# Avvia 3 sensori di temperatura in parallelo usando thread
sensori_temperatura = [
    ("temp001", "Sensore Temperatura 1", 0),
    ("temp002", "Sensore Temperatura 2", 1),
    ("temp003", "Sensore Temperatura 3", 2),
    ("temp004", "Sensore Temperatura 4", 3),
    ("temp005", "Sensore Temperatura 5", 4),
    ("temp006", "Sensore Temperatura 6", 5),
    ("temp007", "Sensore Temperatura 7", 6),
    ("temp008", "Sensore Temperatura 8", 7),
    ("temp009", "Sensore Temperatura 9", 8),
    ("temp010", "Sensore Temperatura 10", 9),
    ("temp011", "Sensore Temperatura 11", 10),
    ("temp012", "Sensore Temperatura 12", 11),
    ("temp013", "Sensore Temperatura 13", 12),
    ("temp014", "Sensore Temperatura 14", 13),
    ("temp015", "Sensore Temperatura 15", 14),
    ("temp016", "Sensore Temperatura 16", 15),
    ("temp017", "Sensore Temperatura 17", 16),
    ("temp018", "Sensore Temperatura 18", 17),
    ("temp019", "Sensore Temperatura 19", 18),
    ("temp020", "Sensore Temperatura 20", 19),
    ("temp021", "Sensore Temperatura 21", 20),
    ("temp022", "Sensore Temperatura 22", 21),
    ("temp023", "Sensore Temperatura 23", 22),
    ("temp024", "Sensore Temperatura 24", 23),
    ("temp025", "Sensore Temperatura 25", 24),
    ("temp026", "Sensore Temperatura 26", 25),
    ("temp027", "Sensore Temperatura 27", 26),
    ("temp028", "Sensore Temperatura 28", 27),
    ("temp029", "Sensore Temperatura 29", 28),
    ("temp030", "Sensore Temperatura 30", 29),
]

for id_sensore, descrizione, ritardo in sensori_temperatura:
    threading.Thread(target=simula_sensore_temperatura, args=(id_sensore, descrizione, ritardo)).start()
