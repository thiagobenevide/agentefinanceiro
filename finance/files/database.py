import psycopg2
import pandas as pd
# 🔹 Configuração da conexão com o PostgreSQL
host = "172.18.0.2"
port = "5432"
database = "finance"
user = "postgres"
password = "123456"

# 🔹 Criando a conexão
def connect():
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=database,
        user=user,
        password=password
    )
    return conn


def select():
    conn = connect()
    querySelect = """
        SELECT 
            data_issue, 
            money_value, 
            description, 
            cat
        FROM transations
        ORDER BY data_issue ASC;
    """
    df = pd.read_sql_query(querySelect, conn)
    conn.close()
    return df
