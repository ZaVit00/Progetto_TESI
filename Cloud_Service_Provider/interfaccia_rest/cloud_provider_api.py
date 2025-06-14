import logging
import uvicorn
from fastapi import FastAPI
from entita.dati_modellati import DatiPayload

app = FastAPI()
# Configurazione globale del logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


@app.post("/ricevi_batch")
async def ricevi_batch(payload: DatiPayload):
    print("✅ Ricevuto batch ID:", payload.batch.id_batch)
    print("📦 Numero misurazioni:", len(payload.misurazioni))
    #CAMPO DI DEBUG DISATTIVATO print("🌿 Merkle Root:", payload.batch.merkle_root)
    return {"stato": "ricevuto", "batch": payload.batch.id_batch}


def main():
    uvicorn.run(app, host="127.0.0.1", port=8080)


if __name__ == "__main__":
    main()