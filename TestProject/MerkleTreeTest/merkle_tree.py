import hashlib
from typing import List, Dict, Tuple, Optional


def hash_concat(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode()).hexdigest()


def calcola_hash_foglia(foglia_raw: str) -> str:
    return hashlib.sha256(foglia_raw.encode()).hexdigest()


class MerkleTree:
    def __init__(self, foglie_hash: List[str]):
        self.foglie_hash = foglie_hash
        self.proofs: Optional[Dict[int, List[Tuple[str, str]]]] = None
        self.root: Optional[str] = None

    def _aggiorna_proofs(self, gruppo_sx: List[int], gruppo_dx: List[int], elem_sx: str, elem_dx: str):
        if self.proofs is None:
            return
        for idx in gruppo_sx:
            self.proofs[idx].append(("right", elem_dx))
            print(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")
        for idx in gruppo_dx:
            self.proofs[idx].append(("left", elem_sx))
            print(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello SINISTRO {elem_sx}\n")

    def costruisci_albero(self, genera_proofs: bool = False, verbose: bool = True) -> str:
        self.proofs = {i: [] for i in range(len(self.foglie_hash))} if genera_proofs else None
        livello_corrente = list(self.foglie_hash)
        indici_correnti = [[i] for i in range(len(self.foglie_hash))]

        if verbose:
            print("🌱 Hash delle foglie iniziali:")
            for i, h in enumerate(self.foglie_hash):
                print(f"  Foglia {i}: {h}")

        livello = 0
        while len(livello_corrente) > 1:
            if verbose:
                print(f"\n🧱 Livello {livello} (len={len(livello_corrente)})")
                print(f"  Indici correnti: {indici_correnti}")
            nuovo_livello = []
            nuovi_indici = []

            for i in range(0, len(livello_corrente), 2):
                elem_sx = livello_corrente[i]
                elem_dx = livello_corrente[i + 1]
                elem_padre = hash_concat(elem_sx, elem_dx)
                nuovo_livello.append(elem_padre)

                if verbose:
                    print(f"    Hash sinistro: {elem_sx}")
                    print(f"    Hash destro  : {elem_dx}")
                    print(f"    Hash padre   : {elem_padre}")

                if genera_proofs:
                    gruppo_sx = indici_correnti[i]
                    gruppo_dx = indici_correnti[i + 1]
                    if verbose:
                        print(f"  Gruppo {gruppo_sx} + {gruppo_dx}")
                    self._aggiorna_proofs(gruppo_sx, gruppo_dx, elem_sx, elem_dx)
                    nuovi_indici.append(gruppo_sx + gruppo_dx)

            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        self.root = livello_corrente[0]
        if verbose:
            print(f"\n🌳 Merkle Root finale: {self.root}")

            if self.proofs:
                print("\n📦 Proofs finali:")
                for i, p in self.proofs.items():
                    print(f"  Foglia {i}:")
                    for j, merkle_proof in enumerate(p):
                        print(f"    Livello {j}: {merkle_proof}")

        return self.root

    def get_proof(self, indice_foglia: int) -> List[Tuple[str, str]]:
        if self.proofs is None or indice_foglia not in self.proofs:
            raise IndexError(f"Indice foglia {indice_foglia} non valido")
        return self.proofs[indice_foglia]


def verifica_merkle_path(foglia_raw: str, proof: List[Tuple[str, str]], root_attesa: str) -> bool:
    merkle_root_hash = calcola_hash_foglia(foglia_raw)
    for direzione, hash_fratello in proof:
        if direzione == "left":
            merkle_root_hash = hash_concat(hash_fratello, merkle_root_hash)
        elif direzione == "right":
            merkle_root_hash = hash_concat(merkle_root_hash, hash_fratello)
        else:
            raise ValueError(f"Direzione non valida nella proof: {direzione}")
    return merkle_root_hash == root_attesa


def main():
    foglie = ["data0", "data1", "data2", "data3"]
    foglie_hash = [calcola_hash_foglia(d) for d in foglie]
    tree = MerkleTree(foglie_hash)
    root_originale = tree.costruisci_albero(genera_proofs=True)

    proofs = {i: tree.get_proof(i) for i in range(len(foglie))}

    foglie_modificate = ["data0", "data1020303003", "data290882", "data3"]
    print("\n🔍 Verifica foglie modificate contro la root originale:")
    for i in range(len(foglie)):
        esito = verifica_merkle_path(foglie_modificate[i], proofs[i], root_originale)
        print(f"  Foglia indice {i}: {'valida' if esito else 'non valida'}")

def test_proof_da_albero_compromesso():
    # 1. Albero originale
    foglie_originali = ["data0", "data1", "data2", "data3"]
    foglie_hash_originali = [calcola_hash_foglia(f) for f in foglie_originali]
    tree_originale = MerkleTree(foglie_hash_originali)
    root_originale = tree_originale.costruisci_albero(genera_proofs=True)

    print(f"\n🔐 Merkle root originale (salvata su blockchain): {root_originale}")

    # 2. Albero compromesso (dati alterati)
    foglie_manipolate = ["data0", "data123", "data2", "data333"]
    foglie_hash_manipolate = [calcola_hash_foglia(f) for f in foglie_manipolate]
    tree_manipolato = MerkleTree(foglie_hash_manipolate)
    root_manipolata = tree_manipolato.costruisci_albero(genera_proofs=True)

    print(f"\n🚨 Merkle root compromessa (non firmata): {root_manipolata}")

    # 3. Verifica: uso le proof dall'albero compromesso ma confronto con la root originale
    print("\n🔎 Verifica di ciascuna foglia MANIPOLATA con proof compromesse contro ROOT ORIGINALE:")
    for i in range(len(foglie_manipolate)):
        foglia = foglie_manipolate[i]
        proof_compromessa = tree_manipolato.get_proof(i)
        esito = verifica_merkle_path(foglia, proof_compromessa, root_originale)
        print(f"  Foglia {i}: {'✅ valida' if esito else '❌ NON valida'}")

    print("\n💡 Osservazione: anche se il cloud ha creato proof coerenti con i suoi dati,")
    print("   queste NON portano alla root originale: le modifiche vengono rilevate.")


def test_verifiche_confrontate():
    # 1. Albero originale
    foglie_originali = ["data0", "data1", "data2", "data3"]
    foglie_hash_originali = [calcola_hash_foglia(f) for f in foglie_originali]
    tree_originale = MerkleTree(foglie_hash_originali)
    root_originale = tree_originale.costruisci_albero(genera_proofs=True)

    print(f"\n🔐 Merkle root originale (salvata su blockchain): {root_originale}")

    # 2. Proof originali
    proofs_originali = {i: tree_originale.get_proof(i) for i in range(len(foglie_originali))}

    # 3. Simulazione: foglie modificate
    foglie_manipolate = ["data0", "data123", "data2", "data333"]
    foglie_hash_manipolate = [calcola_hash_foglia(f) for f in foglie_manipolate]
    tree_manipolato = MerkleTree(foglie_hash_manipolate)
    tree_manipolato.costruisci_albero(genera_proofs=True)
    proofs_albero_manipolato= {i: tree_manipolato.get_proof(i) for i in range(len(foglie_manipolate))}

    # === 4. Verifica 1: proof manipolata + tuple manipolata
    print("\n🔎 [CASO 1] Proof da ALBERO CORROTTO con dati CORROTTI, root originale:")
    for i in range(len(foglie_manipolate)):
        esito = verifica_merkle_path(foglie_manipolate[i], proofs_albero_manipolato[i], root_originale)
        print(f"  Foglia {i}: {'✅ valida' if esito else '❌ NON valida'}")

    # === 5. Verifica 2: proof originale + tupla manipolata
    print("\n🔎 [CASO 2] Proof ORIGINALE con dati CORROTTI, root originale:")
    for i in range(len(foglie_originali)):
        foglia_modificata = foglie_manipolate[i]
        proof_originale = proofs_originali[i]
        esito = verifica_merkle_path(foglia_modificata, proof_originale, root_originale)
        print(f"  Foglia {i}: {'✅ valida' if esito else '❌ NON valida'}")

    print("\n💡 Conclusione:")
    print("   ❌ Se modifichi i dati → root calcolata ≠ root salvata")
    print("   ❌ Se modifichi le proof → root calcolata ≠ root salvata")
    print("   ✅ Solo dati autentici + proof autentica → root corretta")

def test_verifiche_confrontate_2():
    # COMPARATIVO DELLA MIA SOLUZIONE
    foglie_originali = ["data0", "data1", "data2", "data3"]
    foglie_hash_originali = [calcola_hash_foglia(f) for f in foglie_originali]
    tree_originale = MerkleTree(foglie_hash_originali)
    root_originale = tree_originale.costruisci_albero(genera_proofs=True)

    proofs_originali = {i: tree_originale.get_proof(i) for i in range(len(foglie_originali))}

    # Casi da testare
    casi = {
        "✅ Tupla intatta + Proof intatta": (foglie_originali, proofs_originali),
        "❌ Tupla modificata + Proof intatta": (["dataX", "data1", "data2", "data3"], proofs_originali),
        "❌ Tupla intatta + Proof modificata": (foglie_originali, {i: [("right", "WRONGHASH")] for i in range(4)}),
        "❌ Tupla modificata + Proof modificata": (["dataX", "dataY", "dataZ", "dataW"], {i: [("left", "FAKEHASH")] for i in range(4)}),
    }

    for descrizione, (foglie_test, proofs_test) in casi.items():
        print(f"\n🔎 {descrizione}")
        for i in range(len(foglie_test)):
            esito = verifica_merkle_path(foglie_test[i], proofs_test[i], root_originale)
            print(f"  Foglia {i}: {'✅ valida' if esito else '❌ NON valida'}")
    print("\n📌 Fine test comparativi.")

# Invoca la funzione di test
if __name__ == "__main__":
    #main()
    #test_proof_da_albero_compromesso()
    #test_verifiche_confrontate()
    test_verifiche_confrontate_2()

