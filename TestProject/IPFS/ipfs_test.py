import json
import requests
""""
# 1. Dizionario simile al merkle_paths reale
dati_merkle_paths = {
    "1025": {
        "d": "01",
        "h": ["abc123", "def456"]
    },
    "1026": {
        "d": "10",
        "h": ["ghi789", "xyz000"]
    }
}

# 2. Salviamo su file temporaneo
nome_file = "merkle_paths_test.json"
with open(nome_file, "w") as f:
    json.dump(dati_merkle_paths, f)

# 3. Aggiungiamo il file a IPFS via API
with open(nome_file, "rb") as f:
    files = {'file': f}
    response = requests.post("http://127.0.0.1:5001/api/v0/add", files=files)

# 4. Parsing della risposta per ottenere il CID
cid = response.json()["Hash"]
print(f"✅ CID ottenuto: {cid}")

# 5. Recuperiamo il contenuto via cat
params = {"arg": cid}
response_cat = requests.post("http://127.0.0.1:5001/api/v0/cat", params=params)
contenuto = response_cat.content.decode()

print("\n📦 Contenuto recuperato:")
print(contenuto)


"""""


def visualizza_contenuto_file_cid():
    # METODO PER VERIFICARE IL CONTENUTO DI UN FILE IDENTIFICATO DAL CID
    import requests
    cid = "QmZU6MZp2Y8FN5MVRqyzpgu2qfDFn2PzMNsFvHku1t7NLE"
    params = {"arg": cid}
    response = requests.post("http://127.0.0.1:5001/api/v0/cat", params=params)
    print(response.content.decode())



def visualizza_cid_nodo_locali():
    """"
        Prende e mi restituisce quali CID sono memorizzati nel nodo locale
        """
    response = requests.post("http://127.0.0.1:5001/api/v0/pin/ls", params={"type": "recursive"})
    cids = response.json()
    print(cids)

def elimina_file():
    # Lista dei CID da rimuovere
    cid_da_rimuovere = [
        "QmUNLLsPACCz1vLxQVkXqqLX5R1X345qqfHbsf67hvA3Nn",
        "QmUnkkGR4mCY72gh6Z8CgtHLSHhHZ7r1KXhdtmTRRKs5Kj",
        "QmZU6MZp2Y8FN5MVRqyzpgu2qfDFn2PzMNsFvHku1t7NLE"
    ]

    # 1. Rimuovi ogni pin
    for cid in cid_da_rimuovere:
        response = requests.post("http://127.0.0.1:5001/api/v0/pin/rm", params={"arg": cid})
        print(f"🗑️  Rimozione pin {cid}: {response.text}")

    # 2. Esegui garbage collection
    gc_response = requests.post("http://127.0.0.1:5001/api/v0/repo/gc")
    print("\n♻️  Risultato garbage collection:")
    print(gc_response.text)

if __name__ == "__main__":
    #visualizza_contenuto_file_cid()
    visualizza_cid_nodo_locali()
    #elimina_file()