"""Carga dos dados processados usados pelas duas telas."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

PROCESSADOS = Path(__file__).resolve().parents[1] / "dados" / "processados"
NIVEL_RECORDE = 5.35  # maio de 2024
AZUIS = ["#eef3f8", "#c9d9ea", "#9dbcd9", "#6a9bc6", "#3d78ad", "#1f4e80"]
COR = "#2f6ea5"
COR_DESTAQUE = "#b8621b"


@st.cache_data
def inct() -> pd.DataFrame:
    return pd.read_csv(PROCESSADOS / "inct_limpo.csv")


@st.cache_data
def inconsistencias() -> pd.DataFrame:
    return pd.read_csv(PROCESSADOS / "inct_inconsistencias.csv")


@st.cache_data
def bairros_geojson() -> dict:
    with open(PROCESSADOS / "bairros.geojson", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def csv(nome: str) -> pd.DataFrame:
    return pd.read_csv(PROCESSADOS / nome)


@st.cache_data
def fontes() -> dict:
    with open(PROCESSADOS / "fontes.json", encoding="utf-8") as f:
        return json.load(f)


def numero(valor: float) -> str:
    """Inteiro com separador de milhar em português."""
    return f"{valor:,.0f}".replace(",", ".")


def metros(valor: float) -> str:
    """Nível com vírgula decimal, por exemplo '5,3 m'."""
    return f"{valor:.1f} m".replace(".", ",")
