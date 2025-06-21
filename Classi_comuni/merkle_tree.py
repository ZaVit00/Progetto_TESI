import json
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict
from hash_utils import Hashing

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL + 1)

@dataclass
class PathCompatto:
    # Classe per la rappresentazione compatta di un Merkle Path
    # Migliora le leggibilità del codice
    def __init__(self):
        self.direzione: str = ""  # Stringa di direzioni codificate ("01", "10", ecc.)
        self.hash_fratelli: List[str] = []  # Lista degli hash fratelli lungo il Merkle Path

    def get_direzione(self) -> str:
        return self.direzione

    def get_hash_fratelli(self) -> List[str]:
        return self.hash_fratelli

    def append_direzione(self, direzione: str) -> None:
        self.direzione += direzione

    def set_direzione(self, dir : str):
        self.direzione = dir

    def set_hash_fratelli(self, hash_fratelli : list[str]):
        self.hash_fratelli = list(hash_fratelli)

    def to_dict(self) -> dict:
        """
        Restituisce un dizionario. Necessaria per la serializzazione dell'oggetto self.paths
        """
        return {
            "dir": self.direzione,
            "hash": self.hash_fratelli
        }

class MerkleTree:
    def __init__(self, foglie_hash: List[str], mappa_id: List[int]):
        self.foglie_hash = foglie_hash
        self.paths: Optional[Dict[int, PathCompatto]] = None  # Merkle Path compatte per ogni foglia
        self.root: Optional[str] = None
        self.mappa_id = mappa_id

    def _aggiorna_paths(self, gruppo_sx: List[int], gruppo_dx: List[int],
                        elem_sx: str, elem_dx: str) -> None:
        if self.paths is None:
            return
        for idx in gruppo_sx:
            self.paths[idx].append_direzione("0")  # 0 = aggiungi fratello a destra
            self.paths[idx].hash_fratelli.append(elem_dx)
            logger.debug(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")
        for idx in gruppo_dx:
            self.paths[idx].append_direzione("1")  # 1 = fratello a sinistra
            self.paths[idx].hash_fratelli.append(elem_sx)
            logger.debug(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello SINISTRO {elem_sx}\n")

    def costruisci_albero(self) -> str:
        if not self.foglie_hash:
            raise ValueError("L'albero non può essere costruito senza foglie.")
        n = len(self.foglie_hash)
        # verifica che il numero di foglie è potenza di due
        if not n > 0 and (n & (n - 1)) == 0:
            raise ValueError("Il numero di foglie deve essere una potenza di due")

        if self.mappa_id is None:
            raise ValueError("È obbligatorio fornire una mappa_id per generare i Merkle Path.")
        if len(self.mappa_id) != len(self.foglie_hash):
            raise ValueError("La lunghezza di mappa_id deve essere uguale al numero di foglie")

        # inizializzazione delle strutture dati importanti
        self.paths = {id_logico: PathCompatto() for id_logico in self.mappa_id}
        indici_correnti = [[id_logico] for id_logico in self.mappa_id]
        livello_corrente = list(self.foglie_hash)

        logger.info("🌱 Hash delle foglie iniziali:")
        for i, h in enumerate(self.foglie_hash):
            logger.debug(f"  Foglia {i}: {h}")

        #solo per debug uso la variabile livello
        livello = 0
        while len(livello_corrente) > 1:
            logger.debug(f"\n🧱 Livello {livello} (len={len(livello_corrente)})")
            logger.debug(f"  Indici correnti: {indici_correnti}")
            nuovo_livello = []
            nuovi_indici = []

            for i in range(0, len(livello_corrente), 2):
                elem_sx = livello_corrente[i]
                elem_dx = livello_corrente[i + 1]
                elem_padre = Hashing.hash_concat(elem_sx, elem_dx)
                nuovo_livello.append(elem_padre)
                gruppo_sx = indici_correnti[i]
                gruppo_dx = indici_correnti[i + 1]

                logger.debug(
                    f"Hash Sinistro:   {elem_sx}\n"
                    f"Hash Destro:     {elem_dx}\n"
                    f"Hash Padre:      {elem_padre}\n"
                    f"Gruppo SX:       {gruppo_sx}\n"
                    f"Gruppo DX:       {gruppo_dx}\n"
                )
                self._aggiorna_paths(gruppo_sx, gruppo_dx, elem_sx, elem_dx)
                nuovi_indici.append(gruppo_sx + gruppo_dx)

            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        self.root = livello_corrente[0]
        return self.root

    def ottieni_merkle_paths(self) -> dict[int, PathCompatto]:
        """
        Restituisce il dizionario completo dei Merkle Path compatti:
        - chiavi: ID delle misurazioni
        - valori: {'direzioni': str, 'hash_fratelli': list[str]}
        """
        if self.paths is None:
            raise ValueError("Proofs non ancora generate. Costruisci prima l'albero Merkle.")
        return self.paths

    def ottieni_merkle_paths_JSON(self) -> str:
        """
        Restituisce una stringa JSON formattata del dizionario dei Merkle Path compatti.
        Utile per la memorizzazione o l'invio su IPFS/Filebase.
        """
        if self.paths is None:
            raise ValueError("Proofs non ancora generate. Costruisci prima l'albero Merkle.")

        # Converte tutte i PathCompatti in dizionari standard Python (serializzabili in JSON)
        # self.paths è un dizionario: {id_misurazione: PathCompatti}
        # Usando .to_dict() su ogni PathCompatto, otteniamo:
        # {id_misurazione: {"direzione": "01", "hash_fratelli": ["abc", "def"]}, ...}
        # chiave id_misurazione --> valore: un dizionario composto da due chiavi "dir"
        # "hash"
        paths_dict = {
            id_misurazione: path.to_dict()
            for id_misurazione, path in self.paths.items()
        }

        # Serializza il dizionario finale in stringa JSON leggibile
        # - sort_keys=True → ordina le chiavi (utile per confronti o diff)
        # - separators → compatta leggermente il JSON
        # - indent=2 → lo rende leggibile a occhio umano
        return json.dumps(
            paths_dict,
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )

    def ottieni_merkle_root(self) -> str:
        if self.root is None:
            raise ValueError("Costruisci prima l'albero e poi ottieni la radice!")
        return self.root

    @staticmethod
    def verifica_singola_foglia(foglia_hash: str, path: PathCompatto, root_attesa: str) -> bool:
        # Verifica l'integrità di una singola foglia usando il Merkle Path compatto
        direzioni = path.get_direzione()
        hash_fratelli = path.get_hash_fratelli()
        h = foglia_hash
        for direzione, fratello in zip(direzioni, hash_fratelli):
            if direzione == "1":  # sinistra
                h = Hashing.hash_concat(fratello, h)
            elif direzione == "0":  # destra
                h = Hashing.hash_concat(h, fratello)
        return h == root_attesa
