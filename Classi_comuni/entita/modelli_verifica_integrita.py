from typing import List

from pydantic import Field
from modelli_dati import DatiSensore, DatiMisurazione, DatiBatch
from modelli import ModelliHashabili


class DatiMisurazioneSensore(ModelliHashabili):
    dati_sensore : DatiSensore = Field(..., description="dati del sensore")
    dati_misurazione : DatiMisurazione = Field(..., description="dati della misurazioni")

    def differenza(self, altro: "DatiMisurazioneSensore") -> dict:
        """
        Confronta questa istanza con un'altra di tipo DatiMisurazioneSensore
        e restituisce un dizionario contenente le differenze trovate nei
        campi `dati_sensore` e `dati_misurazione`.

        Le differenze sono riportate come:
        {
            "sensore": {...},         # differenze in DatiSensore
            "misurazione": {...}      # differenze in DatiMisurazione
        }
        Se una sezione non ha differenze, non viene inclusa nel risultato.
        """
        differenze = {}
        diff_sensore = self.dati_sensore.differenza(altro.dati_sensore)
        if diff_sensore:
            #aggiungi il campo solo se presente alterazioni
            differenze["sensore"] = diff_sensore

        diff_misurazione = self.dati_misurazione.differenza(altro.dati_misurazione)
        if diff_misurazione:
            #aggiungi il campo se presenti alterazioni
            differenze["misurazione"] = diff_misurazione

        return differenze


class DatiPerVerificaEstesa(ModelliHashabili):
    dati_batch : DatiBatch = Field(..., description="dati del batch")
    dati_misurazione_sensore : List[DatiMisurazioneSensore] = Field()

    def differenza(self, altro: "DatiPerVerificaEstesa") -> dict:
        differenze = {}

        # 1. Differenze nel batch
        diff_batch = self.dati_batch.differenza(altro.dati_batch)
        if diff_batch:
            differenze["batch"] = diff_batch

        # 2. Differenze nella lista misurazioni-sensori
        diz_locali = {
            ms.dati_misurazione.id_misurazione: ms
            for ms in self.dati_misurazione_sensore
        }
        diz_ricevuti = {
            ms.dati_misurazione.id_misurazione: ms
            for ms in altro.dati_misurazione_sensore
        }

        # Intersezione tra gli ID presenti in entrambi
        id_comuni = set(diz_locali.keys()) & set(diz_ricevuti.keys())

        differenze_ms = {}

        for id_mis in sorted(id_comuni):
            ms_locale = diz_locali[id_mis]
            ms_ricevuto = diz_ricevuti[id_mis]
            diff = ms_locale.differenza(ms_ricevuto)
            if diff:
                differenze_ms[str(id_mis)] = diff  # chiave stringa per compatibilità JSON

        if differenze_ms:
            differenze["misurazioni-sensori"] = differenze_ms

        return differenze

