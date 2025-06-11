import hashlib
import json
from typing import List, Dict, Tuple, Optional


def hash_concat(left: str, right: str) -> str:
    return hashlib.sha256((left + right).encode()).hexdigest()


def calcola_hash_foglia(foglia_raw: str) -> str:
    return hashlib.sha256(foglia_raw.encode()).hexdigest()


def is_power_of_two(n: int) -> bool:
    return n > 0 and (n & (n - 1)) == 0


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
        if not is_power_of_two(len(self.foglie_hash)):
            raise ValueError("Il numero di foglie deve essere una potenza di due")

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


def verifica_singola_misurazione(valore: str, path: Dict[str, List[str]], root_attesa: str) -> bool:
    """
    Verifica l'integrità di una singola misurazione usando la root attesa e il Merkle Path compatto.

    :param valore: il valore grezzo della misurazione (es. stringa JSON)
    :param path: dizionario compatto con 'd' = stringa di direzioni, 'h' = lista hash fratelli
    :param root_attesa: merkle_root_misurazioni salvata su blockchain
    :return: True se la verifica ha successo, False altrimenti
    """
    h = calcola_hash_foglia(valore)
    direzioni = path["d"]
    fratelli = path["h"]
    #IN py una stringa è una lista di caratteri

    #zip accorpa elemento di ciascuna lista in una tupla
    for direzione, fratello in zip(direzioni, fratelli):
        if direzione == "1":
            h = hash_concat(fratello, h)
        else:  # "0"
            h = hash_concat(h, fratello)
    return h == root_attesa


def main():
    misurazioni = {
        1025: "temperatura=24.5;timestamp=1620000001",
        1026: "temperatura=24.7;timestamp=1620000002",
        1042: "temperatura=25.0;timestamp=1620000003",
        1099: "temperatura=25.2;timestamp=1620000004"
    }

    # Ordina le misurazioni per ID
    misurazioni_ordinate = dict(sorted(misurazioni.items()))
    foglie_hash = [calcola_hash_foglia(v) for v in misurazioni_ordinate.values()]
    ids = list(misurazioni_ordinate.keys())

    albero = MerkleTree(foglie_hash)
    merkle_root_misurazioni = albero.costruisci_albero(genera_proofs=True, mappa_id=ids)
    proofs = {id_: albero.get_proof(id_) for id_ in ids}

    batch_record = {
        "id_batch": 99,
        "timestamp": "2025-06-11T00:00:00",
        "merkle_root_misurazioni": merkle_root_misurazioni,
        "merkle_paths": {str(k): {"d": "".join(str(d) for d, _ in v), "h": [h for _, h in v]} for k, v in proofs.items()}
    }
    hash_batch = calcola_hash_batch(batch_record)
    print(batch_record["merkle_paths"])

    print("Merkle Root delle misurazioni:", merkle_root_misurazioni)
    print("Hash del batch:", hash_batch)

    for id_, valore in misurazioni_ordinate.items():
        # le chiavi di un dizionario sono sempre stringhe in Py
        path = batch_record["merkle_paths"][str(id_)]
        esito = verifica_singola_misurazione(valore, path, merkle_root_misurazioni)
        print(f"ID {id_} → verifica: {'OK' if esito else 'FALLITA'}")


if __name__ == "__main__":
    main()



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