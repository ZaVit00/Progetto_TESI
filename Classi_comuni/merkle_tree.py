import logging
from dataclasses import dataclass
from typing import List, Optional, Dict
from Classi_comuni.utils.dict_utils import serializza_dict
from hashing_utils import Hashing
logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)

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

    def set_hash_fratelli(self, hash_fratelli : List[str]):
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

    def __init__(self, foglie_hash: List[str], mappa_id_foglie: List[int]):
        """
        Inizializza un albero di Merkle con le foglie già hashate passate come argomenti.
        ATTENZIONE:
        - `foglie_hash` e `mappa_id_foglie` devono avere la stessa lunghezza.
        - L'elemento `foglie_hash[i]` rappresenta l'hash della misurazione
          identificata da `mappa_id_foglie[i]`.
        Le liste `foglie_hash` e `mappa_id` sono logicamente derivate da una struttura dati
        dizionario che lega ciascun ID all'hash corrispondente.
        Per semplicità, la classe MerkleTree lavora su due liste separate ma che, per costruzione,
        sono sempre allineate: l'hash in posizione i corrisponde all'ID in posizione i.

        Args:
            foglie_hash (List[str]): Lista di stringhe contenenti gli hash delle foglie.
                                     Il primo hash è la tupla del batch mappato con id 0;
                                     I restati hash sono tuple formate da sensore inner join misurazione
                                     mappati con l'id della misurazione;

            mappa_id_foglie (List[int]): Lista di ID associati alle foglie
                                  usata per collegare i Merkle Path a ogni elemento.
                                  La corrispondenza logica tra id e hash è mantenuta esternamente alla classe

        """
        self.foglie_hash = foglie_hash  # Lista degli hash delle foglie (già calcolati)
        self.paths: Optional[Dict[int, PathCompatto]] = None  # Dizionario: ID → Merkle Path compatto
        self.root: Optional[str] = None  # Merkle root finale dell'albero (una volta costruito)
        self.mappa_id_foglie = mappa_id_foglie  # Mappa di ID per mantenere la corrispondenza con le foglie

    def _aggiorna_paths(self, gruppo_sx: List[int], gruppo_dx: List[int],
                        elem_sx: str, elem_dx: str) -> None:
        """
        Aggiorna i Merkle Path per ciascuna foglia, aggiungendo l'hash del fratello
        nella posizione corretta (destra o sinistra) per proseguire nella costruzione del percorso.

        Args:
            gruppo_sx (List[int]): Lista di ID delle foglie che si trovano nel sottoalbero sinistro.
            gruppo_dx (List[int]): Lista di ID delle foglie che si trovano nel sottoalbero destro.
            elem_sx (str): Hash del nodo sinistro (a sinistra della coppia).
            elem_dx (str): Hash del nodo destro (a destra della coppia).
        """
        if self.paths is None:
            return  # Se paths non è inizializzato, esce subito

        # Aggiorna il percorso per le foglie del gruppo sinistro
        for idx in gruppo_sx:
            self.paths[idx].append_direzione("0")  # 0 = fratello a destra
            self.paths[idx].hash_fratelli.append(elem_dx)  # Aggiunge l'hash del fratello destro
            logger.debug(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")

        # Aggiorna il percorso per le foglie del gruppo destro
        for idx in gruppo_dx:
            self.paths[idx].append_direzione("1")  # 1 = fratello a sinistra
            self.paths[idx].hash_fratelli.append(elem_sx)  # Aggiunge l'hash del fratello sinistro
            logger.debug(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello SINISTRO {elem_sx}\n")

    def costruisci_albero(self) -> str:
        """
        Costruisce l'albero di Merkle binario a partire dalle foglie fornite e genera la Merkle Root.
        Durante la costruzione, aggiorna i Merkle Path compatti per ogni foglia (basati su mappa_id_foglie).

        Returns:
            str: La Merkle Root dell'albero generato.
        Raises:
            ValueError: Se non ci sono foglie, se il numero di foglie non è potenza di due,
                        o se la mappa_id_foglie è mancante o incoerente.
        """

        # Verifica che ci siano foglie da cui costruire l'albero
        if not self.foglie_hash:
            raise ValueError("L'albero non può essere costruito senza foglie.")

        n = len(self.foglie_hash)

        # Controllo: il numero di foglie deve essere una potenza di due (es. 2, 4, 8, 16, ecc.)
        if not (n > 0 and (n & (n - 1)) == 0):
            raise ValueError("Il numero di foglie deve essere una potenza di due")

        # Verifica che la mappa_id_foglie sia presente e allineata con le foglie
        if self.mappa_id_foglie is None:
            raise ValueError("È obbligatorio fornire una mappa_id_foglie per generare i Merkle Path.")
        if len(self.mappa_id_foglie) != n:
            raise ValueError("La lunghezza di mappa_id_foglie deve essere uguale al numero di foglie")

        # Inizializzazione dei Merkle Path per ogni ID logico
        self.paths = {id_logico: PathCompatto() for id_logico in self.mappa_id_foglie}

        # Inizializzazione degli indici correnti (serve a sapere quali ID compongono ciascun nodo intermedio)
        indici_correnti = [[id_logico] for id_logico in self.mappa_id_foglie]

        # Il livello corrente è la lista degli hash delle foglie
        livello_corrente = list(self.foglie_hash)

        logger.info("🌱 Hash delle foglie iniziali:")
        for i, h in enumerate(self.foglie_hash):
            logger.debug(f"  Foglia {i}: {h}")

        livello = 0  # Usato solo per debug per indicare a che "altezza" siamo

        # Costruzione dell'albero: ogni iterazione rappresenta un livello
        while len(livello_corrente) > 1:
            logger.debug(f"\n🧱 Livello {livello} (len={len(livello_corrente)})")
            logger.debug(f"  Indici correnti: {indici_correnti}")

            nuovo_livello = []  # Lista degli hash dei nodi genitori
            nuovi_indici = []  # Lista dei gruppi di ID associati a ciascun nuovo nodo

            # Procediamo a coppie (binario): ogni due nodi foglia o intermedio generano un padre
            for i in range(0, len(livello_corrente), 2):
                #estrazione delle coppie
                elem_sx = livello_corrente[i]
                elem_dx = livello_corrente[i + 1]
                elem_padre = Hashing.hash_concat(elem_sx, elem_dx)  # Hash del nodo padre

                nuovo_livello.append(elem_padre)

                gruppo_sx = indici_correnti[i]
                gruppo_dx = indici_correnti[i + 1]

                # Log dettagliato per debugging
                logger.debug(
                    f"Hash Sinistro:   {elem_sx}\n"
                    f"Hash Destro:     {elem_dx}\n"
                    f"Hash Padre:      {elem_padre}\n"
                    f"Gruppo SX:       {gruppo_sx}\n"
                    f"Gruppo DX:       {gruppo_dx}\n"
                )

                # Aggiorna i Merkle Path per ogni foglia di sinistra e destra
                self._aggiorna_paths(gruppo_sx, gruppo_dx, elem_sx, elem_dx)

                # Il gruppo padre sarà la somma degli ID dei figli
                nuovi_indici.append(gruppo_sx + gruppo_dx)

            # Avanzamento al livello superiore
            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        # Quando rimane un solo nodo, è la root
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
        # {id_misurazione: {"dir": "01", "hash": ["abc", "def"]}, ...}
        # chiave id_misurazione --> valore: un dizionario composto da due chiavi "dir" e "hash"
        paths_dict = {
            id_misurazione: path.to_dict()
            for id_misurazione, path in self.paths.items()
        }

        # Serializza il dizionario finale in stringa JSON leggibile
        return serializza_dict(paths_dict)

    def ottieni_merkle_root(self) -> str:
        if self.root is None:
            raise ValueError("Costruisci prima l'albero e poi ottieni la radice!")
        return self.root

    @staticmethod
    def verifica_singola_foglia(foglia_hash: str, path: PathCompatto, root_attesa: str) -> bool:
        """
        Verifica l'integrità di una singola foglia usando il suo Merkle Path compatto.
        L'algoritmo ricostruisce il percorso hash partendo dall'hash della foglia,
        concatenando in ordine gli hash dei nodi fratelli secondo le direzioni (0/1),
        fino a ottenere una root. Se questa root coincide con la `root_attesa`,
        la foglia è integra.

        Args:
            foglia_hash (str): L'hash della foglia da verificare.
            path (PathCompatto): Il Merkle Path compatto associato alla foglia.
                                 Contiene direzioni ("0"/"1") e hash dei fratelli.
            root_attesa (str): La Merkle Root attesa, con cui confrontare il risultato.

        Returns:
            bool: True se la foglia è integra (la root ricostruita corrisponde a quella attesa),
                  False altrimenti.
        """
        # Ottieni la lista delle direzioni (0=fratello a destra, 1=fratello a sinistra)
        direzioni = path.get_direzione()

        # Ottieni la lista degli hash dei nodi fratelli, nell’ordine del path
        hash_fratelli = path.get_hash_fratelli()

        # Partenza: hash della foglia
        h = foglia_hash
        # Applica le concatenazioni secondo le direzioni per risalire l’albero
        for direzione, fratello in zip(direzioni, hash_fratelli):
            if direzione == "1":
                # Se il fratello è a sinistra, lo si concatena prima
                h = Hashing.hash_concat(fratello, h)
            elif direzione == "0":
                # Se il fratello è a destra, lo si concatena dopo
                h = Hashing.hash_concat(h, fratello)

        # Verifica se la root calcolata coincide con quella attesa
        return h == root_attesa

