import logging
import json
from Verificatore.verifica.verificatore import Verificatore

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

    print("\n=== ANALIZI DELLE ANOMALIE DETTAGLIATA ===")
    print(json.dumps(risultati, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
