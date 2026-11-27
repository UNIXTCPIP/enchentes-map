"""Tela 2: a simulação do INCT comparada com a base da UFRGS sobre a enchente de 2024."""
import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import dados

OBSERVADA = "rhguaiba_planet-skysat_inundacao_obs_20240506"

inct = dados.inct()
area = dados.csv("ufrgs_area_bairro.csv")
escolas = dados.csv("escolas_poa.csv")
abrigos = dados.csv("abrigos_poa.csv")
geo = dados.bairros_geojson()


@st.cache_data
def manchas() -> dict:
    with open(dados.PROCESSADOS / "ufrgs_manchas.geojson", encoding="utf-8") as f:
        return {f_["properties"]["camada"]: f_ for f_ in json.load(f)["features"]}


def nivel_inct(nivel: float) -> float:
    """Nível do INCT (passos de 0,1 m, a partir de 3,0 m) mais próximo do nível da camada."""
    return float(np.clip(round(nivel, 1), 3.0, 10.0))


st.title("A simulação do INCT bate com a enchente de 2024?")
st.caption("Comparação, bairro a bairro, entre a simulação do INCT SiMAI (Tela 1) e o banco de dados "
           "das cheias de maio de 2024 produzido por pesquisadores da UFRGS.")
st.warning(
    "**Leia antes de comparar.** O INCT mede a *porcentagem de prédios* afetados; a base da UFRGS "
    "mede a *porcentagem da área* do bairro inundada. As duas medidas não são iguais: um bairro "
    "com parque ou orla alagados tem muita área inundada e poucos prédios atingidos. A base da "
    "UFRGS é um esforço voluntário e emergencial, não um levantamento oficial.", icon="⚠️")

camadas = area.drop_duplicates("camada").set_index("camada")
ordem = [OBSERVADA] + [c for c in camadas.sort_values("nivel_m").index if c != OBSERVADA]
f1, f2 = st.columns([2, 1])
camada = f1.selectbox("Comparar a simulação do INCT com", ordem,
                      format_func=lambda c: camadas.loc[c, "rotulo"],
                      help="Mancha observada por satélite ou manchas simuladas pela UFRGS "
                           "para diferentes níveis do Guaíba.")
redes = f2.multiselect("Rede das escolas", sorted(escolas["rede"].unique()),
                       default=sorted(escolas["rede"].unique()))
nivel = nivel_inct(camadas.loc[camada, "nivel_m"])
rotulo = camadas.loc[camada, "rotulo"]

comp = (inct[np.isclose(inct["nivel_m"], nivel)][["bairro", "percentage", "affected_population"]]
        .merge(area[area["camada"] == camada][["bairro", "pct_area"]], on="bairro"))
comp["diferenca"] = comp["percentage"] - comp["pct_area"]
esc = escolas[escolas["rede"].isin(redes)]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Nível do INCT usado", dados.metros(nivel))
k2.metric("Correlação entre as duas bases", f"{comp['percentage'].corr(comp['pct_area']):.2f}".replace(".", ","),
          help="Correlação de Pearson entre % de prédios (INCT) e % de área (UFRGS) nos 94 bairros.")
k3.metric("Bairros com diferença acima de 20 p.p.", int((comp["diferenca"].abs() > 20).sum()))
k4.metric("Escolas em área alagada", f"{int(esc[camada].sum())} de {len(esc)}")

# ---------------------------------------------------------------- dispersão + mapa
esq, dir_ = st.columns(2)
with esq:
    st.subheader("Cada ponto é um bairro")
    comp["destaque"] = np.where(comp["diferenca"].abs() > 20, comp["bairro"], "")
    disp = px.scatter(comp, x="pct_area", y="percentage", text="destaque", hover_name="bairro",
                      color_discrete_sequence=[dados.COR],
                      hover_data={"destaque": False, "pct_area": ":.1f", "percentage": ":.1f"},
                      labels={"pct_area": "% da área inundada (UFRGS)",
                              "percentage": "% de prédios afetados (INCT)"})
    disp.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                   line=dict(color="#8a8f98", dash="dot"))
    disp.update_traces(textposition="top center", textfont_size=10, marker_size=9)
    disp.update_layout(height=470, margin=dict(l=0, r=0, t=10, b=0),
                       xaxis_range=[-3, 103], yaxis_range=[-3, 108])
    st.plotly_chart(disp, width="stretch")
    st.caption("Na linha pontilhada as duas bases concordam. Abaixo dela o INCT indica menos impacto "
               "que a UFRGS; acima, mais.")
with dir_:
    st.subheader("Onde as bases divergem")
    mapa = px.choropleth_map(
        comp, geojson=geo, locations="bairro", featureidkey="properties.bairro",
        color="diferenca", range_color=(-50, 50),
        color_continuous_scale=["#8c510a", "#d8b365", "#f3f1ec", "#7fb8cf", "#1f4e80"],
        map_style="carto-positron", center={"lat": -30.09, "lon": -51.17}, zoom=9.3, opacity=0.75,
        hover_name="bairro",
        hover_data={"bairro": False, "percentage": ":.1f", "pct_area": ":.1f", "diferenca": ":+.1f"},
        labels={"percentage": "% prédios (INCT)", "pct_area": "% área (UFRGS)",
                "diferenca": "Diferença (p.p.)"})
    mapa.update_layout(
        height=470, margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="INCT − UFRGS<br>(p.p.)"),
        map_layers=[dict(sourcetype="geojson", source=manchas()[camada], type="line",
                         color="#1f2d3d", line=dict(width=1))])
    st.plotly_chart(mapa, width="stretch", config={"scrollZoom": False})
    st.caption(f"Contorno escuro: {rotulo.lower()}. Marrom: o INCT indica menos impacto que a "
               "UFRGS. Azul: indica mais.")

