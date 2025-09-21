# ruoli del sistema previsti (le stringhe sono immutabili in python)
RUOLO_PRODUTTORE : str = "produttore"
RUOLO_VERIFICATORE : str = "verificatore"

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
        #quindi se vi è il permesso di scrittura vi è anche il permesso
        #di verifica estesa
        return self.permesso_scrittura()

    def __repr__(self):
        return f"UtenteAPI(nome='{self.nome}', ruolo='{self.ruolo}')"
