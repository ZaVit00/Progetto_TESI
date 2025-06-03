import uvicorn
from interfaccia_rest.cloud_provider_api import app  # Importa l'app FastAPI

#avvia il server uvicorn su 127.0.0.1 e porta 8080
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)