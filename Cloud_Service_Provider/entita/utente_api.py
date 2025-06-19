from ruoli import RUOLO_PRODUTTORE, RUOLO_VERIFICATORE
class UtenteAPI:
    def __init__(self, nome: str, ruolo: str):
        self.nome = nome
        self.ruolo = ruolo

    def puo_scrivere(self) -> bool:
        return self.ruolo == RUOLO_PRODUTTORE

    def puo_verificare(self) -> bool:
        return self.ruolo in (RUOLO_PRODUTTORE, RUOLO_VERIFICATORE)