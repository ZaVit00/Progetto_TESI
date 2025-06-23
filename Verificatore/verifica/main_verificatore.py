import copy
import logging
import json
from Verificatore.verifica.verificatore import Verificatore
from api_cloud import richiedi_metadata_misurazione, richiedi_metadata_batch

# Configura il logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def main():
    id_batch = 1 # ← cambia questo valore a piacimento
    verificatore = Verificatore(id_batch)
    risultati = verificatore.esegui_verifica_completa()

    print("\n=== RISULTATO VERIFICA ===")

    if risultati["esito_globale"]:
        print("\n✅ Il batch è integro.")
    else:
        print("\n❌ Il batch presenta alterazioni.")

    print("\n=== ANALISI DELLE ANOMALIE DETTAGLIATA ===")
    print(json.dumps(risultati, indent=2, ensure_ascii=False))

    # Recupero dei metadati delle sole anomalie
    print("\n=== METADATI DELLE FOGLIE ALTERATE ===")

    for record in risultati["dettagli"]["anomalie"]:
        tipo = record["tipo"]
        id_elemento = record["id"]
        print(f"\n--- {tipo.upper()} ID {id_elemento} ---")
        try:
            if tipo == "batch":
                metadati = richiedi_metadata_misurazione(id_elemento)
            elif tipo == "misurazione":
                metadati = richiedi_metadata_batch(id_elemento)

            print(json.dumps(metadati, indent=2, ensure_ascii=False))

        except ValueError as e:
            print(f"Errore nel recupero dei metadati: {e}")

if __name__ == "__main__":
    main()
