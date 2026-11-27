"""Tela 1: simulação do INCT SiMAI (apenas o data.json, depois de limpo)."""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st

import dados

df = dados.inct()
geo = dados.bairros_geojson()

st.title("Se o Guaíba chegar a X metros, quem é afetado?")
st.caption("Simulação do INCT SiMAI para os 94 bairros de Porto Alegre.")

st.warning(
    "**Estes números são estimativas de uma simulação, não previsões nem contagens oficiais.** "
    "A população afetada supõe que as pessoas se distribuem igualmente entre todos os prédios "
    "do bairro, inclusive os não residenciais. O resultado é agregado por bairro: não diz "
    "quais ruas ou casas são atingidas. 17 valores inconsistentes do arquivo original foram "
    "corrigidos (detalhes no fim da página).",
    icon="⚠️",
)

nivel = st.slider("Nível do Guaíba (m)", 3.0, 10.0, 5.3, 0.1, format="%.1f m",
                  help="A simulação cobre de 3,0 m a 10,0 m. O recorde de maio de 2024 foi 5,35 m.")
nivel = round(nivel, 1)

atual = df[np.isclose(df["nivel_m"], nivel)]
atingidos = atual[atual["affected_buildings"] > 0]

c1, c2, c3 = st.columns(3)
c1.metric("Pessoas afetadas (estimativa)", dados.numero(atual["affected_population"].sum()),
          f"{100 * atual['affected_population'].sum() / atual['population'].sum():.1f}% da população",
          delta_color="off", delta_arrow="off")
c2.metric("Prédios afetados", dados.numero(atual["affected_buildings"].sum()),
          f"{100 * atual['affected_buildings'].sum() / atual['total_buildings'].sum():.1f}% dos prédios",
          delta_color="off", delta_arrow="off")
c3.metric("Bairros atingidos", f"{len(atingidos)} de {len(atual)}")

# ---------------------------------------------------------------- mapa
st.subheader(f"Porcentagem de prédios afetados por bairro a {dados.metros(nivel)}")
em_3d = st.toggle("Ver em 3D (altura = % de prédios afetados)")
if em_3d:
    por_bairro = atual.set_index("bairro")
    feicoes = []
    for f in geo["features"]:
        linha = por_bairro.loc[f["properties"]["bairro"]]
        pct = float(linha["percentage"])
        tom = [int(238 - 2.07 * pct), int(243 - 1.65 * pct), int(248 - 1.2 * pct)]
        feicoes.append({"type": "Feature", "geometry": f["geometry"], "properties": {
            "bairro": f["properties"]["bairro"], "pct": round(pct, 1),
            "pessoas": dados.numero(linha["affected_population"]),
            "altura": pct * 30, "cor": tom}})
    camada = pdk.Layer("GeoJsonLayer", {"type": "FeatureCollection", "features": feicoes},
                       extruded=True, get_elevation="properties.altura",
                       get_fill_color="properties.cor", get_line_color=[90, 110, 130],
                       line_width_min_pixels=1, pickable=True, opacity=0.9)
    st.pydeck_chart(pdk.Deck(
        layers=[camada], map_style="light",
        initial_view_state=pdk.ViewState(latitude=-30.08, longitude=-51.17, zoom=9.8,
                                         pitch=50, bearing=-15),
        tooltip={"text": "{bairro}\n{pct}% dos prédios\n{pessoas} pessoas (estimativa)"}),
        height=520)
else:
    mapa = px.choropleth_map(
        atual, geojson=geo, locations="bairro", featureidkey="properties.bairro",
        color="percentage", range_color=(0, 100), color_continuous_scale=dados.AZUIS,
        map_style="carto-positron", center={"lat": -30.09, "lon": -51.17}, zoom=9.6, opacity=0.8,
        hover_name="bairro",
        hover_data={"bairro": False, "percentage": ":.1f", "affected_buildings": ":,",
                    "affected_population": ":,"},
        labels={"percentage": "% prédios", "affected_buildings": "Prédios afetados",
                "affected_population": "Pessoas (estimativa)"})
    mapa.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520,
                       coloraxis_colorbar=dict(title="% prédios<br>afetados"))
    st.plotly_chart(mapa, width="stretch", config={"scrollZoom": False})
st.caption("Malha de bairros: ObservaPOA / Prefeitura de Porto Alegre.")

