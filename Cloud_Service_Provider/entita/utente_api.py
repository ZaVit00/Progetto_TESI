from ruoli import RUOLO_PRODUTTORE, RUOLO_VERIFICATORE
class UtenteAPI:
    def __init__(self, nome: str, ruolo: str):
        self.nome = nome
        self.ruolo = ruolo

    def permesso_scrittura(self) -> bool:
        return self.ruolo == RUOLO_PRODUTTORE

    def permesso_verifica(self) -> bool:
        return self.ruolo in (RUOLO_PRODUTTORE, RUOLO_VERIFICATORE)

    def permesso_verifica_profonda(self) -> bool:
        #solo il produttore è abilitato alla verifica profonda
        return self.permesso_scrittura()