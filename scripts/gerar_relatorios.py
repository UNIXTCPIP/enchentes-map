"""Gera relatorios/limpeza_dados.pdf (Fase 2) e relatorios/dashboard.pdf (Fase 3).

Os números dos relatórios são lidos de dados/processados/, então rode antes
limpeza_inct.py, coleta_bairros.py, coleta_zenodo.py e processa_tela2.py.

Uso: python scripts/gerar_relatorios.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

from limpeza_inct import carregar_longo

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
REL = RAIZ / "relatorios"
IMG = REL / "img"
AUTOR = "Renato Trindade"
REPO = "https://github.com/UNIXTCPIP/enchentes-map"
LINK_DASHBOARD = ""  # preencher depois de publicar (Streamlit Community Cloud)
AZUL, LARANJA = "#2f6ea5", "#b8621b"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.5, leading=13)
SMALL = ParagraphStyle("S", parent=P, fontSize=8, leading=10)
CELL = ParagraphStyle("C", parent=P, fontSize=8, leading=10)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")
MONO = "<font face='Courier'>{}</font>".format


def p(txt, estilo=P):
    return Paragraph(txt, estilo)


def tabela(linhas, larguras):
    dados = [[p(str(c), CELLB if i == 0 else CELL) for c in l] for i, l in enumerate(linhas)]
    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe7f3")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def figura(caminho, largura_cm=17):
    from PIL import Image as PILImage
    w, h = PILImage.open(caminho).size
    return Image(str(caminho), width=largura_cm * cm, height=largura_cm * cm * h / w)


def n(valor):
    return f"{valor:,.0f}".replace(",", ".")


def pdf(nome, titulo, story):
    SimpleDocTemplate(str(REL / nome), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm, title=titulo,
                      author=AUTOR).build(story)
    print("gerado:", REL / nome)


# ---------------------------------------------------------------------- figuras
def fig_inconsistencias(bruto, limpo, erros):
    bairros = erros["bairro"].unique()
    fig, eixos = plt.subplots(1, len(bairros), figsize=(16, 3.2))
    for ax, b in zip(eixos, bairros):
        o, l = bruto[bruto.bairro == b], limpo[limpo.bairro == b]
        ax.plot(o.nivel_m, o.affected_buildings, color=LARANJA, lw=1, marker="o", ms=3, label="original")
        ax.plot(l.nivel_m, l.affected_buildings, color=AZUL, lw=2, label="corrigido")
        if b == "Arquipélago":
            ax.set_ylim(4670, 4692)
        ax.set_title(b, fontsize=10)
        ax.set_xlabel("nível (m)")
        ax.grid(alpha=0.3)
    eixos[0].set_ylabel("prédios afetados")
    eixos[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(IMG / "inconsistencias.png", dpi=130)
    plt.close(fig)


def fig_wireframes():
    def caixa(ax, x, y, w, h, texto, cor="#eef3f8"):
        ax.add_patch(Rectangle((x, y), w, h, facecolor=cor, edgecolor="#5a6b7d", lw=1))
        ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=8)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 8.2))
    for ax, titulo in ((a1, "Tela 1 · Simulação do INCT"), (a2, "Tela 2 · Simulação × enchente de 2024")):
        ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
        ax.set_title(titulo, fontsize=12, loc="left")
    caixa(a1, 0, 91, 100, 7, "Aviso: estimativas de simulação, não contagens oficiais", "#fff4d6")
    caixa(a1, 0, 82, 100, 7, "Controle deslizante: nível do Guaíba, 3,0 a 10,0 m, passo 0,1 m")
    for i, t in enumerate(["Pessoas afetadas", "Prédios afetados", "Bairros atingidos"]):
        caixa(a1, i * 34, 71, 32, 9, f"Indicador\n{t}", "#dbe7f3")
    caixa(a1, 0, 44, 100, 25, "Mapa dos bairros colorido pela % de prédios afetados\n(opção 2D / 3D)")
    caixa(a1, 0, 17, 58, 25, "Barras: % de prédios afetados\nem cada bairro atingido")
    caixa(a1, 60, 17, 40, 25, "Ranking dos bairros\n(por pessoas ou por %)")
    caixa(a1, 0, 0, 100, 15, "Curva: população afetada na cidade por nível,\ncom o recorde de 2024 (5,35 m) marcado")
    caixa(a2, 0, 91, 100, 7, "Aviso: prédios (INCT) e área (UFRGS) são medidas diferentes", "#fff4d6")
    caixa(a2, 0, 82, 64, 7, "Filtro: camada da UFRGS (observada ou simulada por nível)")
    caixa(a2, 66, 82, 34, 7, "Filtro: rede das escolas")
    for i, t in enumerate(["Nível INCT", "Correlação", "Bairros divergentes", "Escolas alagadas"]):
        caixa(a2, i * 25.5, 71, 23.5, 9, f"Indicador\n{t}", "#dbe7f3")
    caixa(a2, 0, 44, 49, 25, "Dispersão por bairro:\n% prédios (INCT) × % área (UFRGS)")
    caixa(a2, 51, 44, 49, 25, "Mapa: diferença INCT − UFRGS\ncom o contorno da mancha")
    caixa(a2, 0, 27, 100, 15, "Curvas por nível: INCT × UFRGS (filtro: bairro ou cidade)")
    caixa(a2, 0, 10, 49, 15, "Barras: escolas em área\nalagada a cada nível")
    caixa(a2, 51, 10, 49, 15, "Barras: abrigos por bairro\n(24/05/2024)")
    caixa(a2, 0, 0, 100, 8, "Fontes: link, licença e data de coleta de cada dado")
    fig.tight_layout()
    fig.savefig(IMG / "wireframes.png", dpi=120)
    plt.close(fig)


# ---------------------------------------------------------------------- relatório de limpeza
def relatorio_limpeza(bruto, limpo, erros, area, escolas, abrigos):
    exata = 100 * bruto.affected_buildings / bruto.total_buildings
    n_teto = int((np.ceil(exata) == bruto.percentage).sum())
    cid = limpo.groupby("nivel_m")[["affected_population", "affected_population_orig",
                                    "affected_buildings", "afetados_orig"]].sum()
    obs = area[area.tipo == "observada"]
    comp = limpo[np.isclose(limpo.nivel_m, 5.3)][["bairro", "percentage"]].merge(
        obs[["bairro", "pct_area"]], on="bairro")

    s = [
        p("Fase 2 · Limpeza de dados e coleta das bases externas", H1),
        p("Projeto Extensionista · Dashboard de Enchentes em Porto Alegre · INCT SiMAI", P),
        p(f"Autor: {AUTOR} · Repositório: {REPO}", P),

        p("1. O que foi entregue", H2),
        tabela([
            ["Item", "Arquivo"],
            ["JSON do INCT em formato longo e limpo", MONO("scripts/limpeza_inct.py") + " → " +
             MONO("dados/processados/inct_limpo.csv") + " e " + MONO("inct_inconsistencias.csv")],
            ["Coleta das bases externas por código", MONO("scripts/coleta_zenodo.py") +
             " (API do Zenodo) e " + MONO("scripts/coleta_bairros.py") + " (ObservaPOA)"],
            ["Processamento da base externa", MONO("scripts/processa_tela2.py") + " → arquivos " +
             MONO("ufrgs_*.csv/geojson") + ", " + MONO("escolas_poa.csv") + ", " + MONO("abrigos_poa.csv")],
            ["EDA com 9 gráficos comentados", MONO("notebooks/eda.ipynb")],
            ["Esboço das duas telas", "Seção 6 deste relatório"],
        ], [6 * cm, 11 * cm]),

        p("2. Formato longo", H2),
        p(f"O {MONO('data.json')} é um dicionário aninhado (nível → bairro → 5 campos). Foi convertido "
          f"para uma linha por nível e bairro: <b>{bruto.shape[0]} linhas × {bruto.shape[1]} colunas</b> "
          f"(71 níveis × 94 bairros), como esperado no enunciado. A chave do nível "
          f"({MONO('3_0m')}) vira o número {MONO('3.0')}."),

        p("3. Verificações feitas", H2),
        tabela([
            ["Verificação", "Resultado"],
            ["Todos os níveis têm os mesmos 94 bairros e os mesmos 5 campos", "Sim"],
            ["Bairros na mesma ordem em todos os níveis", "<b>Não</b>: o nível 5,3 m vem em outra ordem"],
            ["Tipos dos campos", "Todos inteiros, inclusive " + MONO("percentage")],
            ["Valores negativos; afetados &gt; total; % &gt; 100; população afetada &gt; população", "Nenhum caso"],
            [MONO("total_buildings") + " e " + MONO("population") + " constantes por bairro", "Sim"],
            ["Prédios afetados nunca diminuem quando o rio sobe",
             f"<b>Não</b>: {len(erros)} valores em {erros.bairro.nunique()} bairros quebram a regra"],
            [MONO("percentage") + " = afetados / total × 100",
             f"<b>Não exatamente</b>: é sempre arredondada para cima ({n(n_teto)} de {n(len(bruto))} linhas)"],
            [MONO("affected_population") + " = população × percentage / 100",
             "Coerente com a fórmula, mas herda o arredondamento para cima"],
            ["Nomes de bairros com espaços sobrando ou duplicados", "Nenhum caso"],
        ], [9 * cm, 8 * cm]),

        PageBreak(),
        p("4. Inconsistências encontradas e tratamento", H1),

        p("4.1 Bairros em ordem diferente no nível 5,3 m", H2),
        p(f"<b>Onde:</b> chave {MONO('5_3m')}; os outros 70 níveis seguem a mesma ordem. "
          "<b>Por que é um problema:</b> qualquer código que compare níveis pela posição (por exemplo, "
          "transformando cada nível em uma lista) cruzaria bairros errados justamente no nível mais "
          "importante, o mais próximo do recorde de 2024. <b>Tratamento:</b> manter os dados e sempre "
          "acessar pelo nome do bairro; depois da carga, o arquivo é ordenado por bairro e nível."),

        p("4.2 Prédios afetados que diminuem quando o rio sobe", H2),
        p("<b>Por que é um problema:</b> na simulação, um prédio alagado a um nível continua alagado "
          "em um nível maior. Uma série que cai é fisicamente impossível e faria o dashboard mostrar "
          "o impacto diminuindo ao subir o controle do nível. Foram encontrados três padrões:"),
        figura(IMG / "inconsistencias.png"),
        p("• <b>Zeros isolados</b> (Centro Histórico em 9,7 e 9,8 m; Lageado em 8,1 m; Rubem Berta em "
          "8,8 m): o valor cai a zero e volta ao patamar anterior. Parece falha de registro.<br/>"
          "• <b>Picos</b> (Espírito Santo): 637 prédios de 3,0 a 3,3 m, 633 em 3,4 m e 2.101 em 4,7 m, "
          "enquanto os níveis vizinhos têm de 25 a 47 e o bairro só chega a 133 prédios em 10,0 m.<br/>"
          "• <b>Ruído</b> (Arquipélago): oscila entre 4.674 e 4.688 em torno de 4.680, de 3,0 a 5,4 m."),
        p("<b>Tratamento (corrigir por interpolação):</b> para cada bairro mantemos a maior sequência "
          "de pontos que não decresce, o que equivale a descartar o menor número possível de pontos, "
          "e substituímos os descartados por interpolação linear entre os vizinhos válidos (no início "
          "da série, repetimos o primeiro valor válido). <b>Justificativa:</b> descartar o bairro ou o "
          "nível inteiro deixaria buracos no controle deslizante; manter os valores mostraria "
          "resultados impossíveis; a interpolação altera só os pontos suspeitos e usa a informação "
          "dos vizinhos. As linhas alteradas ficam marcadas na coluna " + MONO("corrigido") +
          " e o valor original é preservado em " + MONO("afetados_orig") + "."),
        tabela([["Bairro", "Nível (m)", "Original", "Corrigido", "Problema", "Tratamento"]] + [
            [r.bairro, f"{r.nivel_m:.1f}".replace(".", ","), n(r.valor_original), n(r.valor_corrigido),
             r.problema, r.tratamento] for r in erros.itertuples()],
            [2.7 * cm, 1.5 * cm, 1.6 * cm, 1.7 * cm, 4.2 * cm, 5.3 * cm]),

        PageBreak(),
        p("4.3 Porcentagem arredondada para cima", H2),
        p(f"<b>Onde:</b> campo {MONO('percentage')} em todas as linhas. Em {n(n_teto)} das "
          f"{n(len(bruto))} linhas o valor é o <i>teto</i> de afetados / total × 100, e não o "
          "arredondamento normal. Exemplo: Aberta dos Morros a 3,4 m tem 1 prédio afetado em 4.696 "
          "(0,02%) e o arquivo registra 1%. <b>Por que é um problema:</b> o gráfico pedido na Tela 1 "
          "usa essa porcentagem, e ela superestima todos os bairros pouco afetados. "
          "<b>Tratamento (corrigir):</b> recalcular com duas casas decimais a partir de "
          f"{MONO('affected_buildings / total_buildings')}. O original fica em {MONO('percentage_orig')}."),
        p("<b>Caso particular, erro de ponto flutuante:</b> em Boa Vista do Sul a 7,2 e 7,3 m, "
          "686 / 2.450 dá exatamente 28%, mas o arquivo traz 29%. Em ponto flutuante a conta resulta "
          "em 28,000000000000004 e o teto vira 29. O recálculo resolve."),

        p("4.4 População afetada superestimada", H2),
        p(f"<b>Onde:</b> campo {MONO('affected_population')} em todas as linhas com porcentagem não "
          "inteira. O campo é calculado a partir da porcentagem já arredondada para cima, e ainda "
          "arredondado para cima de novo. <b>Por que é um problema:</b> infla o principal indicador "
          "do dashboard. <b>Tratamento (corrigir):</b> recalcular como população × afetados / total. "
          "Efeito no total da cidade:"),
        tabela([["Nível (m)", "Prédios afetados (original)", "Prédios afetados (limpo)",
                 "Pessoas afetadas (original)", "Pessoas afetadas (limpo)", "Diferença"]] + [
            [f"{nv:.1f}".replace(".", ","), n(cid.loc[nv, "afetados_orig"]), n(cid.loc[nv, "affected_buildings"]),
             n(cid.loc[nv, "affected_population_orig"]), n(cid.loc[nv, "affected_population"]),
             f"{100 * (cid.loc[nv, 'affected_population_orig'] / cid.loc[nv, 'affected_population'] - 1):+.1f}%"
             .replace(".", ",")]
            for nv in (3.0, 4.0, 5.3, 7.0, 10.0)],
            [2 * cm, 3.2 * cm, 3 * cm, 3.2 * cm, 3 * cm, 2.6 * cm]),

        p("4.5 Limitação mantida com aviso: distribuição uniforme da população", H2),
        p("A população afetada supõe que as pessoas se distribuem igualmente entre todos os prédios "
          "do bairro, inclusive os não residenciais. Não é um erro do arquivo e não há como corrigir "
          "com os dados disponíveis. <b>Tratamento (manter e avisar):</b> aviso visível no topo da "
          "Tela 1 e rótulo \"estimativa\" em todos os números de pessoas."),

        p("5. Bases externas: coleta e limpeza", H1),
        tabela([
            ["Base", "Coleta por código", "Problemas encontrados e tratamento"],
            ["UFRGS / Zenodo, banco de dados das cheias de maio de 2024 (v1.4, CC-BY-4.0)",
             "API REST do Zenodo. Verifica o checksum MD5 e não baixa de novo o que já está no disco. "
             "Grava fonte, versão, licença e data em " + MONO("metadados_coleta.json") + ".",
             "Arquivo de 217,6 MB, fora do Git. Camadas em sistemas de coordenadas diferentes "
             "(reprojetadas para SIRGAS 2000 / UTM 22S). Geometrias inválidas e com coordenada Z "
             "(corrigidas). O glossário traz descrições trocadas em algumas camadas, por isso o "
             "nível de cada mancha foi tirado do nome da camada."],
            ["ObservaPOA, limites oficiais dos bairros",
             "Download automatizado do Shapefile publicado na página de mapas.",
             "128 polígonos para 94 bairros (bairros em mais de uma parte foram unidos). Nomes em "
             "maiúsculas e sem acento: casados com os do INCT sem acento e sem apóstrofo. Dois nomes "
             "precisaram de equivalência manual: CEL. APARICIO BORGES e PASSO DA AREIA."],
            ["Escolas (INEP 2023) e abrigos de 24/05/2024, incluídos no registro do Zenodo",
             "Mesmo script do Zenodo.",
             f"Escolas filtradas para Porto Alegre ({len(escolas)}) e associadas ao bairro pelo ponto. "
             f"Abrigos sem coordenada foram descartados; restaram {n(abrigos.abrigos.sum())} abrigos em "
             f"{len(abrigos)} bairros. Nomes e endereços dos abrigos não vão para o dashboard."],
        ], [3.8 * cm, 4.6 * cm, 8.6 * cm]),
        Spacer(1, 6),
        p(f"<b>Primeiro resultado do cruzamento:</b> a 5,3 m, a porcentagem de prédios afetados do "
          f"INCT e a porcentagem de área inundada observada por satélite em 06/05/2024 têm correlação "
          f"de {comp.percentage.corr(comp.pct_area):.2f} entre os 94 bairros.".replace("0.", "0,")),

        PageBreak(),
        p("6. Esboço das duas telas", H1),
        figura(IMG / "wireframes.png"),

        p("7. Como reproduzir", H2),
        p(MONO("pip install -r requirements.txt") + "<br/>" +
          MONO("python scripts/limpeza_inct.py") + "<br/>" +
          MONO("python scripts/coleta_bairros.py") + "<br/>" +
          MONO("python scripts/coleta_zenodo.py") + " (baixa cerca de 220 MB)<br/>" +
          MONO("python scripts/processa_tela2.py") + "<br/>" +
          MONO("python scripts/gerar_relatorios.py")),
        p("Registro de uso de IA", H2),
        p("O Claude Code foi usado em 11/11/2026 para escrever os scripts de limpeza, coleta e "
          "processamento, o notebook de EDA e este relatório, a partir das decisões descritas acima. "
          "O autor deve revisar e saber explicar cada parte. O histórico está em AI_LOG.md.", SMALL),
    ]
    pdf("limpeza_dados.pdf", "Fase 2 - Limpeza de dados", s)


# ---------------------------------------------------------------------- relatório do dashboard
def relatorio_dashboard(limpo, area, escolas):
    a53 = limpo[np.isclose(limpo.nivel_m, 5.3)]
    obs = area[area.tipo == "observada"]
    comp = a53[["bairro", "percentage"]].merge(obs[["bairro", "pct_area"]], on="bairro")
    link = LINK_DASHBOARD or "ainda não publicado (ver seção 6)"
    s = [
        p("Fase 3 · Relatório do dashboard", H1),
        p("Projeto Extensionista · Dashboard de Enchentes em Porto Alegre · INCT SiMAI", P),
        p(f"Autor: {AUTOR} · Repositório: {REPO}<br/>Link do dashboard: {link}", P),

        p("1. Ponto de partida: a ferramenta atual do INCT", H2),
        p("Observações feitas em 11/11/2026 na página http://vhlab.com.br/INCT/floods/:"),
        tabela([
            ["O que funciona", "O que atrapalha"],
            ["Mapa interativo com a região inundada e controle do nível de 3,0 a 10,0 m.<br/>"
             "Totais da cidade (prédios e população afetados) visíveis ao lado do mapa.<br/>"
             "Histórico recente do nível do rio na mesma página.",
             "Abre em inglês (\"Affected Buildings\", \"Select grid\"); o português fica atrás de um botão.<br/>"
             "A busca pede seis campos (país, estado, cidade, bairro, rua, CEP) para chegar a um lugar.<br/>"
             "Não há ranking nem comparação entre bairros na tela inicial.<br/>"
             "Parâmetros técnicos sem explicação (\"Road Size: 0.0002\").<br/>"
             "Mostra os totais do arquivo original: a 5,3 m, 138.414 pessoas e 53.989 prédios, "
             f"contra {n(a53.affected_population.sum())} e {n(a53.affected_buildings.sum())} depois da limpeza.<br/>"
             "Não há aviso de que os números são estimativas."],
        ], [8.5 * cm, 8.5 * cm]),
        p("Estas observações vieram de uma leitura automatizada da página. As impressões de uso do "
          "autor (tempo de carregamento, travamentos) devem ser acrescentadas aqui.", SMALL),

        p("2. Tela 1 · Simulação do INCT", H2),
        p("<b>Objetivo:</b> responder \"se o rio chegar a X metros, quais bairros e quantas pessoas "
          "são afetados?\" usando só o JSON do INCT depois de limpo."),
        tabela([
            ["Elemento", "Por que foi escolhido"],
            ["Controle deslizante do nível (3,0 a 10,0 m, passo 0,1 m)",
             "Requisito. Atualiza todos os elementos da tela. Começa em 5,3 m, o nível mais próximo do recorde."],
            ["Três indicadores: pessoas, prédios e bairros atingidos",
             "Requisito. Cada um traz a proporção em relação ao total da cidade, para dar escala."],
            ["Mapa dos bairros colorido pela % de prédios (2D ou 3D)",
             "Diferencial. Mostra de relance que o impacto se concentra na faixa baixa da cidade. "
             "No modo 3D a altura do bairro também representa a porcentagem."],
            ["Barras horizontais: % de prédios em cada bairro atingido",
             "Requisito. Barras ordenadas permitem comparar bairros; só aparecem os atingidos no nível escolhido."],
            ["Ranking dos 15 bairros mais afetados",
             "Requisito. Pode ser ordenado por pessoas ou por porcentagem, porque os dois critérios "
             "destacam bairros diferentes (Sarandi lidera em pessoas; Farrapos e Humaitá em porcentagem)."],
            ["Curva da população afetada por nível, com 5,35 m marcado",
             "Requisito. O ponto do nível escolhido aparece sobre a curva, ligando o controle ao contexto."],
            ["Aviso de limitações no topo e detalhes no fim",
             "Requisito e cuidado ético: deixa claro que são estimativas de simulação."],
        ], [6 * cm, 11 * cm]),
        figura(IMG / "tela1.jpg", 15),

        PageBreak(),
        p("3. Tela 2 · Simulação × enchente de 2024", H2),
        p("<b>Objetivo:</b> responder \"a simulação do INCT bate com a inundação observada em maio de "
          "2024, e quais bairros divergem?\" usando o banco de dados das cheias da UFRGS (Zenodo)."),
        tabela([
            ["Elemento", "Por que foi escolhido"],
            ["Filtro da camada da UFRGS (observada por satélite ou simulada de 2,94 a 7,00 m)",
             "Filtro interativo. O dashboard escolhe sozinho o nível do INCT mais próximo da camada."],
            ["Dispersão por bairro: % prédios (INCT) × % área (UFRGS)",
             "Liga a base externa à Tela 1 pelos bairros. A diagonal mostra onde as bases concordam; "
             "os bairros com mais de 20 p.p. de diferença recebem rótulo."],
            ["Mapa da diferença INCT − UFRGS com o contorno da mancha",
             "Mostra onde ficam os bairros divergentes. Escala divergente, com neutro no zero."],
            ["Curvas por nível: INCT × UFRGS (filtro por bairro)",
             "Liga a base externa à Tela 1 pelo nível do Guaíba, na cidade toda ou em um bairro."],
            ["Barras: escolas em área alagada a cada nível (filtro por rede)",
             "Responde a um dos exemplos do enunciado com o Censo Escolar do INEP."],
            ["Barras: abrigos por bairro em 24/05/2024",
             "Mostra para onde as pessoas foram, colorido pelo impacto do bairro na simulação."],
            ["Fontes com link, licença e data de coleta", "Requisito."],
        ], [6 * cm, 11 * cm]),
        figura(IMG / "tela2.jpg", 15),
        p(f"<b>Resultado principal:</b> a 5,3 m, a correlação entre as duas bases é de "
          f"{comp.percentage.corr(comp.pct_area):.2f}".replace("0.", "0,") +
          f"; {int(((comp.percentage - comp.pct_area).abs() > 20).sum())} bairros têm diferença acima "
          f"de 20 pontos percentuais; {int(escolas['rhguaiba_planet-skysat_inundacao_obs_20240506'].sum())} "
          f"das {len(escolas)} escolas de Porto Alegre ficam dentro da mancha observada."),

        PageBreak(),
        p("4. Como usar", H2),
        p("1. Na Tela 1, arraste o controle do nível do Guaíba. Indicadores, mapa, barras e ranking "
          "mudam juntos; passe o mouse sobre um bairro para ver os números.<br/>"
          "2. Ligue \"Ver em 3D\" para o mapa em perspectiva.<br/>"
          "3. No ranking, troque entre \"Pessoas afetadas\" e \"% de prédios\".<br/>"
          "4. Na Tela 2 (menu lateral), escolha a camada da UFRGS, a rede das escolas e, na seção das "
          "curvas, um bairro.<br/>"
          "5. Para rodar localmente: " + MONO("pip install -r requirements.txt") + " e " +
          MONO("streamlit run app/app.py") + "."),

        p("5. Limitações", H2),
        p("• Os números são estimativas de uma simulação, não previsões nem contagens oficiais.<br/>"
          "• A população afetada supõe distribuição uniforme das pessoas entre os prédios do bairro.<br/>"
          "• O resultado é por bairro: não diz quais ruas ou casas são atingidas.<br/>"
          "• 17 valores do arquivo do INCT foram corrigidos por interpolação e todas as porcentagens "
          "foram recalculadas (ver limpeza_dados.pdf).<br/>"
          "• Na Tela 2, o INCT mede prédios e a UFRGS mede área. A diferença entre as duas não prova "
          "erro de nenhuma delas.<br/>"
          "• A base da UFRGS é um esforço voluntário; a mancha observada é de um único dia "
          "(06/05/2024) e a comparação usa o nível do INCT mais próximo, com passo de 0,1 m.<br/>"
          "• As manchas foram simplificadas (tolerância de 25 m) para o mapa carregar rápido."),

        p("6. Publicação", H2),
        p(f"Link público: {link}. O aplicativo está pronto para o Streamlit Community Cloud: "
          "repositório " + REPO + ", arquivo principal " + MONO("app/app.py") + ". Os dados "
          "processados estão versionados, então a publicação não precisa baixar nada."),

        p("Registro de uso de IA", H2),
        p("O Claude Code foi usado em 11/11/2026 para escrever o código do dashboard e este "
          "relatório. O autor deve revisar e saber explicar cada parte. O histórico está em AI_LOG.md.",
          SMALL),
    ]
    pdf("dashboard.pdf", "Fase 3 - Relatório do dashboard", s)


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    bruto = carregar_longo()
    limpo = pd.read_csv(PROC / "inct_limpo.csv")
    erros = pd.read_csv(PROC / "inct_inconsistencias.csv")
    area = pd.read_csv(PROC / "ufrgs_area_bairro.csv")
    escolas = pd.read_csv(PROC / "escolas_poa.csv")
    abrigos = pd.read_csv(PROC / "abrigos_poa.csv")
    fig_inconsistencias(bruto, limpo, erros)
    fig_wireframes()
    relatorio_limpeza(bruto, limpo, erros, area, escolas, abrigos)
    relatorio_dashboard(limpo, area, escolas)


if __name__ == "__main__":
    main()
