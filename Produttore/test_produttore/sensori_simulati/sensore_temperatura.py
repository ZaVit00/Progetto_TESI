import threading
import random
import time
import requests
ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"

def simula_sensore_temperatura(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0,
                                ripetizioni: int = 100, intervallo: float = 1.0):
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
    ("temp003", "Sensore Temperatura 3", 2)
]

for id_sensore, descrizione, ritardo in sensori_temperatura:
    threading.Thread(target=simula_sensore_temperatura, args=(id_sensore, descrizione, ritardo)).start()
