"""Dashboard de enchentes em Porto Alegre (INCT SiMAI).

Rodar: streamlit run app/app.py
"""
import streamlit as st

st.set_page_config(page_title="Enchentes em Porto Alegre", page_icon="🌊", layout="wide")

pagina = st.navigation([
    st.Page("tela1_simulacao.py", title="Tela 1 · Simulação do INCT", icon="🌊", default=True),
    st.Page("tela2_bases.py", title="Tela 2 · Simulação × enchente de 2024", icon="🛰️"),
])
st.sidebar.caption(
    "Projeto extensionista · Coleta, Preparação e Análise de Dados (PUCRS) com o INCT SiMAI. "
    "Os números são estimativas de simulação, não contagens oficiais.")
pagina.run()
