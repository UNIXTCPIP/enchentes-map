"""Processa a base externa (UFRGS/Zenodo) para a Tela 2.

Entradas (baixadas por scripts/coleta_zenodo.py e scripts/coleta_bairros.py):
  dados/originais/zenodo/*.gpkg, *.csv
  dados/processados/bairros.geojson

Saídas em dados/processados/ (pequenas, versionadas no Git):
  ufrgs_area_bairro.csv  % da área de cada bairro dentro de cada mancha de inundação
  ufrgs_manchas.geojson  manchas recortadas em Porto Alegre e simplificadas (mapa)
  escolas_poa.csv        escolas de Porto Alegre e em quais manchas elas caem
  abrigos_poa.csv        abrigos de 24/05/2024 em Porto Alegre, por bairro
  fontes.json            fonte, link, licença e data de coleta de cada dado

Uso: python scripts/processa_tela2.py
"""
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ZENODO = RAIZ / "dados" / "originais" / "zenodo"
PROC = RAIZ / "dados" / "processados"
GPKG = ZENODO / "cheias_rhguaiba_2024_db_v14.gpkg"
UTM = 31982  # SIRGAS 2000 / UTM 22S (metros)

# camada -> (rótulo, nível em m, tipo). O glossário do Zenodo tem descrições trocadas
# para algumas destas camadas, então o nível vem do nome da camada.
CAMADAS = {
    "poa_inundacao_2015_294cm": ("Cheia de 2015 (2,94 m)", 2.94, "simulada"),
    "poa_inundacao_1967_313cm": ("Cheia de 1967 (3,13 m)", 3.13, "simulada"),
    "poa_inundacao_2023_set_318cm": ("Cheia de set/2023 (3,18 m)", 3.18, "simulada"),
    "poa_inundacao_2023_nov_346cm": ("Cheia de nov/2023 (3,46 m)", 3.46, "simulada"),
    "poa_inundacao_1941_475cm": ("Cheia de 1941 (4,75 m)", 4.75, "simulada"),
    "poa_inundacao_simulada_500cm": ("Simulação UFRGS 5,00 m", 5.00, "simulada"),
    "poa_inundacao_2024_530cm": ("Cheia de mai/2024 (5,30 m)", 5.30, "simulada"),
    "poa_inundacao_simulada_550cm": ("Simulação UFRGS 5,50 m", 5.50, "simulada"),
    "poa_inundacao_simulada_600cm": ("Simulação UFRGS 6,00 m", 6.00, "simulada"),
    "poa_inundacao_simulada_650cm": ("Simulação UFRGS 6,50 m", 6.50, "simulada"),
    "poa_inundacao_simulada_700cm": ("Simulação UFRGS 7,00 m", 7.00, "simulada"),
    "rhguaiba_planet-skysat_inundacao_obs_20240506":
        ("Observada por satélite em 06/05/2024", 5.30, "observada"),
}


def carregar_mancha(camada: str, limite) -> gpd.GeoDataFrame:
    """Lê a camada, corrige geometrias inválidas e recorta em Porto Alegre."""
    bbox = tuple(gpd.GeoSeries([limite], crs=UTM).to_crs(
        gpd.read_file(GPKG, layer=camada, rows=1).crs).total_bounds)
    g = gpd.read_file(GPKG, layer=camada, bbox=bbox).to_crs(UTM)
    g["geometry"] = g.geometry.force_2d().make_valid()
    uniao = g.geometry.union_all().intersection(limite)
    return gpd.GeoDataFrame({"camada": [camada]}, geometry=[uniao], crs=UTM)


