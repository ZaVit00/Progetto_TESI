from typing import TypedDict
"""
Tipologie che abbiamo:

- DettagliVerifica: Dettagli relativi a una singola anomalia di integrità rilevata durante la verifica.
Ogni anomalia si riferisce a un ID (es. misurazione o batch), con specifica del tipo di elemento,
esito della verifica (True = integro, False = alterato), presenza di una modifica strutturale,
ed eventuali note esplicative.

- StrutturaVerifica: Risultato del confronto tra la struttura attesa da IPFS e quella ricevuta dal cloud
basandoci unicamente sugli id. 
Nota bene: la tupla del batch è sempre mappata con ID logico 0
in questo modo precede sempre le misurazioni quando effettuiamo l'ordinamento.
Elenca gli ID mancanti (presenti nell'albero originale ma assenti nei dati ricevuti)
e quelli aggiunti (presenti nei dati ricevuti ma non nell'albero originale).

- RisultatoVerifica: Risultato complessivo della verifica di un batch.
Riassume il numero di anomalie rilevate, distinguendo tra anomalie di integrità e strutturali,
e fornisce il dettaglio delle anomalie e delle differenze strutturali.
"""
#--- Tipi ausiliari per la verifica --- #

class DettagliVerifica(TypedDict):
    tipo : str                         # Tipo di elemento ("batch", "misurazione", ecc.)
    esito : bool                       # Esito della verifica: True se integro, False se alterato
    modifica_strutturale : bool        # True se la STRUTTURA risulta compromessa (es. hash alterato, path errato)
    note : str                         # Nota esplicativa


class StrutturaVerifica(TypedDict):
    id_mancanti: list[int]             # Lista degli ID previsti ma non presenti nei dati ricevuti
    id_aggiunti: list[int]             # Lista degli ID presenti ma non previsti(anomalia strutturale)


class RisultatoVerifica(TypedDict):
    id_batch : int                                     # ID del batch verificato
    numero_anomalie_integrita: int                     # Numero di elementi alterati nei contenuti (hash errati)
    numero_anomalie_strutturali : int                  # Numero totale di elementi mancanti o aggiunti
    anomalie_integrita: dict[int, DettagliVerifica]    # dict mappato per ID
    anomalie_strutturali: StrutturaVerifica            # Dettagli sulle differenze strutturali del batch