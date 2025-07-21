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
            "tipo": "vagangul a mamt",
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
    ("temp011", "Sensore Temperatura 11", 10, 1.5),
    ("temp012", "Sensore Temperatura 12", 11, 1.6),
    ("temp013", "Sensore Temperatura 13", 12, 1.7),
    ("temp014", "Sensore Temperatura 14", 13, 1.8),
    ("temp015", "Sensore Temperatura 15", 14, 1.9),
    ("temp016", "Sensore Temperatura 16", 15, 2.0),
    ("temp017", "Sensore Temperatura 17", 16, 2.1),
    ("temp018", "Sensore Temperatura 18", 17, 2.2),
    ("temp019", "Sensore Temperatura 19", 18, 2.3),
    ("temp020", "Sensore Temperatura 20", 19, 2.4),
    ("temp021", "Sensore Temperatura 21", 20, 2.5),
    ("temp022", "Sensore Temperatura 22", 21, 2.6),
    ("temp023", "Sensore Temperatura 23", 22, 2.7),
    ("temp024", "Sensore Temperatura 24", 23, 2.8),
    ("temp025", "Sensore Temperatura 25", 24, 2.9),
    ("temp026", "Sensore Temperatura 26", 25, 3.0),
    ("temp027", "Sensore Temperatura 27", 26, 3.1),
    ("temp028", "Sensore Temperatura 28", 27, 3.2),
    ("temp029", "Sensore Temperatura 29", 28, 3.3),
    ("temp030", "Sensore Temperatura 30", 29, 3.4),
]

# Avvia ogni sensore in un thread dedicato
for id_sensore, descrizione, ritardo, freq in sensori_temperatura:
    intervallo = 1.0 / freq
    threading.Thread(
        target=simula_sensore_temperatura,
        args=(id_sensore, descrizione, ritardo, 300, intervallo, freq)
    ).start()
