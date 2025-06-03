from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json

app = FastAPI()

# Lista globale per memorizzare gli ID dei batch ricevuti
batch_ids_ricevuti = []

@app.post("/api/invia")
async def ricevi_batch(request: Request):
    try:
        payload = await request.json()
        print("[INFO] Batch ricevuto dal nodo fog:")
        print(json.dumps(payload, indent=2))

        # Estrai e salva l'id_batch
        id_batch = payload.get("batch", {}).get("id_batch")
        if id_batch is not None:
            batch_ids_ricevuti.append(id_batch)

        return JSONResponse(content={"status": "ricevuto", "messaggio": "Batch acquisito correttamente."})
    except Exception as e:
        print(f"[ERRORE] Fallita la ricezione del batch: {e}")
        return JSONResponse(status_code=400, content={"status": "errore", "messaggio": str(e)})

@app.on_event("shutdown")
def stampa_batch_ricevuti():
    print("\n[INFO] ID dei batch ricevuti durante l'esecuzione:")
    for batch_id in batch_ids_ricevuti:
        print(f"- Batch ID: {batch_id}")
