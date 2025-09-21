import logging
from typing import List

from costanti_comuni import TipoServizio
from registro_log import setup_logger

logger = setup_logger(TipoServizio.VERIFICATORE, module=__name__, level=logging.DEBUG)

def acquisisci_input_id_batch(lista_id_batch: List[int]) -> int:
    """
    Mostra gli ID dei batch disponibili e chiede all’utente di sceglierne uno.
    Se l'utente seleziona un id non valido restituisce errore
    """
    while True:
        try:
            scelta = int(input("\nInserisci l'ID del batch da verificare: "))
            if scelta in lista_id_batch:
                return scelta
            logger.warning("ID non presente nella lista. Riprova.")
        except ValueError:
            logger.warning("Inserisci un numero intero valido.")
