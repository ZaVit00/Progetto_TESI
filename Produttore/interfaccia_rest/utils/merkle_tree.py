from typing import List
from utils.hash_utils import calcola_hash


class MerkleTree:
    """
    Classe per la costruzione di un Merkle Tree da una lista di hash foglia.
    Supporta due modalità di costruzione:
    - Binaria (2 figli per nodo);
    - Quaternaria (4 figli per nodo).
    """

    def __init__(self, hash_foglie: List[str]):
        """
        Inizializza l'albero a partire da una lista di stringhe hash,
        ognuna corrispondente a una foglia.
        """
        self.hash_foglie = hash_foglie
        self.radice = None

    def costruisci_binario(self) -> str:
        """
        Costruisce un Merkle Tree binario: ogni nodo padre è l'hash concatenato
        di due nodi figli.
        In caso di numero dispari di nodi a un livello, l'ultimo viene duplicato.
        """
        #crea una nuova lista di lavoro
        livello = list(self.hash_foglie)

        while len(livello) > 1:
            if len(livello) % 2 == 1:
                livello.append(livello[-1])  # Duplica l'ultimo se dispari

            livello = [
                calcola_hash(livello[i] + livello[i + 1])
                for i in range(0, len(livello), 2)
            ]

        self.radice = livello[0]
        return self.radice

    def costruisci_quaternario(self) -> str:
        """
        Costruisce un Merkle Tree quaternario: ogni nodo padre è l'hash concatenato
        di quattro nodi figli.
        In caso il numero di nodi a un livello non sia multiplo di 4, l'ultimo viene
        duplicato fino a raggiungere la lunghezza corretta.
        """
        # crea una nuova lista di lavoro
        livello = list(self.hash_foglie)

        while len(livello) > 1:
            while len(livello) % 4 != 0:
                livello.append(livello[-1])  # Completa fino a multiplo di 4

            livello = [
                calcola_hash(
                    livello[i] + livello[i + 1] + livello[i + 2] + livello[i + 3]
                )
                for i in range(0, len(livello), 4)
            ]

        self.radice = livello[0]
        return self.radice
