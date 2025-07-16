import json
from abc import ABC
from deepdiff import DeepDiff
from pydantic import BaseModel
from Classi_comuni.utils.hashing_utils import Hashing


class ModelliSerializzabili(BaseModel, ABC):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON.
    Serializzare in JSON significa convertire l'oggetto (con i suoi attributi) in una stringa
    testuale nel formato JSON (JavaScript Object Notation), che può essere facilmente trasmessa
    via rete, salvata su file o interpretata da altri sistemi. È utile per lo scambio di dati
    tra componenti diversi (es. tra nodi IoT e server cloud).
    """

    def to_json(self) -> str:
        """
       Restituisce una rappresentazione JSON dell'istanza, ordinata e leggibile.

       Utilizzo combinato di `model_dump()` e `json.dumps()`:
       - `model_dump()` (di Pydantic) converte l'istanza di una classe che eredita da BaseModel
         in un dizionario Python puro, escludendo i metadati interni e garantendo compatibilità JSON.
       - `json.dumps()` serializza quel dizionario in una stringa JSON (libreria json di python)

       Opzioni usate in `json.dumps()`:
       - `sort_keys=True`: ordina le chiavi nel JSON, garantendo una serializzazione deterministica,
         fondamentale per il calcolo di hash stabili. Due oggetti uguali hanno la medesima rappresentazione
         JSON e quindi, hanno lo stesso hash.
       - `separators=(",", ":")`: rimuove gli spazi superflui dopo virgole e due punti (ottimizzazione della stringa).
       - `indent=2`: aggiunge indentazione per migliorare la leggibilità (utile in fase di debug o log).
        """
        return json.dumps(
            self.model_dump(),
            sort_keys=True,
            separators=(",", ":"),
            indent=2
        )


class ModelliHashabili(ModelliSerializzabili):
    """
    Classe base astratta per modelli che devono poter essere serializzati in JSON
    e da cui calcolare un hash univoco.
    """
    def to_hash(self) -> str:
        """
        Calcola e restituisce l'hash dell'istanza,
        convertendola prima in una stringa JSON deterministica.
        La funzione di hashing è generica e può essere cambiata a piacimento
        """
        return Hashing.calcola_hash(self.to_json())

    def differenze_con(self, altro: "ModelliHashabili") -> dict:
        """
        Confronta l'istanza corrente di ModelliHashabili con un'altra istanza di ModelliHashabili
        e restituisce un dizionario
        con le differenze rilevate usando la libreria DeepDiff.
        """
        return DeepDiff(
            self.model_dump(),
            altro.model_dump(),
            ignore_order=True,
            verbose_level = 2
        )
