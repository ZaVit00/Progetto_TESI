from typing import List, Optional, Dict
from costanti import ID_BATCH_LOGICO
from interfaccia_rest.utils.hash_utils import Hashing


class ProofCompatta:
    # Classe per la rappresentazione compatta di una Merkle Proof
    def __init__(self):
        self.direzione: str = ""  # Stringa di direzioni codificate ("01", "10", ecc.)
        self.hash_fratelli: List[str] = []  # Lista degli hash fratelli lungo il Merkle Path

    def get_direzione(self) -> str:
        return self.direzione

    def get_hash_fratelli(self) -> List[str]:
        return self.hash_fratelli

    def append_direzione(self, direzione: str) -> None:
        self.direzione += direzione

class MerkleTree:
    def __init__(self, foglie_hash: List[str]):
        self.foglie_hash = foglie_hash
        self.proofs: Optional[Dict[int, ProofCompatta]] = None  # Proofs compatte per ogni foglia
        self.root: Optional[str] = None

    def _aggiorna_proofs(self, gruppo_sx: List[int], gruppo_dx: List[int],
                         elem_sx: str, elem_dx: str, verbose: bool = False) -> None:
        if self.proofs is None:
            return
        for idx in gruppo_sx:
            self.proofs[idx].append_direzione("0")  # 0 = aggiungi fratello a destra
            self.proofs[idx].hash_fratelli.append(elem_dx)
            if verbose:
                print(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")
        for idx in gruppo_dx:
            self.proofs[idx].append_direzione("1")  # 1 = fratello a sinistra
            self.proofs[idx].hash_fratelli.append(elem_sx)
            if verbose:
                print(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello SINISTRO {elem_sx}\n")

    def costruisci_albero(self, mappa_id: Optional[List[int]] = None, verbose: bool = True) -> str:
        if not self.foglie_hash:
            raise ValueError("L'albero non può essere costruito senza foglie.")
        n = len(self.foglie_hash)
        # verifica che il numero di foglie è potenza di due
        if not n > 0 and (n & (n - 1)) == 0:
            raise ValueError("Il numero di foglie deve essere una potenza di due")

        if mappa_id is None:
            raise ValueError("È obbligatorio fornire una mappa_id per generare i Merkle Path.")
        if len(mappa_id) != len(self.foglie_hash):
            raise ValueError("La lunghezza di mappa_id deve essere uguale al numero di foglie")

        # inizializzazione delle strutture dati importanti
        self.proofs = {id_logico: ProofCompatta() for id_logico in mappa_id}
        indici_correnti = [[id_logico] for id_logico in mappa_id]
        livello_corrente = list(self.foglie_hash)

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
                elem_padre = Hashing.hash_concat(elem_sx, elem_dx)
                nuovo_livello.append(elem_padre)
                if verbose:
                    print(f"    Hash sinistro: {elem_sx}")
                    print(f"    Hash destro  : {elem_dx}")
                    print(f"    Hash padre   : {elem_padre}")

                gruppo_sx = indici_correnti[i]
                gruppo_dx = indici_correnti[i + 1]
                if verbose:
                    print(f"  Gruppo {gruppo_sx} + {gruppo_dx}")
                self._aggiorna_proofs(gruppo_sx, gruppo_dx, elem_sx, elem_dx, verbose)
                nuovi_indici.append(gruppo_sx + gruppo_dx)

            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        self.root = livello_corrente[0]
        return self.root

    def get_proofs(self) -> dict[int, ProofCompatta]:
        # Restituisce i Merkle Path già strutturati per l'invio
        if self.proofs is None:
            raise ValueError("Proofs non ancora generate. Costruisci prima l'albero Merkle.")
        return self.proofs

    def get_root(self) -> str:
        if self.root is None:
            raise ValueError("Costruisci prima l'albero e poi ottieni la radice!")
        return self.root

    @staticmethod
    def verifica_singola_foglia(foglia_hash: str, path: Dict[str, List[str]], root_attesa: str) -> bool:
        # Verifica l'integrità di una singola foglia usando il Merkle Path compatto
        direzioni = path["d"]
        hash_fratelli = path["h"]
        h = foglia_hash

        for direzione, fratello in zip(direzioni, hash_fratelli):
            if direzione == "1":  # sinistra
                h = Hashing.hash_concat(fratello, h)
            elif direzione == "0":  # destra
                h = Hashing.hash_concat(h, fratello)
        return h == root_attesa
