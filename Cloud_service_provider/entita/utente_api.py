# RUOLI DEL SISTEMA
from typing import final

# ruoli del sistema previsti
RUOLO_PRODUTTORE : final = "produttore"
RUOLO_VERIFICATORE : final = "verificatore"

class UtenteAPI:
    def __init__(self, nome: str, ruolo: str):
        self.nome = nome
        self.ruolo = ruolo

    def permesso_scrittura(self) -> bool:
        return self.ruolo == RUOLO_PRODUTTORE

    def permesso_verifica(self) -> bool:
        return self.ruolo in (RUOLO_PRODUTTORE, RUOLO_VERIFICATORE)

    def permesso_verifica_estesa(self) -> bool:
        #solo il produttore è abilitato alla verifica estesa
        return self.permesso_scrittura()

    def __repr__(self):
        return f"UtenteAPI(nome='{self.nome}', ruolo='{self.ruolo}')"