# ---------------------------------------------------------------- curvas por nível
st.subheader("As duas bases ao longo dos níveis do rio")
opcoes = ["Toda a cidade"] + sorted(inct["bairro"].unique())
local = st.selectbox("Bairro", opcoes)
if local == "Toda a cidade":
    serie_inct = inct.groupby("nivel_m").apply(
        lambda g: 100 * g["affected_buildings"].sum() / g["total_buildings"].sum(),
        include_groups=False)
    total_km2 = sum(f["properties"]["area_km2"] for f in geo["features"])
    serie_ufrgs = (area.groupby(["camada", "nivel_m", "tipo"])["area_inundada_km2"].sum()
                   .mul(100 / total_km2).rename("pct_area").reset_index())
else:
    serie_inct = inct[inct["bairro"] == local].set_index("nivel_m")["percentage"]
    serie_ufrgs = area[area["bairro"] == local][["camada", "nivel_m", "tipo", "pct_area"]]
sim = serie_ufrgs[serie_ufrgs["tipo"] == "simulada"].sort_values("nivel_m")
obs = serie_ufrgs[serie_ufrgs["tipo"] == "observada"]
curvas = go.Figure()
curvas.add_scatter(x=serie_inct.index, y=serie_inct.values, mode="lines", name="INCT: % de prédios afetados",
                   line=dict(color=dados.COR, width=3), hovertemplate="%{x:.1f} m: %{y:.1f}%<extra></extra>")
curvas.add_scatter(x=sim["nivel_m"], y=sim["pct_area"], mode="lines+markers",
                   name="UFRGS: % da área inundada (simulações)",
                   line=dict(color=dados.COR_DESTAQUE, width=2), marker_size=8,
                   hovertemplate="%{x:.2f} m: %{y:.1f}%<extra></extra>")
curvas.add_scatter(x=obs["nivel_m"], y=obs["pct_area"], mode="markers",
                   name="UFRGS: observada por satélite (06/05/2024)",
                   marker=dict(symbol="diamond", size=14, color="#1f2d3d"),
                   hovertemplate="Observada: %{y:.1f}%<extra></extra>")
curvas.add_vline(x=dados.NIVEL_RECORDE, line_dash="dash", line_color="#8a8f98",
                 annotation_text="recorde de 2024 (5,35 m)", annotation_position="top right")
curvas.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), separators=",.",
                     xaxis_title="Nível do Guaíba (m)", yaxis_title="%", yaxis_rangemode="tozero",
                     legend=dict(orientation="h", y=-0.25))
st.plotly_chart(curvas, width="stretch")

# ---------------------------------------------------------------- escolas e abrigos
e1, e2 = st.columns(2)
with e1:
    st.subheader("Escolas em área alagada a cada nível")
    por_nivel = pd.DataFrame({
        "camada": camadas.index, "rotulo": camadas["rotulo"].values,
        "nivel_m": camadas["nivel_m"].values, "tipo": camadas["tipo"].values,
        "escolas": [int(esc[c].sum()) for c in camadas.index]}).sort_values(["tipo", "nivel_m"],
                                                                             ascending=[False, True])
    por_nivel["cor"] = np.where(por_nivel["camada"] == camada, "Camada escolhida", "Outras camadas")
    barras = px.bar(por_nivel, x="escolas", y="rotulo", orientation="h", color="cor",
                    color_discrete_map={"Camada escolhida": dados.COR_DESTAQUE,
                                        "Outras camadas": dados.COR},
                    labels={"escolas": "Escolas dentro da mancha", "rotulo": "", "cor": ""})
    barras.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0),
                         yaxis=dict(categoryorder="array", categoryarray=por_nivel["rotulo"][::-1]),
                         legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(barras, width="stretch")
    st.caption("Escolas do Censo Escolar (INEP 2023) cuja localização cai dentro de cada mancha.")
with e2:
    st.subheader("Onde ficaram os abrigos em 24/05/2024")
    ab = abrigos.merge(comp[["bairro", "percentage"]], on="bairro").nlargest(15, "pessoas_abrigadas")
    fig_ab = px.bar(ab.sort_values("pessoas_abrigadas"), x="pessoas_abrigadas", y="bairro",
                    orientation="h", color="percentage", range_color=(0, 100),
                    color_continuous_scale=dados.AZUIS, hover_data={"abrigos": True},
                    labels={"pessoas_abrigadas": "Pessoas abrigadas", "bairro": "",
                            "percentage": "% prédios<br>afetados (INCT)", "abrigos": "Abrigos"})
    fig_ab.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_ab, width="stretch")
    st.caption("Os 15 bairros com mais pessoas abrigadas. A cor mostra o quanto o bairro é afetado "
               f"na simulação do INCT a {dados.metros(nivel)}.")

# ---------------------------------------------------------------- fontes
st.subheader("Fontes dos dados")
for f in dados.fontes():
    st.markdown(f"- **{f['dado']}**: {f['fonte']}. [{f['link']}]({f['link']}). "
                f"Licença: {f['licenca']}. Coleta: {f['coleta']}, em "
                f"{pd.to_datetime(f['data_coleta']).strftime('%d/%m/%Y')}.")
st.caption("O nível de cada mancha da UFRGS foi tirado do nome da camada, porque o glossário da "
           "base traz descrições trocadas para algumas delas. A mancha observada por satélite é de "
           "um único dia (06/05/2024), um dia depois do pico.")
