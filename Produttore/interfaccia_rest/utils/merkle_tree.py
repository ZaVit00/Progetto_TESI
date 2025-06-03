from typing import List
from utils.hash_utils import calcola_hash

class MerkleTree:
    def __init__(self, foglie: List[str]):
        """
        foglie: lista di stringhe da cui costruire l'albero.
        """
        self.foglie_hashed = foglie
        self.radice = None

    def merkle_tree_binario(self) -> str:
        """
        Costruisce il Merkle Tree binario (coppie di nodi).
        """
        livello = list(self.foglie_hashed)
        while len(livello) > 1:
            #controllo sul numero di elementi per ciascun livello
            if len(livello) % 2 == 1:
                # aggiunge l'ultimo elemento per avere 2 figli per nodo
                livello.append(livello[-1])
            #creo il nuovo livello effettuando l'hashing a coppie di nodi
            livello = [
                calcola_hash(livello[i] + livello[i + 1])
                for i in range(0, len(livello), 2)
            ]
        #ultimo livello è la radice del Merkle Tree
        self.radice = livello[0]
        return self.radice

    def merkle_tree_quad(self) -> str:
        """
        Costruisce il Merkle Tree a 4 figli per nodo (Quad Merkle Tree).
        """
        livello = list(self.foglie_hashed)
        while len(livello) > 1:
            while len(livello) % 4 != 0:
                """
                Controllo per verificare che ogni livello abbia un numero di elementi
                multiplo di quattro. Potrebbe essere necessario ripetere l'operazione
                più volte per ottenere un numero di elementi corretto
                diversamente come accade nel caso binario.
                """
                livello.append(livello[-1])

            # creo il nuovo livello effettuando l'hashing a quattro nodi
            livello = [
                calcola_hash(livello[i] + livello[i + 1] + livello[i + 2] + livello[i + 3])
                for i in range(0, len(livello), 4)
            ]
        self.radice = livello[0]
        return self.radice
