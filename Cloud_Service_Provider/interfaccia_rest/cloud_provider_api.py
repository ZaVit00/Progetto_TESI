import uvicorn
from fastapi import FastAPI
from comuni.dati_modellati import DatiPayload

app = FastAPI()


# Indirizzo del fog node (da personalizzare se necessario)
FOG_NODE_ENDPOINT_CONFERMA = "http://127.0.0.1:8000/conferma_batch"

@app.post("/ricevi_batch")
async def ricevi_batch(payload: DatiPayload):
    print("✅ Ricevuto batch ID:", payload.batch.id_batch)
    print("📦 Numero misurazioni:", len(payload.misurazioni))
    print("🌿 Merkle Root:", payload.batch.merkle_root)
    return {"stato": "ricevuto", "batch": payload.batch.id_batch}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)