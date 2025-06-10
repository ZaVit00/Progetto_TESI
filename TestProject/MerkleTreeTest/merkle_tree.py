import hashlib
from typing import List, Dict, Tuple, Optional


def hash_concat(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode()).hexdigest()


def calcola_hash_foglia(foglia_raw: str) -> str:
    return hashlib.sha256(foglia_raw.encode()).hexdigest()


class MerkleTree:
    def __init__(self, foglie_hash: List[str]):
        self.foglie_hash = foglie_hash
        self.proofs: Dict[int, List[Tuple[str, str]]] = {i: [] for i in range(len(self.foglie_hash))}
        self.root: Optional[str] = None


    def _aggiorna_proofs(self, gruppo_sx: List[int], gruppo_dx: List[int], elem_sx: str, elem_dx: str):
        if self.proofs is None:
            return
        for idx in gruppo_sx:
            self.proofs[idx].append(("right", elem_dx))
            print(f"AGGIORNAMENTO MERKLE_PATH ↳Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")
        for idx in gruppo_dx:
            self.proofs[idx].append(("left", elem_sx))
            print(f"AGGIORNAMENTO MERKLE_PATH ↳Foglia {idx} → aggiunge fratello SINISTRO {elem_sx}\n")

    def costruisci_albero(self, genera_proofs: bool = False) -> str:
        #memorizza le proofs per ciascuna foglia
        self.proofs = {i: [] for i in range(len(self.foglie_hash))} if genera_proofs else None
        #lista contenente gli hash a ciascun livello
        livello_corrente = list(self.foglie_hash)
        #lista di indici correnti
        indici_correnti = [[i] for i in range(len(self.foglie_hash))]

        print("🌱 Hash delle foglie iniziali:")
        for i, h in enumerate(self.foglie_hash):
            print(f"  Foglia {i}: {h}")

        # utile solo per debug la variabile livello
        livello = 0
        while len(livello_corrente) > 1:
            print(f"\n🧱 Livello {livello} (len={len(livello_corrente)})")
            print(f"  Indici correnti: {indici_correnti}")
            nuovo_livello = []
            nuovi_indici = []

            for i in range(0, len(livello_corrente), 2):
                elem_sx = livello_corrente[i]
                elem_dx = livello_corrente[i + 1]
                elem_padre = hash_concat(elem_sx, elem_dx)
                nuovo_livello.append(elem_padre)
                print(f"    Hash sinistro: {elem_sx}")
                print(f"    Hash destro  : {elem_dx}")
                print(f"    Hash padre   : {elem_padre}")

                # SOLO se vogliamo generare le proof
                if genera_proofs:
                    gruppo_sx = indici_correnti[i]
                    gruppo_dx = indici_correnti[i + 1]
                    print(f"  Gruppo {gruppo_sx} + {gruppo_dx}")
                    self._aggiorna_proofs(gruppo_sx, gruppo_dx, elem_sx, elem_dx)
                    nuovi_indici.append(gruppo_sx + gruppo_dx)

            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        self.root = livello_corrente[0]
        print(f"\n🌳 Merkle Root finale: {self.root}")

        if self.proofs:
            print("\n📦 Proofs finali:")
            for i, p in self.proofs.items():
                print(f"  Foglia {i}:")
                for j, merkle_proof in enumerate(p):
                    print(f"    Livello {j}: {merkle_proof}")

        return self.root

    def get_proof(self, indice_foglia: int):
        #DA GESTIRE ECCEZIONE: COSA SUCCEDE SE INSERISCO INDICI ERRATI
        return self.proofs[indice_foglia]

def verifica_merkle_path(foglia_raw: str, proof: List[Tuple[str, str]], root_attesa: str) -> bool:
    merkle_root_hash = foglia_raw
    for direzione, hash_fratello in proof:
        if direzione == "left":
            merkle_root_hash = hash_concat(hash_fratello, merkle_root_hash)
        elif direzione == "right":
            merkle_root_hash = hash_concat(merkle_root_hash, hash_fratello)
        else:
            raise ValueError(f"Direzione non valida nella proof: {direzione}")
    return merkle_root_hash == root_attesa


def main():
    # 1. Costruzione dell’albero originale
    foglie = ["data0", "data1", "data2", "data3"]
    foglie_hash = [hashlib.sha256(d.encode()).hexdigest() for d in foglie]
    tree = MerkleTree(foglie_hash)
    tree.costruisci_albero(genera_proofs=True)
    root_originale = tree.root

    # 2. Ottieni le proof originali
    proofs = {i: tree.get_proof(i) for i in range(len(foglie))}

    # 3. Simulazione: foglie modificate
    foglie_modificate = ["data0", "data1020303003", "data290882", "data3"]
    foglie_modificate_hash = [hashlib.sha256(d.encode()).hexdigest() for d in foglie_modificate]

    # 4. Verifica ogni foglia modificata contro root originale e proof originale
    print("\n🔍 Verifica foglie modificate contro la root originale:")
    for i in range(len(foglie)):
        esito = verifica_merkle_path(foglie_modificate[i], proofs[i], root_originale)
        print(f"  Foglia indice {i}: {'valida' if esito else 'non valida'}")


# invocazione del metodo MAIN
if __name__ == "__main__":
    main()