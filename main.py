import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
from datetime import datetime
import subprocess

# CONFIGURAÇÕES INICIAIS

CONVIDADOS        = "data/LISTA_DOS_CONVIDADOS.csv"
CARNES            = "data/CARNES.csv"
GRAMAS_POR_PESSOA = 450                             # segundo netão

def calcular_proteina_total() -> float:
    """ Calcula a quantidade total de proteína a ser comprada

    Retorna a quantidade de proteíne em kg
    """

    df_pessoas = pd.read_csv(CONVIDADOS)
    df_pagantes = df_pessoas["COMPRAR_CARNE"] == 1
    total_pessoas = df_pagantes.sum()
    print(f"CALCULANDO CHURRASCO PARA {total_pessoas} PESSOAS")

    return total_pessoas * GRAMAS_POR_PESSOA / 1000 # em kg


def obter_preco(url: str) -> float:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
    except:
        return 0.0
    time.sleep(1)


    if "swift" in url.lower():
        price_element = soup.find("strong", class_ = "skuBestPrice")
        if not price_element:
            price_element = soup.find("strong", class_ = "skuPrice")

        if price_element:
            price_text = price_element.text.strip()
            price_text = price_text.replace("R$", "").replace(",", ".")
            price_float = float(price_text)

            return round(price_float, 2)

    else:
        return 0.0

def obter_quantidades(total_kg: float|int, df: pd.DataFrame):
    """ Calcula a distribuição de quantidades por categoria """
    bovino = df["Categoria"] == "bovino"
    suino  = df["Categoria"] == "suino"
    aves   = df["Categoria"] == "aves"
    outros = df["Categoria"] == "outros"

    total_bovino = 0.7 * total_kg
    total_nao_boi = total_kg * 0.3

    qtd_boi = bovino.sum()
    qtd_nao_boi = (suino | aves).sum()

    df.loc[bovino, "Quantidade (kg)"]       = round(total_bovino / qtd_boi, 2) if qtd_boi > 0 else 0
    df.loc[suino | aves, "Quantidade (kg)"] = round(total_nao_boi / qtd_nao_boi, 2) if qtd_nao_boi > 0 else 0
    df.loc[outros, "Quantidade (kg)"] = len(df)*1.5*0.05 #cada pão frances tem 50g em média

    return df


def main():
    proteina_total = calcular_proteina_total()
    print(f"Total de {proteina_total}kg")

    df_carnes = pd.read_csv(CARNES)
    df_pessoas = pd.read_csv(CONVIDADOS)
    print("Obtendo preços...")

    df_carnes["preço (R$/kg)"] = df_carnes["URL"].apply(obter_preco)

    df_carnes = obter_quantidades(proteina_total, df_carnes)
    print(df_carnes)

    preco_total = (df_carnes["preço (R$/kg)"] * df_carnes["Quantidade (kg)"]).sum()
    preco_total = round(preco_total, 2)
    print("PREÇO TOTAL: R$", str(preco_total).replace(".", ","))

    total_convidados = len(df_pessoas)
    preco_por_pessoa = round(preco_total/total_convidados, 2)
    print("PREÇO POR PESSOA: R$", preco_por_pessoa)

    

    report = rf"""
---
geometry:
    - top=30mm
    - left=20mm
    - right=20mm
    - bottom=30mm
---

# Churrasco 2025

Segue o documento contendo as informações para o churrasco.

## Valores e Quantidades

* Data de atualização dos valores: {datetime.now().strftime("%d/%m/%Y %H:%M")} 
* Total de pessoas confirmadas: {total_convidados}

{df_carnes.drop("Categoria", axis=1).to_markdown(index=False)}

* Preço total: R\${preco_total}.
* Preço por pessoa: R\${preco_por_pessoa}.

## Metodologia

Usando como base 450g de proteína por pessoa, foi considerado 70% para carnes de origem bovina
e 30% de outras origens, neste caso foram usadas carnes de origem suina e aves. [1]

Contas verificadas e coerentes com [2].

## Referências

1. Como calcular a quantidade ideal de carne para o seu churrasco! | **Netão! Bom Beef #87**. Disponível em: https://www.youtube.com/watch?v=qNqH0f9WZoU
2. Churrascometro. Disponível em: https://www.churrascometro.com.br
"""

    #TODO: adicionar lista de convidados em página separada
    # string_break = r"```{=latex}\newpage```"

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report)

    try:
        comando = ["pandoc", "report.md", "-o", "report.pdf"]
        subprocess.run(comando)
    except:
        pass


if __name__ == "__main__":
    main()
