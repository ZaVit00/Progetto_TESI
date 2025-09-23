import random
import threading
import time
import requests

import costanti_produttore
from costanti_produttore import TipoSensore

# Endpoint del server FastAPI
ENDPOINT_MISURAZIONE = "http://localhost:8000/misurazione"
ENDPOINT_SENSORE = "http://localhost:8000/sensore"

def simula_sensore_umidita(id_sensore: str, descrizione: str, ritardo_iniziale: float = 0,
                            ripetizioni: int = 300, intervallo: float = 1.0, frequenza_hz: float = 1.0):
    """
    Simula un sensore di umidità che invia dati periodicamente al fog node.
    """
    time.sleep(ritardo_iniziale)

    # Registrazione del sensore
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

    # Invio delle misurazioni
    for i in range(ripetizioni):
        dati = {
            "id_sensore": id_sensore.upper(),
            "tipo": TipoSensore.UMIDITA,
            "valore": round(random.uniform(30.0, 90.0), 2)
        }
        try:
            response = requests.post(ENDPOINT_MISURAZIONE, json=dati)
            response.raise_for_status()
            print(f"[OK] {id_sensore.upper()}: misurazione {i+1} inviata")
        except requests.RequestException as e:
            print(f"[ERRORE] Invio misurazione {id_sensore.upper()}: {e}")

        time.sleep(intervallo)

# Definizione dei sensori con frequenze personalizzate (0.5 Hz fino a 3.4 Hz)
sensori_umidita = []
for i in range(60):
    id_sensore = f"HUM{i+1:03d}"
    descrizione = f"Umidità {chr(65 + (i % 26))}{chr(65 + (i // 26)) if i >= 26 else ''}"
    ritardo = i  # ritardo progressivo
    freq = 0.5 + (i * 0.05)  # da 0.5 Hz a circa 3.45 Hz
    sensori_umidita.append((id_sensore, descrizione, ritardo, freq))

# Avvio thread per ciascun sensore
for id_sensore, descrizione, ritardo, freq in sensori_umidita:
    intervallo = 1.0 / freq
    threading.Thread(
        target=simula_sensore_umidita,
        args=(id_sensore, descrizione, ritardo, 300, intervallo, freq)
    ).start()
