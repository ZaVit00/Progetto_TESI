from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import json

app = FastAPI()

# Lista per tenere traccia dei batch ricevuti (in memoria)
batch_ids_ricevuti = []

# Indirizzo del fog node (da personalizzare se necessario)
FOG_NODE_ENDPOINT_CONFERMA = "http://127.0.0.1:8000/conferma_batch"

@app.post("/api/invia")
async def ricevi_batch(request: Request):
    try:
        payload = await request.json()
        print("[INFO] Batch ricevuto dal nodo fog:")
        print(json.dumps(payload, indent=2))

        # Estrai l'id del batch
        id_batch = payload.get("batch", {}).get("id_batch")
        print(f"[DEBUG] ID del Batch ricevuto dal produttore:")
        if id_batch is not None:
            batch_ids_ricevuti.append(id_batch)
            # Costruisci il messaggio di conferma
            conferma = {
                "id_batch": id_batch,
                "messaggio": "Batch ricevuto e salvato correttamente dal cloud."
            }

            # Invia la conferma al fog node
            try:
                response = requests.post(FOG_NODE_ENDPOINT_CONFERMA, json=conferma)
                response.raise_for_status()
                print(f"[INFO] Conferma di ricezione inviata al nodo fog per batch {id_batch}")
            except requests.RequestException as e:
                print(f"[ERRORE] Fallita la conferma al nodo fog per il batch {id_batch}: {e}")

        return JSONResponse(content={"status": "ricevuto", "messaggio": "Batch acquisito correttamente."})
    except Exception as e:
        print(f"[ERRORE] Fallita la ricezione del batch: {e}")
        return JSONResponse(status_code=400, content={"status": "errore", "messaggio": str(e)})
