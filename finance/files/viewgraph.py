import streamlit as st
import pandas as pd
import plotly.express as px
from database import select

# 1 - Carregamento de dados
df = select()
st.set_page_config(layout="wide")

# 2 - Filtros
meses_nome = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

# Adicionar coluna 'Mês' e 'Ano'
df["Ano"] = df["data_issue"].apply(lambda x: x.year)
df["Mês"] = df["data_issue"].apply(lambda x: meses_nome[x.month - 1])

# Renomear colunas
df_renamed = df.rename(columns={
    "data_issue": "Data",
    "money_value": "Valor R$",
    "description": "Descrição",
    "cat": "Categoria",
    "Ano": "Ano",
    "Mês": "Mês"
})

# Função para filtrar dados
def filter_data(df, ano, meses, selected_categories):
    df_filtered = df[df["Ano"] == ano]
    df_filtered = df_filtered[df_filtered["Mês"].isin(meses)]
    if selected_categories:
        df_filtered = df_filtered[df_filtered['Categoria'].isin(selected_categories)]
    return df_filtered

# Título
st.title("Dashboard de Despesas")

# Seletores
ano = st.sidebar.selectbox("Ano", df["Ano"].unique())
meses_selecionados = st.sidebar.multiselect("Meses", options=meses_nome, default=meses_nome)
categories = df["cat"].dropna().unique().tolist()
select_categories = st.sidebar.multiselect("Filtro por Categoria", categories, default=categories)

# Filtrar dados
df_filtered = filter_data(df_renamed, ano, meses_selecionados, select_categories)

# Converter "Valor R$" para números, garantir que os valores sejam positivos e remover valores inválidos
df_filtered["Valor R$"] = pd.to_numeric(df_filtered["Valor R$"], errors="coerce")
df_filtered["Valor R$"] = df_filtered["Valor R$"].abs()  # Garantir que todos os valores sejam positivos
df_filtered["Valor R$"] = df_filtered["Valor R$"].round(2)
df_filtered = df_filtered.dropna(subset=["Valor R$"])

# Estilo para tabela (com formatação de 2 casas decimais e alinhamento dos cabeçalhos)
styled_df = df_filtered.style.format({'Valor R$': '{:,.2f}'})  # Formatar a coluna 'Valor R$' com 2 casas decimais
styled_df = styled_df.set_table_styles([{
    'selector': 'thead th', 'props': [('text-align', 'center')]
}])  # Alinhar os cabeçalhos ao centro

# Exibir a tabela formatada
st.dataframe(styled_df, use_container_width=True)

# Verificar se há dados para os filtros selecionados
if df_filtered.empty:
    st.write("## Não há dados para os filtros selecionados.")
else:
    # Distribuição por categoria
    category_distribution = df_filtered.groupby("Categoria")["Valor R$"].sum().reset_index()

    # Gráfico de Pizza para a distribuição por categoria
    fig = px.pie(category_distribution, values="Valor R$", names='Categoria', title="Distribuição por Categoria", hole=0.3)
    fig.update_layout(width=500, height=500)
    st.plotly_chart(fig, use_container_width=True)

# Espaçamento
st.markdown("<br>", unsafe_allow_html=True)

# ... (seu código para o segundo gráfico, se houver)
