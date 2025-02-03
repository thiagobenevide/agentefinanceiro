"""
Objetivos:
1 - Tratar os extratos dos arquivos OFX
2 - Mandar os dados para a IA 
3 - Criar um data frame de dados
4 - Gravar os dados no PostgreSQL
"""

import sys
import os
import re
import pandas as pd
import ofxparse
from llm import request, template
from database import connect
from psycopg2.extras import execute_values

# Diretório dos arquivos
DIRETORIO_IMPORTACAO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extract_bank"))

# Capturar os arquivos passados como argumento
arquivos_selecionados = sys.argv[1:]

if not arquivos_selecionados:
    print("Nenhum arquivo foi passado para análise.")
    sys.exit(1)

# 1 - Extrair os dados dos extratos bancários
df = pd.DataFrame()
for extrato in arquivos_selecionados:
    caminho_arquivo = os.path.join(DIRETORIO_IMPORTACAO, extrato)

    if not os.path.exists(caminho_arquivo):
        print(f"Arquivo não encontrado: {caminho_arquivo}")
        continue

    with open(caminho_arquivo, encoding='ISO-8859-1') as ofx_file:
        ofx = ofxparse.OfxParser.parse(ofx_file)

    transactions_data = []
    for account in ofx.accounts:
        for transaction in account.statement.transactions:
            transactions_data.append({
                "Data": transaction.date,
                "Valor": transaction.amount,
                "Descrição": transaction.memo,
                "ID": transaction.id  
            })

    df_temp = pd.DataFrame(transactions_data)
    df_temp["Valor"] = df_temp["Valor"].astype(float)
    df_temp["Data"] = df_temp["Data"].apply(lambda x: x.date())
    df = pd.concat([df, df_temp])

# 2 - Tratar os dados e enviar para a LLM
categoria = []
dftempo = df.copy()
count = 0
for transaction in list(dftempo["Descrição"].values):
    padrao = r" - (•••\.\d{3}\.\d{3}-••|\d{2}\.\d{3}\.\d{3}/0001-\d{2}) -.*(\(.*\))?.* Conta:.*"
    clean_text = re.sub(padrao, "", transaction)
    temp = request(template(clean_text))
    categoria.append(temp)
    count += 1
    print(f"{count} - {clean_text} - {temp}")

dftempo["Categoria"] = categoria

# 3 - Enviar os dados para o PostgreSQL
conn = connect()
cursor = conn.cursor()

if len(categoria) != len(dftempo):
    raise ValueError("O tamanho da lista `categoria` não corresponde ao número de linhas de `dftempo`")

dftempo.rename(columns={
    'Data': 'DATA_ISSUE',
    'Valor': 'MONEY_VALUE',
    'Descrição': 'DESCRIPTION',
    'ID': 'IDENT',
    'Categoria': 'CAT'
}, inplace=True)

dftempo.loc[:, "CAT"] = categoria
records = [tuple(row) for row in dftempo.itertuples(index=False, name=None)]

query = """
    INSERT INTO PUBLIC.TRANSATIONS (DATA_ISSUE, MONEY_VALUE, DESCRIPTION, IDENT, CAT)
    VALUES %s
    ON CONFLICT (IDENT) 
    DO UPDATE SET CAT = EXCLUDED.CAT
    WHERE TRANSATIONS.CAT IS DISTINCT FROM EXCLUDED.CAT;
"""

try:
    execute_values(cursor, query, records)
    conn.commit()
    print("Inserção concluída com sucesso!")
except Exception as e:
    conn.rollback()
    print(f"Erro ao inserir dados: {e}")
finally:
    cursor.close()
    conn.close()