# ---------------------------------------------------------------- barras e ranking
esq, dir_ = st.columns([3, 2])
with esq:
    st.subheader("Prédios afetados em cada bairro atingido")
    if atingidos.empty:
        st.info("Nenhum bairro atingido neste nível.")
    else:
        ordenado = atingidos.sort_values("percentage")
        barras = px.bar(ordenado, x="percentage", y="bairro", orientation="h",
                        color_discrete_sequence=[dados.COR],
                        hover_data={"affected_buildings": ":,", "total_buildings": ":,"},
                        labels={"percentage": "% de prédios afetados", "bairro": "",
                                "affected_buildings": "Prédios afetados",
                                "total_buildings": "Total de prédios"})
        barras.update_layout(height=max(320, 20 * len(ordenado)), xaxis_range=[0, 100],
                             margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(barras, width="stretch")
with dir_:
    st.subheader("Ranking dos bairros mais afetados")
    criterio = st.radio("Ordenar por", ["Pessoas afetadas", "% de prédios"], horizontal=True)
    coluna = "affected_population" if criterio == "Pessoas afetadas" else "percentage"
    ranking = (atingidos.sort_values([coluna, "affected_buildings"], ascending=False)
               .head(15).reset_index(drop=True))
    ranking.index += 1
    st.dataframe(pd.DataFrame({
        "Bairro": ranking["bairro"],
        "Pessoas (est.)": ranking["affected_population"].map(dados.numero),
        "Prédios": ranking["affected_buildings"].map(dados.numero),
        "% prédios": ranking["percentage"].map(lambda v: f"{v:.1f}%".replace(".", ",")),
    }), height=563)

# ---------------------------------------------------------------- curva da cidade
st.subheader("População afetada em toda a cidade, por nível do rio")
cidade = df.groupby("nivel_m", as_index=False)["affected_population"].sum()
no_recorde = float(np.interp(dados.NIVEL_RECORDE, cidade["nivel_m"], cidade["affected_population"]))
curva = go.Figure()
curva.add_scatter(x=cidade["nivel_m"], y=cidade["affected_population"], mode="lines",
                  line=dict(color=dados.COR, width=3), name="População afetada",
                  hovertemplate="%{x:.1f} m: %{y:,.0f} pessoas<extra></extra>")
curva.add_vline(x=dados.NIVEL_RECORDE, line_dash="dash", line_color=dados.COR_DESTAQUE)
curva.add_annotation(x=dados.NIVEL_RECORDE, y=cidade["affected_population"].max(), xanchor="left",
                     showarrow=False, font=dict(color=dados.COR_DESTAQUE),
                     text=f" Recorde de maio de 2024 (5,35 m): ~{dados.numero(no_recorde)} pessoas")
curva.add_scatter(x=[nivel], y=[atual["affected_population"].sum()], mode="markers",
                  marker=dict(size=13, color="#1f2d3d"), name="Nível escolhido",
                  hovertemplate="Nível escolhido: %{x:.1f} m<extra></extra>")
curva.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0), separators=",.",
                    xaxis_title="Nível do Guaíba (m)", yaxis_title="Pessoas afetadas (estimativa)",
                    yaxis_tickformat=",.0f",
                    legend=dict(orientation="h", y=-0.25))
st.plotly_chart(curva, width="stretch")

# ---------------------------------------------------------------- limitações
with st.expander("Limitações e correções feitas nos dados"):
    st.markdown(
        "- **Fonte:** arquivo `data.json` do INCT SiMAI (71 níveis × 94 bairros). Prédios: "
        "OpenStreetMap. População: Censo IBGE 2022.\n"
        "- **População afetada é estimativa:** população do bairro × fração de prédios afetados.\n"
        "- **Porcentagens recalculadas:** o arquivo original arredondava a porcentagem para cima, "
        "para inteiro, o que inflava a população afetada (7,8% a mais a 3,0 m).\n"
        "- **Valores corrigidos:** prédios afetados não podem diminuir quando o rio sobe. "
        "Os pontos que quebravam essa regra foram substituídos por interpolação:")
    st.dataframe(dados.inconsistencias(), hide_index=True, column_config={
        "bairro": "Bairro", "nivel_m": st.column_config.NumberColumn("Nível (m)", format="%.1f"),
        "valor_original": "Original", "valor_corrigido": "Corrigido",
        "problema": "Problema", "tratamento": "Tratamento"})
