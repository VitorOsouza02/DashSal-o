import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Clientes", layout="wide")
st.title("Dashboard de Clientes")

# Função para calcular KPIs
def calcular_kpis(df):
    n_clientes = df['Código do Cliente'].nunique()
    pl_total = df['PL'].sum()
    taxa_media = df['Taxa contratada'].mean()
    return n_clientes, pl_total, taxa_media

# Upload do arquivo CSV
arquivo = st.file_uploader("Faça upload do arquivo CSV", type=["csv"])
if arquivo:
    df = pd.read_csv(
        arquivo,
        encoding='utf-8',
        sep=',',
        decimal='.',
        thousands=','
    )
    df.columns = [col.strip() for col in df.columns]

    # Filtros
    todos = df
    ativos_aprovados = df[df['Status'].isin(['Ativo', 'Aprovado'])]
    ativos = df[df['Status'] == 'Ativo']
    aprovados = df[df['Status'] == 'Aprovado']
    pendentes = df[df['Status'] == 'Pendente']

    # Calcular KPIs
    kpis = [
        calcular_kpis(todos),
        calcular_kpis(ativos_aprovados),
        calcular_kpis(ativos),
        calcular_kpis(aprovados),
        calcular_kpis(pendentes)
    ]
    nomes = [
        "Todos os Clientes",
        "Ativos e Aprovados",
        "Ativos",
        "Aprovados",
        "Pendentes"
    ]

    # Layout dos cards
    cols = st.columns(5)
    for i, col in enumerate(cols):
        n, pl, taxa = kpis[i]
        col.metric(nomes[i], f"{n} clientes")
        col.metric("PL Total", f"R$ {pl:,.2f}")
        col.metric("Taxa Média", f"{taxa:.2%}")

    # Exibir tabela filtrada (opcional)
    st.write("\n### Dados Filtrados")
    st.dataframe(df)
else:
    st.info("Faça upload do arquivo CSV para visualizar o dashboard.")
