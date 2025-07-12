from typing import List

from modelli_metadati import MetaDatiBatch


def stampa_tabella_batch(batch_list: List[MetaDatiBatch]) -> None:
    """
    Stampa i metadati dei batch disponibili in formato tabellare (output utente).
    """
    print("\n📦 Lista batch disponibili:")
    header = f"{'ID':<6} {'Timestamp':<25} {'# Misurazioni':<15}"
    print(header)
    print("-" * len(header))

    for b in batch_list:
        print(f"{b.id_batch:<6} {b.timestamp_creazione:<25} {b.numero_misurazioni:<15}")

def stampa_risultato_verifica(integro: bool) -> None:
    """
    Stampa l'esito della verifica in forma leggibile.
    """
    print("\n=== RISULTATO VERIFICA ===")
    if integro:
        print("\n✅ Il batch è integro.")
    else:
        print("\n❌ Il batch presenta alterazioni.")

def stampa_anomalie(output: str) -> None:
    """
    Stampa delle anomalie/differenze
    """
    print(output)
