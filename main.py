import pandas as pd

# CONFIGURAÇÕES INICIAIS

CONVIDADOS        = "data/LISTA_DOS_CONVIDADOS.csv"
CARNES            = "data/CARNES.csv"
GRAMAS_POR_PESSOA = 450                             # segundo netão

def calcular_proteina_total() -> float:
    """ Calcula a quantidade total de proteína a ser comprada

    Retorna a quantidade de proteíne em kg
    """

    df_pessoas = pd.read_csv(CONVIDADOS)
    total_pessoas = len(df_pessoas)

    return total_pessoas * GRAMAS_POR_PESSOA / 1000 # em kg



def main():
    ...
