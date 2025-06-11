import hashlib
import json
import requests
import tempfile
import os

# === STEP 1: GENERAZIONE DATI E MERKLE TREE ===

def hash_concat(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode()).hexdigest()

def calcola_hash_foglia(foglia_raw: str) -> str:
    return hashlib.sha256(foglia_raw.encode()).hexdigest()

class MerkleTree:
    def __init__(self, foglie_hash, mappa_id):
        if len(foglie_hash) & (len(foglie_hash) - 1) != 0:
            raise ValueError("Numero di foglie non è potenza di due")
        self.foglie_hash = foglie_hash
        self.mappa_id = mappa_id
        self.proofs = {id_: [] for id_ in mappa_id}
        self.root = None

    def _aggiorna_proofs(self, gruppo_sx, gruppo_dx, elem_sx, elem_dx):
        for idx in gruppo_sx:
            self.proofs[idx].append((0, elem_dx))
        for idx in gruppo_dx:
            self.proofs[idx].append((1, elem_sx))

    def costruisci(self):
        livello = list(self.foglie_hash)
        indici = [[id_] for id_ in self.mappa_id]
        while len(livello) > 1:
            nuovo_livello = []
            nuovi_indici = []
            for i in range(0, len(livello), 2):
                sx = livello[i]
                dx = livello[i + 1]
                padre = hash_concat(sx, dx)
                nuovo_livello.append(padre)
                self._aggiorna_proofs(indici[i], indici[i + 1], sx, dx)
                nuovi_indici.append(indici[i] + indici[i + 1])
            livello = nuovo_livello
            indici = nuovi_indici
        self.root = livello[0]
        return self.root

def verifica_misurazione(valore, path, root_attesa):
    h = calcola_hash_foglia(valore)
    for d, fratello in zip(path["d"], path["h"]):
        if d == "1":
            h = hash_concat(fratello, h)
        else:
            h = hash_concat(h, fratello)
    return h == root_attesa


def test():
    # Misurazioni simulate (ordinamento per chiave intera)
    misurazioni = {
        1025: "temp=24.5;ts=1620001",
        1026: "temp=24.7;ts=1620002",
        1042: "temp=25.0;ts=1www3620003",
        1099: "temp=25.2;ts=1620004"
    }
    misurazioni_ordinate = dict(sorted(misurazioni.items()))
    foglie_hash = [calcola_hash_foglia(v) for v in misurazioni_ordinate.values()]
    ids = list(misurazioni_ordinate.keys())
    albero = MerkleTree(foglie_hash, ids)
    merkle_root_misurazioni = albero.costruisci()
    # Costruzione Merkle Paths in formato compatto

    # === STEP 2: SALVATAGGIO SU IPFS ===
    # Salviamo su file temporaneo
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8") as tmpfile:
        json.dump(proofs_compatti, tmpfile)
        path_file = tmpfile.name
    # Carichiamo su IPFS
    with open(path_file, "rb") as f:
        files = {'file': f}
        response = requests.post("http://127.0.0.1:5001/api/v0/add", files=files)
        cid = response.json()["Hash"]
        print(f"questo è il CID del file {cid}")
    # Rimuoviamo il file temporaneo
    os.remove(path_file)
    # === STEP 3: VERIFICA DA "VERIFICATORE ESTERNO" ===
    # Recupero via /api/v0/cat
    params = {"arg": cid}
    resp = requests.post("http://127.0.0.1:5001/api/v0/cat", params=params)
    proofs_recuperati = json.loads(resp.content)
    # Verifica
    esiti = {}
    for id_, valore in misurazioni_ordinate.items():
        path = proofs_recuperati[str(id_)]
        esito = verifica_misurazione(valore, path, merkle_root_misurazioni)
        esiti[id_] = esito
    # Stampa risultati
    print("\n📋 Risultati Verifica delle Misurazioni:")
    print("-" * 40)
    for id_, esito in esiti.items():
        stato = "✅ OK" if esito else "❌ FALLITA"
        print(f"ID {id_}: {stato}")
    print("-" * 40)
    return merkle_root_misurazioni


def test_corruzione(merkle_root: str):
    # Recupero via /api/v0/cat
    params = {"arg": "QmcuZqAHddNEUeVKfVuP354MCMqL8TPvQajdoLVzSvTUNX"}
    resp = requests.post("http://127.0.0.1:5001/api/v0/cat", params=params)
    proofs_recuperati = json.loads(resp.content)

    # Modifica simulata: altero il valore della misurazione con ID 1025
    misurazioni = {
        1025: "temp=30.5;ts=1620001",  # <-- CORROTTA
        1026: "temp=24.7;ts=1620002",
        1042: "temp=25.0;ts=1www3620003",
        1099: "temp=5324r4335.2;ts=1620004"
    }
    misurazioni_ordinate = dict(sorted(misurazioni.items()))

    # Verifica
    esiti = {}
    for id_, valore in misurazioni_ordinate.items():
        path = proofs_recuperati[str(id_)]
        esito = verifica_misurazione(valore, path, merkle_root)
        esiti[id_] = esito

    # Stampa risultati
    print("\n📋 Risultati Verifica con Corruzione:")
    print("-" * 40)
    for id_, esito in esiti.items():
        stato = "✅ OK" if esito else "❌ FALLITA"
        print(f"ID {id_}: {stato}")
    print("-" * 40)



if __name__ == "__main__":
    mt = test()
    test_corruzione(mt)