def main() -> None:
    bairros = gpd.read_file(PROC / "bairros.geojson").to_crs(UTM)
    bairros["geometry"] = bairros.geometry.make_valid()
    limite = bairros.geometry.union_all()

    manchas, linhas = [], []
    for camada, (rotulo, nivel, tipo) in CAMADAS.items():
        m = carregar_mancha(camada, limite)
        m["rotulo"], m["nivel_m"], m["tipo"] = rotulo, nivel, tipo
        manchas.append(m)
        inter = bairros.geometry.intersection(m.geometry.iloc[0]).area
        for bairro, a_int, a_tot in zip(bairros["bairro"], inter, bairros.geometry.area):
            linhas.append({"camada": camada, "rotulo": rotulo, "nivel_m": nivel, "tipo": tipo,
                           "bairro": bairro, "area_inundada_km2": round(a_int / 1e6, 4),
                           "pct_area": round(100 * a_int / a_tot, 2)})
        print(f"{rotulo:42s} {m.geometry.area.iloc[0] / 1e6:7.1f} km² inundados em POA")
    manchas = pd.concat(manchas, ignore_index=True)
    pd.DataFrame(linhas).to_csv(PROC / "ufrgs_area_bairro.csv", index=False)

    simples = manchas.copy()
    simples["geometry"] = simples.geometry.simplify(25).buffer(0)
    simples.to_crs(4326).to_file(PROC / "ufrgs_manchas.geojson", driver="GeoJSON",
                                 COORDINATE_PRECISION=5)

    # ---------------------------------------------------------------- escolas
    escolas = gpd.read_file(ZENODO / "insumos_inep_escolas_2023_rs.gpkg", layer="Escolas_RS_2023")
    escolas = escolas[escolas["MUNICIPIO"].str.upper() == "PORTO ALEGRE"].to_crs(UTM)
    escolas["geometry"] = escolas.geometry.force_2d()
    escolas = gpd.sjoin(escolas, bairros[["bairro", "geometry"]], predicate="within").drop(
        columns="index_right")
    for _, m in manchas.iterrows():
        escolas[m["camada"]] = escolas.geometry.within(m.geometry)
    wgs = escolas.to_crs(4326)
    saida = pd.DataFrame({
        "escola": escolas["Escola"].str.title(), "rede": escolas["DEP_ADMIN"],
        "bairro": escolas["bairro"], "lat": wgs.geometry.y.round(5), "lon": wgs.geometry.x.round(5),
        **{c: escolas[c] for c in CAMADAS}})
    saida.to_csv(PROC / "escolas_poa.csv", index=False)
    print(f"escolas em Porto Alegre: {len(saida)}; em área alagada (5,30 m): "
          f"{saida['poa_inundacao_2024_530cm'].sum()}")

    # ---------------------------------------------------------------- abrigos
    ab = pd.read_csv(ZENODO / "rs_crise_abrigos_24052024_20h.csv", sep=None, engine="python")
    ab = ab.dropna(subset=["LATITUDE", "LONGITUDE"])
    ab = gpd.GeoDataFrame(ab, geometry=gpd.points_from_xy(ab["LONGITUDE"], ab["LATITUDE"]),
                          crs=4326).to_crs(UTM)
    ab = gpd.sjoin(ab, bairros[["bairro", "geometry"]], predicate="within")
    ab["pessoas"] = pd.to_numeric(ab["PESSOAS ABRIGADAS"], errors="coerce").fillna(0)
    por_bairro = ab.groupby("bairro").agg(abrigos=("pessoas", "size"),
                                          pessoas_abrigadas=("pessoas", "sum")).reset_index()
    por_bairro["pessoas_abrigadas"] = por_bairro["pessoas_abrigadas"].astype(int)
    por_bairro.to_csv(PROC / "abrigos_poa.csv", index=False)
    print(f"abrigos em Porto Alegre (24/05/2024): {por_bairro['abrigos'].sum()} em "
          f"{len(por_bairro)} bairros, {por_bairro['pessoas_abrigadas'].sum()} pessoas")

    # ---------------------------------------------------------------- fontes
    z = json.loads((ZENODO / "metadados_coleta.json").read_text(encoding="utf-8"))
    o = json.loads((RAIZ / "dados" / "originais" / "observapoa_bairros" /
                    "metadados_coleta.json").read_text(encoding="utf-8"))
    fontes = [
        {"dado": "Manchas de inundação (simuladas e observada), escolas (INEP 2023) e abrigos",
         "fonte": f"{z['fonte']} ({z['versao']}), UFRGS e colaboradores",
         "link": z["link"], "licenca": z["licenca"].upper(), "coleta": z["forma_de_coleta"],
         "data_coleta": z["data_coleta"][:10]},
        {"dado": "Limites oficiais dos bairros",
         "fonte": o["fonte"], "link": o["link"], "licenca": "dado público municipal",
         "coleta": o["forma_de_coleta"], "data_coleta": o["data_coleta"][:10]},
        {"dado": "Simulação por bairro e nível (Tela 1)",
         "fonte": "INCT SiMAI, arquivo data.json fornecido na disciplina",
         "link": "https://inct-simai.com.br/?page=home", "licenca": "uso acadêmico",
         "coleta": "arquivo fornecido pelo parceiro", "data_coleta": "2026-10-28"},
    ]
    (PROC / "fontes.json").write_text(json.dumps(fontes, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
    for f in sorted(PROC.iterdir()):
        print(f"  {f.name:28s} {f.stat().st_size / 1e3:8.0f} kB")


if __name__ == "__main__":
    main()
