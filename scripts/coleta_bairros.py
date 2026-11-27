"""Coleta da malha oficial de bairros de Porto Alegre (ObservaPOA / Prefeitura).

A página https://prefeitura.poa.br/smpg/observapoa/mapas publica "Bairros Oficiais"
em Shapefile, hospedado no Google Drive. O script baixa o arquivo, extrai o
shapefile e grava dados/processados/bairros.geojson (WGS84, geometria simplificada
para o dashboard carregar rápido), com os nomes ajustados para a grafia do INCT.

Uso: python scripts/coleta_bairros.py
"""
import io
import json
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

PAGINA = "https://prefeitura.poa.br/smpg/observapoa/mapas"
DRIVE_ID = "1uv0Gi4oU51K9akQCg5NX087EsXTv-V5D"  # link "Bairros Oficiais > SHP" da página
URL = f"https://drive.google.com/uc?export=download&id={DRIVE_ID}"
RAIZ = Path(__file__).resolve().parents[1]
BRUTO = RAIZ / "dados" / "originais" / "observapoa_bairros"
SAIDA = RAIZ / "dados" / "processados" / "bairros.geojson"
# grafias que não casam nem depois de tirar acento e apóstrofo (ObservaPOA -> INCT)
EQUIVALENCIAS = {"CEL. APARICIO BORGES": "Coronel Aparício Borges",
                 "PASSO DA AREIA": "Passo D'Areia"}
HEADERS = {"User-Agent": "enchentes-map (projeto academico PUCRS; coleta unica)"}


def chave(nome: str) -> str:
    """Nome sem acento, apóstrofo, hífen e caixa, para casar grafias diferentes."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return "".join(c for c in sem_acento.lower() if c.isalnum())


def baixar() -> Path:
    BRUTO.mkdir(parents=True, exist_ok=True)
    existentes = list(BRUTO.glob("**/*.shp"))
    if existentes:
        print("ok (já baixado):", existentes[0].name)
        return existentes[0]
    r = requests.get(URL, headers=HEADERS, timeout=120)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(BRUTO)
    (BRUTO / "metadados_coleta.json").write_text(json.dumps({
        "fonte": "ObservaPOA / Prefeitura de Porto Alegre - Bairros Oficiais (SHP)",
        "link": PAGINA, "url_arquivo": URL,
        "forma_de_coleta": "download automatizado (scripts/coleta_bairros.py)",
        "data_coleta": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %z"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return next(BRUTO.glob("**/*.shp"))


def main() -> None:
    shp = baixar()
    gdf = gpd.read_file(shp)
    print("colunas:", list(gdf.columns), "| CRS:", gdf.crs, "| linhas:", len(gdf))
    col_nome = "NOME"

    inct = pd.read_csv(RAIZ / "dados" / "processados" / "inct_limpo.csv")["bairro"].unique()
    nome_inct = {chave(b): b for b in inct}
    gdf["bairro"] = gdf[col_nome].map(
        lambda n: EQUIVALENCIAS.get(str(n).strip()) or nome_inct.get(chave(str(n))))
    sem_par = sorted(gdf.loc[gdf["bairro"].isna(), col_nome].astype(str))
    faltando = sorted(set(inct) - set(gdf["bairro"].dropna()))
    print("sem correspondência no INCT:", sem_par)
    print("bairros do INCT sem polígono:", faltando)

    gdf = gdf.dropna(subset=["bairro"]).dissolve("bairro", as_index=False)[["bairro", "geometry"]]
    gdf["area_km2"] = (gdf.to_crs(31982).area / 1e6).round(3)
    gdf["geometry"] = gdf.to_crs(31982).simplify(15).to_crs(4326)
    gdf = gdf.set_crs(4326, allow_override=True)
    gdf.to_file(SAIDA, driver="GeoJSON")
    print("gravado:", SAIDA, f"({SAIDA.stat().st_size / 1e3:.0f} kB, {len(gdf)} bairros)")


if __name__ == "__main__":
    main()
