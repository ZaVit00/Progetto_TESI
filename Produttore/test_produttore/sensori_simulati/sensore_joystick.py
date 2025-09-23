import random
import threading
import time
import requests
import costanti_produttore
from costanti_produttore import TipoSensore

ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazione"
ENDPOINT_SENSORE = "http://localhost:8000/sensore"

def simula_sensore(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0,
                   ripetizioni: int = 300, intervallo: float = 1.0, frequenza_hz: float = 1.0):
    time.sleep(ritardo_iniziale)
    try:
        response = requests.post(ENDPOINT_SENSORE, json={
            "id_sensore": id_sensore.upper(),
            "descrizione": descrizione,
            "frequenza_hz": frequenza_hz
        })
        response.raise_for_status()
        print(f"[OK] Sensore registrato: {id_sensore} (frequenza = {frequenza_hz} Hz)")
    except requests.RequestException as e:
        print(f"[ERRORE] Registrazione sensore {id_sensore}: {e}")

    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": TipoSensore.JOYSTICK.value,
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

# Lista di 10 sensori con frequenze differenti (Hz)
sensori_joystick = [
    ("joy001", "Joystick A", 0, 0.5),   # 1 misurazione ogni 2.0 s
    ("joy002", "Joystick B", 1, 1.0),   # 1 misurazione ogni 1.0 s
    ("joy003", "Joystick C", 2, 1.5),   # 1 misurazione ogni 0.66 s
    ("joy004", "Joystick D", 3, 2.0),   # 1 misurazione ogni 0.5 s
    ("joy005", "Joystick E", 4, 0.8),   # 1 misurazione ogni 1.25 s
    ("joy006", "Joystick F", 5, 1.2),   # 1 misurazione ogni 0.83 s
    ("joy007", "Joystick G", 6, 0.9),   # 1 misurazione ogni 1.11 s
    ("joy008", "Joystick H", 7, 1.8),   # 1 misurazione ogni 0.55 s
    ("joy009", "Joystick I", 8, 2.5),   # 1 misurazione ogni 0.4 s
    ("joy010", "Joystick J", 9, 1.1),   # 1 misurazione ogni 0.91 s
]

for id_sensore, descrizione, ritardo, freq in sensori_joystick:
    intervallo = 1.0 / freq  # converte Hz in secondi di attesa
    threading.Thread(target=simula_sensore, args=(id_sensore, descrizione, ritardo, 300, intervallo, freq)).start()

# MEDIA ARITMETICA FREQUENZE:
# (0.5 + 1.0 + 1.5 + 2.0 + 0.8 + 1.2 + 0.9 + 1.8 + 2.5 + 1.1) / 10 = 1.33 Hz
