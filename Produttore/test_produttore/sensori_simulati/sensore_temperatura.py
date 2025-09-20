import random
import threading
import time
import requests

import costanti_produttore

ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazioni"
ENDPOINT_SENSORE = "http://localhost:8000/sensori"

def simula_sensore_temperatura(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0,
                                ripetizioni: int = 300, intervallo: float = 1.0, frequenza_hz: float = 1.0):
    # Attende l'avvio differito
    time.sleep(ritardo_iniziale)

    try:
        response = requests.post(ENDPOINT_SENSORE, json={
            "id_sensore": id_sensore.upper(),
            "descrizione": descrizione,
            "frequenza_hz": frequenza_hz
        })
        response.raise_for_status()
        print(f"[OK] Sensore registrato: {id_sensore.upper()} (frequenza = {frequenza_hz} Hz)")
    except requests.RequestException as e:
        print(f"[ERRORE] Registrazione sensore {id_sensore.upper()}: {e}")

    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": "",
            #"tipo": costanti_produttore.TIPO_SENSORE_TEMPERATURA,
            "valore": round(random.uniform(20.0, 30.0), 2),
        }

        try:
            response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
            response.raise_for_status()
            print(f"[OK] {id_sensore.upper()}: misurazione {i + 1} inviata")
        except requests.RequestException as e:
            print(f"[ERRORE] Invio misurazione {id_sensore.upper()}: {e}")

        time.sleep(intervallo)

# Definizione dei 30 sensori con frequenze personalizzate
sensori_temperatura = [
    ("temp001", "Sensore Temperatura 1", 0, 0.5),
    ("temp002", "Sensore Temperatura 2", 1, 0.6),
    ("temp003", "Sensore Temperatura 3", 2, 0.7),
    ("temp004", "Sensore Temperatura 4", 3, 0.8),
    ("temp005", "Sensore Temperatura 5", 4, 0.9),
    ("temp006", "Sensore Temperatura 6", 5, 1.0),
    ("temp007", "Sensore Temperatura 7", 6, 1.1),
    ("temp008", "Sensore Temperatura 8", 7, 1.2),
    ("temp009", "Sensore Temperatura 9", 8, 1.3),
    ("temp010", "Sensore Temperatura 10", 9, 1.4),
]

# Avvia ogni sensore in un thread dedicato
for id_sensore, descrizione, ritardo, freq in sensori_temperatura:
    intervallo = 1.0 / freq
    threading.Thread(
        target=simula_sensore_temperatura,
        args=(id_sensore, descrizione, ritardo, 300, intervallo, freq)
    ).start()
