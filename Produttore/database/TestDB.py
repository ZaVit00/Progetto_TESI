import os
import random
import json
import sqlite3
from gestore_db import GestoreDatabase

def genera_dati_joystick():
    return {
        "x": round(random.uniform(-1.0, 1.0), 2),
        "y": round(random.uniform(-1.0, 1.0), 2),
        "pressed": random.choice([True, False])
    }

def test_inserimento_dati(db: GestoreDatabase, id_sensore: str, n: int):
    print(f"Inserimento di {n} misurazioni per il sensore '{id_sensore}'")
    db.inserisci_dati_sensore(id_sensore, "Joystick di test")
    for i in range(n):
        dati = genera_dati_joystick()
        print(db.inserisci_misurazione(id_sensore=id_sensore, dati=dati))
        print(f"  [{i+1}] {dati}")

if __name__ == "__main__":
    db = GestoreDatabase(soglia_batch=5)  # soglia bassa per test
    db.svuota_tabelle()
    test_inserimento_dati(db, id_sensore="joy_test_001", n=12)
    db.chiudi_connessione()
