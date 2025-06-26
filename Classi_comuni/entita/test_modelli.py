import json

from deepdiff import DeepDiff
from modelli_dati import DatiSensore, DatiMisurazione, DatiMisurazioneSensore, DatiBatch

# Sensori con descrizioni diverse
s1 = DatiSensore(id_sensore="TEMP001", tipo = "joystick", descrizione="Sensore temperatura sala A")
s2 = DatiSensore(id_sensore="TEMP001", tipo = "joystick", descrizione="Sensore temperatura sala B")

# Misurazioni con differenze nei dati
m1 = DatiMisurazione(
    id_misurazione=1,
    id_sensore="TEMP001",
    timestamp="2025-06-25T10:00:00",
    id_batch=42,
    dati={"temperatura": 22.5, "unità": "C"}
)

m2 = DatiMisurazione(
    id_misurazione=1,
    id_sensore="TEMP001",
    timestamp="2025-06-25T10:00:00",
    id_batch=42,
    dati={"temperatura": 24.0, "unità": "C", "extra": "presente"}
)

# Oggetti combinati
mis1 = DatiMisurazioneSensore(dati_sensore=s1, dati_misurazione=m1)
mis2 = DatiMisurazioneSensore(dati_sensore=s2, dati_misurazione=m2)

# Confronti
print("Differenze DatiSensore:")
print(s1.differenze_con(s2))

print("\nDifferenze DatiMisurazione:")
print(m1.differenze_con(m2))

print("\nDifferenze DatiMisurazioneSensore:")
print(mis1.differenze_con(mis2))

batch1 = DatiBatch(id_batch=1, timestamp_creazione="mamt", numero_misurazioni= 20)
batch2 = DatiBatch(id_batch=1, timestamp_creazione="mamt", numero_misurazioni= 21)

print("\nDifferenze DatiBatch:")

print(batch1.differenze_con(batch2))


def confronta_batch(batch1: DatiBatch, batch2: DatiBatch) -> dict:
    if batch1.id_batch != batch2.id_batch:
        raise ValueError("I batch hanno ID diversi: bug logico")

    diff_batch = batch1.differenze_con(batch2)
    return {"id_batch" : batch1.id_batch, **diff_batch}   if diff_batch else {}

def confronta_misurazioni_sensore(
    lista1: list[DatiMisurazioneSensore],
    lista2: list[DatiMisurazioneSensore]
) -> dict:
    mappa1 = {m.dati_misurazione.id_misurazione: m for m in lista1}
    mappa2 = {m.dati_misurazione.id_misurazione: m for m in lista2}

    if set(mappa1.keys()) != set(mappa2.keys()):
        raise ValueError("Le misurazioni hanno ID non corrispondenti: bug logico")

    differenze = []
    for id_mis in sorted(mappa1.keys()):
        m1 = mappa1[id_mis]
        m2 = mappa2[id_mis]
        diff = m1.differenze_con(m2)
        if diff:
            differenze.append({
                "id_misurazione": id_mis,
                **diff  # unpack per dati_sensore e dati_misurazione
            })

    return {"differenza_mis_sens": differenze} if differenze else {}

def confronta_completo(
    batch1: DatiBatch,
    batch2: DatiBatch,
    lista1: list[DatiMisurazioneSensore],
    lista2: list[DatiMisurazioneSensore]
) -> dict:
    risultato = {}

    diff_batch = confronta_batch(batch1, batch2)
    if diff_batch:
        risultato.update(diff_batch)

    diff_mis = confronta_misurazioni_sensore(lista1, lista2)
    if diff_mis:
        risultato.update(diff_mis)

    return risultato



def main():
    list_mis1 = [mis1]
    list_mis2 = [mis2]

    risultato = confronta_completo(batch1, batch2, list_mis1, list_mis2)
    print("\nDifferenze complessive:")
    print(json.dumps(risultato, indent=2))

if __name__ == "__main__":
    main()