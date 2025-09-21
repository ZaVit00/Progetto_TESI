from typing import List
from tabulate import tabulate
from modelli_metadati import MetaDatiBatchPayload


def stampa_tabella_batch(batch_list: List[MetaDatiBatchPayload]):
    """
    Stampa i metadati dei batch disponibili in formato tabellare (output utente).
    Usa la libreria 'tabulate' per una visualizzazione più chiara.
    """
    if not batch_list:
        print("⚠ Nessun batch attualmente disponibile nel sistema.")
        return

    # Prepara i dati come lista di liste
    tabella = [
        [b.id_batch, b.timestamp_creazione, b.numero_misurazioni]
        for b in batch_list
    ]

    # Stampa tabella con intestazioni
    print("\nLista batch disponibili:")
    print(
        tabulate(
            tabella,
            headers=["ID", "Timestamp", "# Misurazioni"],
            tablefmt="pretty"
        )
    )


def stampa_risultato_verifica(integro: bool) -> None:
    """
    Stampa l'esito della verifica in forma leggibile.
    """
    print("\n=== RISULTATO VERIFICA ===")
    if integro:
        print("\n✅ Il batch è integro.")
    else:
        print("\n❌ Il batch presenta alterazioni.")

def visualizza_output(output: str) -> None:
    """
    Stampa delle anomalie/differenze
    """
    print(output)
