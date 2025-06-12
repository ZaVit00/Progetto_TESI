from typing import List, Optional, Dict, Tuple, Union, TypedDict
from costanti import ID_BATCH_LOGICO
from interfaccia_rest.utils.hash_utils import Hashing

class MerkleTree:

    class ProofCompatta(TypedDict):
        # classe interna per la costruzione della proofs compatta
        direzione: str  # direzioni codificate ("01", "10", ecc.)
        hash_fratelli: List[str]  # lista degli hash fratelli

    def __init__(self, foglie_hash: List[str]):
        self.foglie_hash = foglie_hash
        # proofs dizionario chiave stringa id_misurazione, valori liste di coppie direzione, hash
        self.proofs: Optional[Dict[str, List[Tuple[str, str]]]] = None
        self.root: Optional[str] = None
    """
    # Ordina le misurazioni per ID
    misurazioni_ordinate = dict(sorted(misurazioni.items()))
    foglie_hash = [calcola_hash_foglia(v) for v in misurazioni_ordinate.values()]
    ids = list(misurazioni_ordinate.keys())
    QUESTO CODICE DA SCRIVERE
    """
    def _aggiorna_proofs(self, gruppo_sx: List[int], gruppo_dx: List[int], elem_sx: str, elem_dx: str):
        if self.proofs is None:
            return
        for idx in gruppo_sx:
            self.proofs[str(idx)].append(("0", elem_dx)) # 0 = destra
            print(f"AGGIORNAMENTO MERKLE_PATH ↳ Foglia {idx} → aggiunge fratello DESTRO {elem_dx}\n")
        for idx in gruppo_dx:
            self.proofs[str(idx)].append(("1", elem_sx)) # 1 = sinistra
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
        self.proofs = {str(id_logico): [] for id_logico in mappa_id}
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
                self._aggiorna_proofs(gruppo_sx, gruppo_dx, elem_sx, elem_dx)
                nuovi_indici.append(gruppo_sx + gruppo_dx)

            indici_correnti = list(nuovi_indici)
            livello_corrente = nuovo_livello
            livello += 1

        self.root = livello_corrente[0]
        return self.root

    def costruisci_proofs_compatti(self):
        """
        Costruisce una rappresentazione compatta delle Merkle Proofs, utile per
        serializzazione, verifica e archiviazione.

        Ogni proof è rappresentata come un dizionario contenente:
          - 'd': una stringa con le direzioni ('0' = destra, '1' = sinistra)
          - 'h': una lista di hash dei nodi fratelli lungo il Merkle Path

        La chiave principale è l'ID logico della foglia (convertito in stringa).
        :return: Un dizionario compatto delle Merkle Proofs.
        Esempio di input:
        {
            42: [(0, "bbb222..."), (1, "ccc333...")],
            43: [(1, "aaa111..."), (0, "ddd444...")],
        }
        Esempio di output:
        {
            "42": {
                "d": "01",
                "h": [
                    "bbb222...",  # primo fratello a destra
                    "ccc333..."   # poi fratello a sinistra
                ]
            },
            "43": {
                "d": "10",
                "h": [
                    "aaa111...",
                    "ddd444..."
                ]
            }
        }
        proofs_compatti = {
            <id_logico_str>: {
                "d": <stringa_direzioni>,
                "h": <lista_hash_fratelli>
            },
        }
        proofs_compatti: Dict[str, Dict[str, Union[str, List[str]]]]
        Perché ogni valore del sotto-dizionario può essere una str oppure una List[str].
        Se h ci associo una lista di stringhe ovvero i fratelli hash
        Se d ci associo una stringa concatenata ovvero la direzione
        """
        if self.proofs is None:
            raise ValueError("Proofs non ancora generate. Costruisci prima l'albero Merkle.")
        stringa_direzione = ""
        proofs_compatti : dict[str, MerkleTree.ProofCompatta]  = {
            # CHIAVE
            "batch" if key == ID_BATCH_LOGICO else key :
                # VALORE ASSOCIATO ALLA CHIAVE
                MerkleTree.ProofCompatta(
                    #ignoro gli hash e prendo solo la direzione
                    direzione = stringa_direzione.join(direzione for (direzione, _) in values),
                    #ignoro la direzione e prendo solo gli hash
                    hash_fratelli = [hash_fratello for (_, hash_fratello) in values]  # lista degli hash fratelli
                )
            for key, values in self.proofs.items()
        }
        """
        VALUES: LISTA DI TUPLE
        
        k → è un intero, l’ID logico della foglia stringa
        v → è una lista di tuple, ciascuna con due elementi (direzione, hash_fratello)
        List[Tuple[str, str]] = v e k è l'indice chiave del dizionario
        (_,elemento), (elemento, _) è la tupla in cui ignoro un elemento della coppia (_)
        ogni d è il carattere "1" o "0" ed effettuo la concantenazione (join) delle direzioni
        ignorando gli hash e prendendo solo le direzioni (0,1)
        ogni hash_fratello è un hash estratto dalla tupla in cui sto ignorando la direzione
        """
        return proofs_compatti

    def get_proof_da_id(self, id_logico: int) -> list[tuple[str, str]]:
        # DA ELIMINARE O SCOPI DEBUG
        if self.proofs is None or id_logico not in self.proofs:
            raise IndexError(f"ID logico {id_logico} non valido o proofs non generate.")
        return self.proofs[str(id_logico)]

    def get_root(self) -> str:
        if self.root is None:
            raise ValueError("Costruisci prima l'albero e poi ottieni la radice!")
        return self.root

    @staticmethod
    def verifica_singola_foglia(foglia_hash: str, path: Dict[str, List[str]], root_attesa: str) -> bool:
        """
        Verifica l'integrità di una singola foglia usando la Merkle Root attesa e
        un Merkle Path compatto.

        Il Merkle Path compatto è un dizionario con:
        - 'd': stringa di direzioni ('0' = destra, '1' = sinistra)
        - 'h': lista di hash dei nodi fratelli corrispondenti

        :param foglia_hash: Hash della foglia da verificare
        :param path: Dizionario con 'd' (direzioni) e 'h' (hash dei fratelli)
        :param root_attesa: Merkle Root salvata su blockchain
        :return: True se la foglia è valida, False altrimenti
        """
        direzioni = path["d"]
        hash_fratelli = path["h"]
        h = foglia_hash

        # zip accorpa gli elementi alla stessa posizione
        # di diverse liste fornendo una tupla in uscita
        # IN py una stringa è una lista di caratteri (ogni elemento
        # un carattere) e fratelli è una lista di stringhe
        for direzione, fratello in zip(direzioni, hash_fratelli):
            if direzione == "1": #sinistra
                h = Hashing.hash_concat(fratello, h)
            elif direzione == "0":  # "0"
                h = Hashing.hash_concat(h, fratello) #destra
        return h == root_attesa

    """
    Esempio di Merkle Path compatto:
    Supponiamo di voler verificare una foglia con hash:
      foglia_hash = "aaa111..."
    Il Merkle Path compatto per questa foglia potrebbe essere:
      path = {
          "d": "01",   # Destra = 0, poi Sinistra = 1
          "h": [
              "bbb222...",  # primo hash fratello a destra
              "ccc333..."   # poi hash fratello a sinistra
          ]
      }
    Significa che il calcolo sarà:
      1. hash_concatenato = hash(foglia_hash + "bbb222...") a destra perché 0 = destra
      2. hash_finale = hash("ccc333..." + hash_concatenato) a sinistra perche 1 = sinistra
    Il risultato finale (hash_finale) deve coincidere con la Merkle Root salvata.
    """


    """"
    Casi da verificare
    Procedura di verifica prendo i dati del batch precedentemente memorizzati
    (attenzione potrebbero essere stati manomessi) e i dati delle misurazioni (anche questi
    possono essere stati manomessi). Ora in primis verifico l'integrità del batch e capisco
    se le informazioni del batch ma soprattutto i merkle path sono integri.
    Sia se la risposta è sì sia se la risposta è no, procediamo ad effettuare la verifica delle misurazioni
    Ricordati che noi abbiamo a disposizione DUE HASH DISTINTI uno che è il merkle root per le misurazioni
    e l'altro che rappresenta l'hash della tupla batch. Quindi io posso sapere con esattezza che cosa è stato
    modificato se uno o l'altro o entrambi. Inoltre, avendo a disposizione i merkle path se questi sono
    integri posso verificare quale misurazione è stata modificata. Se i merkle path sono stati modificati
    o comunque un qualsiasi campo è stato modificato dobbiamo subito allertare che le informazioni sul batch
    sono state modificate e che ci possono essere errori.
    """

