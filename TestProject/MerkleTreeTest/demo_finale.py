import hashlib
import json
from typing import List, Dict, Tuple, Optional


def hash_concat(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode()).hexdigest()


def calcola_hash_foglia(foglia_raw: str) -> str:
    return hashlib.sha256(foglia_raw.encode()).hexdigest()


class MerkleTree:
    def __init__(self, foglie_hash: List[str]):
        self.foglie_hash = foglie_hash
        self.root: Optional[str] = None
        self.proofs: Optional[Dict[int, List[Tuple[int, str]]]] = None

    def _aggiorna_proofs(self, gruppo_sx: List[int], gruppo_dx: List[int], elem_sx: str, elem_dx: str):
        if self.proofs is None:
            return
        for idx in gruppo_sx:
            self.proofs[idx].append((0, elem_dx))  # 0 = right
        for idx in gruppo_dx:
            self.proofs[idx].append((1, elem_sx))  # 1 = left

    def costruisci_albero(self, genera_proofs: bool = False, mappa_id: Optional[List[int]] = None) -> str:
        if genera_proofs:
            if mappa_id is None:
                raise ValueError("Se genera_proofs=True, è necessario fornire mappa_id")
            if len(mappa_id) != len(self.foglie_hash):
                raise ValueError("La lunghezza di mappa_id deve essere uguale al numero di foglie")
            self.proofs = {id_logico: [] for id_logico in mappa_id}
            indici_correnti = [[id_logico] for id_logico in mappa_id]
        else:
            indici_correnti = None

        livello_corrente = list(self.foglie_hash)

        while len(livello_corrente) > 1:
            nuovo_livello = []
            nuovi_indici = []

            for i in range(0, len(livello_corrente), 2):
                sx = livello_corrente[i]
                dx = livello_corrente[i + 1]
                padre = hash_concat(sx, dx)
                nuovo_livello.append(padre)

                if genera_proofs and indici_correnti:
                    gruppo_sx = indici_correnti[i]
                    gruppo_dx = indici_correnti[i + 1]
                    self._aggiorna_proofs(gruppo_sx, gruppo_dx, sx, dx)
                    nuovi_indici.append(gruppo_sx + gruppo_dx)

            livello_corrente = nuovo_livello
            if genera_proofs:
                indici_correnti = nuovi_indici

        self.root = livello_corrente[0]
        return self.root

    def get_proof(self, id_logico: int) -> List[Tuple[int, str]]:
        if self.proofs is None or id_logico not in self.proofs:
            raise IndexError(f"ID logico {id_logico} non valido o proofs non generate.")
        return self.proofs[id_logico]


def calcola_hash_batch(batch_dict: dict) -> str:
    return calcola_hash_foglia(json.dumps(batch_dict, sort_keys=True))


def verifica_singola_misurazione(id_misurazione, valore, proof, root_attesa):
    h = calcola_hash_foglia(valore)
    for direzione, fratello in proof:
        if direzione == 1:
            h = hash_concat(fratello, h)
        else:
            h = hash_concat(h, fratello)
    return h == root_attesa


def test_casi_verifica_completi():
    print("\n🔍 TEST COMPLETO DEI CASI DI VERIFICA")

    misurazioni_orig = {
        10: "temp:20,t:10:00",
        11: "temp:21,t:10:01",
        12: "temp:22,t:10:02",
        13: "temp:23,t:10:03"
    }

    lista_id = sorted(misurazioni_orig)
    foglie_hash = [calcola_hash_foglia(misurazioni_orig[i]) for i in lista_id]
    tree = MerkleTree(foglie_hash)
    merkle_root = tree.costruisci_albero(genera_proofs=True, mappa_id=lista_id)
    proofs = {i: tree.get_proof(i) for i in lista_id}

    batch = {
        "id_batch": 77,
        "timestamp_creazione": "2025-06-11T15:00:00",
        "merkle_paths": proofs
    }
    hash_batch = calcola_hash_batch(batch)
    root_finale = hash_concat(merkle_root, hash_batch)

    def analizza_integrità(misure, proofs_usate, batch_usato, root_attesa):
        foglie_hash_check = [calcola_hash_foglia(misure[i]) for i in lista_id]
        tree_check = MerkleTree(foglie_hash_check)
        merkle_root_check = tree_check.costruisci_albero()
        hash_batch_check = calcola_hash_batch(batch_usato)
        root_check = hash_concat(merkle_root_check, hash_batch_check)

        print(f"  Merkle Root originale: {merkle_root}")
        print(f"  Merkle Root testata   : {merkle_root_check}")
        print(f"  Hash batch originale  : {hash_batch}")
        print(f"  Hash batch testato    : {hash_batch_check}")
        print(f"  Root finale attesa    : {root_attesa}")
        print(f"  Root finale calcolata : {root_check}")

        if merkle_root_check != merkle_root and hash_batch_check != hash_batch:
            print("  🔴 Modificati sia le misurazioni che il batch.")
        elif merkle_root_check != merkle_root:
            print("  🟠 Modificate le misurazioni.")
        elif hash_batch_check != hash_batch:
            print("  🟡 Modificato il batch.")
        else:
            print("  ✅ Tutto integro.")

    # CASO 1: Tutto integro
    print("\n✅ CASO 1: Tupla originale + Proof originale + Batch originale")
    analizza_integrità(misurazioni_orig, proofs, batch, root_finale)

    # CASO 2: Misurazione modificata
    print("\n❌ CASO 2: Tupla modificata + Proof originale")
    mis_modificate = misurazioni_orig.copy()
    mis_modificate[11] = "temp:99,t:10:01"
    analizza_integrità(mis_modificate, proofs, batch, root_finale)

    # CASO 3: Batch modificato
    print("\n❌ CASO 3: Batch modificato")
    batch_modificato = batch.copy()
    batch_modificato["timestamp_creazione"] = "FAKE_TIMESTAMP"
    analizza_integrità(misurazioni_orig, proofs, batch_modificato, root_finale)

    # CASO 4: Entrambi modificati
    print("\n❌ CASO 4: Tupla modificata + Batch modificato")
    analizza_integrità(mis_modificate, proofs, batch_modificato, root_finale)


test_casi_verifica_completi()
