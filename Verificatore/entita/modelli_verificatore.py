from Classi_comuni.entita.modelli_metadati import MetaDatiBatchPayload, MetaDatiMisurazioneSensorePayload  # usa i tuoi modelli Pydantic reali
from typing import TypedDict, Dict

# --- Tipi ausiliari per la verifica --- #

# Dettagli relativi a una singola anomalia di integrità rilevata durante la verifica.
# Ogni anomalia si riferisce a un ID (es. misurazione o batch), con specifica del tipo di elemento,
# esito della verifica (True = integro, False = alterato), presenza di una modifica strutturale,
# ed eventuali note esplicative.

# Risultato del confronto tra la struttura attesa da IPFS e quella ricevuta dal cloud
# basandoci unicamente sugli id. Nota bene: la tupla del batch è sempre mappata con ID logico 0
# in questo modo precede sempre le misurazioni quando effettuiamo l'ordinamento.
# Elenca gli ID mancanti (presenti nell'albero originale ma assenti nei dati ricevuti)
# e quelli aggiunti (presenti nei dati ricevuti ma non nell'albero originale).

# Risultato complessivo della verifica di un batch.
# Riassume il numero di anomalie rilevate, distinguendo tra anomalie di integrità e strutturali,
# e fornisce il dettaglio delle anomalie e delle differenze strutturali.

class DettagliVerifica(TypedDict):
    tipo : str                         # Tipo di elemento ("batch", "misurazione", ecc.)
    esito : bool                       # Esito della verifica: True se integro, False se alterato
    modifica_strutturale : bool        # True se la struttura risulta compromessa (es. hash alterato, path errato)
    note : str                         # Nota esplicativa


class StrutturaVerifica(TypedDict):
    id_mancanti: list[int]             # Lista degli ID previsti ma non presenti nei dati ricevuti
    id_aggiunti: list[int]             # Lista degli ID presenti ma non previsti (anomalia strutturale)


class RisultatoVerifica(TypedDict):
    id_batch : int                                     # ID del batch verificato
    numero_anomalie_integrita: int                     # Numero di elementi alterati nei contenuti (hash errati)
    numero_anomalie_strutturali : int                  # Numero totale di elementi mancanti o aggiunti
    anomalie_integrita: dict[int, DettagliVerifica]  # era list -> diventa dict mappato per ID
    anomalie_strutturali: StrutturaVerifica            # Dettagli sulle differenze strutturali del batch