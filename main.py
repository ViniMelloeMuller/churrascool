import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
import math
import validators
import sys
from datetime import datetime
import subprocess

# CONFIGURAÇÕES INICIAIS

CONVIDADOS        = "data/LISTA_DOS_CONVIDADOS.csv"
CARNES            = "data/CARNES.csv"
GRAMAS_POR_PESSOA = 450                             # segundo netão
PAO_FRANCES_POR_PESSOA = 1.5
PAO_DE_ALHO_POR_PESSOA = 150 #g

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

    if not validators.url(url):
        return 1.50
    else:
        pass

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

def obter_quantidades(df: pd.DataFrame, total_convidados: int):
    total_kg = calcular_proteina_total()

    """ Calcula a distribuição de quantidades por categoria """
    bovino   = df["Categoria"] == "bovino"
    suino    = df["Categoria"] == "suino"
    aves     = df["Categoria"] == "aves"
    outros   = df["Categoria"] == "outros"
    vegetais = df["Categoria"] == "vegetal"

    total_bovino = 0.7 * total_kg
    total_nao_boi = total_kg * 0.3

    qtd_boi = bovino.sum()
    qtd_nao_boi = (suino | aves).sum()

    df.loc[bovino, "Quantidade (kg)"]       = round(total_bovino / qtd_boi, 2) if qtd_boi > 0 else 0
    df.loc[suino | aves, "Quantidade (kg)"] = round(total_nao_boi / qtd_nao_boi, 2) if qtd_nao_boi > 0 else 0

    df_carnes = df[~outros].copy()
    df_outros = df[outros].copy()

    df_outros.drop("Quantidade (kg)", inplace=True, axis=1)

    # calculo dos outros produtos

    def calcular_quantidade(row):
        if "pão francês" in row["Corte"].lower():
            return math.ceil(total_convidados * PAO_FRANCES_POR_PESSOA)
        elif "pão de alho" in row["Corte"].lower():
            return math.ceil(total_convidados * PAO_DE_ALHO_POR_PESSOA/400) #pois cada bandeja tem 400g

    if not df_outros.empty:
        df_outros["Unidades"] = df_outros.apply(calcular_quantidade, axis=1)

    return df_carnes, df_outros

def main():
    proteina_total = calcular_proteina_total()
    print(f"Total de {proteina_total}kg")

    df_carnes = pd.read_csv(CARNES)
    df_pessoas = pd.read_csv(CONVIDADOS)
    total_convidados = len(df_pessoas)
    print("Obtendo preços...")

    df_carnes["preço (R$/kg)"] = df_carnes["URL"].apply(obter_preco)

    df_carnes, df_outros = obter_quantidades(df_carnes, total_convidados)
    
    preco_total = (df_carnes["preço (R$/kg)"] * df_carnes["Quantidade (kg)"]).sum()
    preco_total += (df_outros["preço (R$/kg)"] * df_outros["Unidades"]).sum()
    preco_total = round(preco_total, 2)
    print("PREÇO TOTAL: R$", str(preco_total).replace(".", ","))

    preco_por_pessoa = round(preco_total/total_convidados, 2)
    print("PREÇO POR PESSOA: R$", preco_por_pessoa)

    # formatar o df pessoas
    df_pessoas.drop("PAGO", axis=1, inplace=True)
    df_pessoas["Restrição"] = df_pessoas["COMPRAR_CARNE"].apply(lambda x: "Irrestrito" if x == 1 else "Estranho")

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

Acompanhamentos:

{df_outros.drop("Categoria", axis=1).to_markdown(index=False)}

* Preço total: R\${preco_total}.
* Preço por pessoa: R\${preco_por_pessoa}.

## Metodologia

Com base em uma média de 450g de proteína por pessoa, foi estabelecida a proporção de 70% para carnes bovinas e 30% para outras opções, incluindo carnes suínas e de aves [1]. Quanto aos acompanhamentos, foram considerados 1,5 unidades de pão francês por pessoa e 100g de pão de alho

Contas verificadas e coerentes com [2].

## Referências

1. Como calcular a quantidade ideal de carne para o seu churrasco! | **Netão! Bom Beef #87**. Disponível em: https://www.youtube.com/watch?v=qNqH0f9WZoU
2. Churrascometro. Disponível em: https://www.churrascometro.com.br
"""

    newpage_string = "```{=latex}\n\\newpage\n```"

    string2 = f"""
## Convidados

Por favor, verifique se de fato seu nome se encontra na lista.

{df_pessoas.drop(columns=["COMPRAR_CARNE"]).to_markdown(index=False)}
"""

    with open("report.md", "w", encoding="utf-8") as f:
        f.write(report + "\n\n" + newpage_string + "\n" + string2)

    try:
        comando = ["pandoc", "report.md", "-o", "report.pdf"]
        subprocess.run(comando)
    except:
        pass


if __name__ == "__main__":
    main()
