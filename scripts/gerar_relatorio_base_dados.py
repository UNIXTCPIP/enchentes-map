"""Gera relatorios/base_dados.pdf (Fase 1: levantamento de bases externas)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

SAIDA = Path(__file__).resolve().parents[1] / "relatorios" / "base_dados.pdf"
DATA_LEVANTAMENTO = "28/10/2026"
EQUIPE = "Renato Trindade"

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceAfter=6)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=10, spaceAfter=4)
P = ParagraphStyle("P", parent=ss["BodyText"], fontSize=9.5, leading=13)
SMALL = ParagraphStyle("S", parent=P, fontSize=8, leading=10)
CELL = ParagraphStyle("C", parent=P, fontSize=8, leading=10)
CELLB = ParagraphStyle("CB", parent=CELL, fontName="Helvetica-Bold")


def p(txt, style=P):
    return Paragraph(txt, style)


def tabela(linhas, larguras, cab=True):
    dados = [[p(c, CELLB if (cab and i == 0) else CELL) for c in l] for i, l in enumerate(linhas)]
    t = Table(dados, colWidths=larguras, repeatRows=1 if cab else 0)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe7f3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def ficha(titulo, linhas):
    return [p(titulo, H2), tabela([["Item", "Descrição"]] + linhas, [3.6 * cm, 13.4 * cm])]


story = [
    p("Fase 1 · Levantamento de bases sobre enchentes no RS", H1),
    p("Projeto Extensionista · Dashboard de Enchentes em Porto Alegre · INCT SiMAI", P),
    p(f"Equipe: {EQUIPE}<br/>Data do levantamento: {DATA_LEVANTAMENTO}", P),
    Spacer(1, 6),

    p("1. Resumo e escolha para a Tela 2", H2),
    p("Foram levantadas <b>7 bases</b> (seção 3). A base principal escolhida para a Tela 2 é o "
      "<b>Banco de dados das cheias na Região Hidrográfica do Lago Guaíba em Maio de 2024</b> "
      "(UFRGS, publicado no Zenodo, CC-BY-4.0), complementada pela malha de bairros e, se houver tempo, "
      "pelo Censo 2022 (API SIDRA do IBGE)."),
    p("<b>Pergunta que a Tela 2 vai responder:</b> <i>a simulação do INCT bate com a inundação "
      "realmente observada em maio de 2024, e quais bairros divergem?</i> Em outras palavras: para cada "
      "bairro, comparar a porcentagem de prédios afetados na simulação do INCT (nível ~5,3 m) com a área "
      "efetivamente inundada observada por sensoriamento remoto, e mostrar quantas escolas e abrigos "
      "ficam em área alagada a cada nível."),

    p("2. Como a escolha se liga à Tela 1", H2),
    tabela([
        ["Requisito do enunciado", "Como a base escolhida atende"],
        ["Pelo menos 1 base obtida por código (API, scraping ou download automatizado)",
         "API REST do Zenodo (<font face='Courier'>zenodo.org/api/records/...</font>) baixa o GeoPackage por script."],
        ["Pelo menos 1 visualização que relacione a base externa à Tela 1 "
         "(bairros, nível do Guaíba ou enchente de 2024)",
         "A camada <font face='Courier'>poa_admin_bairros</font> permite cruzar por bairro, e a camada "
         "<font face='Courier'>poa_inundacao_2024_530cm</font> corresponde ao nível do slider em 5,3 m."],
        ["Pelo menos 3 visualizações e 1 filtro interativo",
         "(i) mapa comparativo observado × simulado; (ii) dispersão % prédios afetados INCT × % área "
         "inundada por bairro; (iii) escolas/abrigos em área alagada por nível. Filtros: nível, bairro e camada."],
        ["Fonte, link e data de coleta de cada dado",
         "Registrados em metadados no script de coleta (DOI, versão, licença, data)."],
    ], [6 * cm, 11 * cm]),

    PageBreak(),
    p("3. Bases encontradas", H1),
]

story += ficha("3.1 UFRGS · Banco de dados das cheias na RH do Lago Guaíba, maio de 2024 (ESCOLHIDA)", [
    ["Origem", "Pesquisadores da UFRGS e colaboradores (esforço voluntário). Zenodo, conceito 11164049; "
               "versão mais recente verificada: v1.4, 08/01/2025 (registro 14617475)."],
    ["Link", "https://zenodo.org/records/14617475 (versões: https://zenodo.org/records/11164049)"],
    ["Conteúdo", "GeoPackage com 35 camadas (glossário no próprio registro). Relevantes: "
                 "<font face='Courier'>poa_admin_bairros</font>; "
                 "<font face='Courier'>poa_inundacao_2024_530cm</font>; simulações hidrostáticas de "
                 "500, 550, 600, 650 e 700 cm; cheias históricas (1941 a 475 cm, 1967, 2015, 2023); "
                 "<font face='Courier'>poa_pontos_nivel</font> (observações de campo); inundação observada "
                 "por satélite (Sentinel-2, Planet/SkySat) em 06/05/2024; abrigos "
                 "(<font face='Courier'>rs_crise_abrigos_*.csv</font>) e escolas INEP 2023."],
    ["Recorte", "Espacial: Região Hidrográfica do Lago Guaíba (não cobre todo o RS); camadas "
                "<font face='Courier'>poa_*</font> cobrem Porto Alegre. Temporal: evento de maio de 2024, "
                "mais cheias históricas pontuais."],
    ["Formato / tamanho", "GeoPackage (.gpkg), 217,6 MB (v1.4), além de CSVs pequenos. Leitura com geopandas."],
    ["Coleta", "API REST do Zenodo (metadados e links de arquivo), por script em Python."],
    ["Licença", "CC-BY-4.0 (citar a fonte)."],
    ["Ligação com o INCT", "Mesmo território (bairros de Porto Alegre) e mesmos níveis do rio; "
                           "permite validar a simulação do INCT contra a mancha observada."],
    ["Limitações", "Os próprios autores avisam que é um esforço emergencial e voluntário, em evolução. "
                   "As camadas observadas são de um dia (06/05/2024). Tamanho grande: não vai para o Git; "
                   "o dashboard usará um recorte processado e pequeno."],
])

story += ficha("3.2 ObservaPOA · limites oficiais dos bairros", [
    ["Origem", "Prefeitura de Porto Alegre (ObservaPOA)."],
    ["Link", "https://prefeitura.poa.br/smpg/observapoa/mapas"],
    ["Conteúdo", "Limites dos bairros em Shapefile e KML (indicado pelo enunciado para o mapa)."],
    ["Formato", "SHP / KML. Download automatizado por script ainda a confirmar (página institucional)."],
    ["Licença", "A confirmar nos termos de uso do portal."],
    ["Ligação com o INCT", "Chave de junção por nome de bairro. Atenção à grafia (acentos e apóstrofos)."],
    ["Limitações", "A camada <font face='Courier'>poa_admin_bairros</font> do Zenodo pode servir de reserva "
                   "se o download automático do ObservaPOA não for viável."],
])

story += ficha("3.3 IBGE · Censo 2022 via API SIDRA", [
    ["Origem", "IBGE."],
    ["Link", "https://apisidra.ibge.gov.br (exemplo testado: tabela 4709, município 4314902)."],
    ["Conteúdo", "População e domicílios por município; renda e perfil em níveis mais detalhados "
                 "(setores censitários) via malhas de download."],
    ["Coleta", "API REST (resposta JSON verificada em 28/10/2026)."],
    ["Ligação com o INCT", "O campo <font face='Courier'>population</font> do INCT já vem do Censo 2022. "
                           "A renda permitiria testar se os bairros mais expostos são os de menor renda."],
    ["Limitações", "Renda por bairro exige agregar setores censitários (trabalho extra). "
                   "Fica como extensão da Tela 2."],
])

story += ficha("3.4 SGB/CPRM e ANA · nível do Guaíba (SACE e Hidroweb)", [
    ["Origem", "Serviço Geológico do Brasil (SACE) e Agência Nacional de Águas (Hidroweb)."],
    ["Link", "https://www.sgb.gov.br/sace/ e portal Hidroweb (snirh.gov.br)."],
    ["Conteúdo", "Séries de nível do Guaíba (estação Gasômetro) e boletins diários em PDF."],
    ["Coleta", "Testado em 28/10/2026: o SACE respondeu 403 a um acesso automatizado simples e a "
               "API do Hidroweb respondeu 401, ou seja, exige cadastro/credenciais."],
    ["Ligação com o INCT", "Responderia 'como o nível se comportou ao longo dos anos e quantas vezes passou "
                           "a cota de inundação'."],
    ["Limitações", "Acesso programático depende de cadastro; boletins em PDF dão trabalho de extração. "
                   "Candidata para uma segunda etapa."],
])

story += ficha("3.5 INPE · International Charter, mancha de inundação RS 2024", [
    ["Origem", "INPE, ativação do Charter para o evento no RS."],
    ["Link", "https://data.inpe.br/charter/data/Call_1003_Brazil_RS/ (acesso verificado, HTTP 200)."],
    ["Conteúdo", "Vetores da mancha de inundação derivados de radar, com metadados em PDF."],
    ["Limitações", "Formato exato, licença e cobertura sobre Porto Alegre a confirmar. A base do Zenodo já "
                   "traz a mancha de 06/05/2024, o que a torna mais direta."],
])

story += ficha("3.6 Governo do RS · Transparência RS / Defesa Civil", [
    ["Origem", "Governo do Estado do RS (portal Transparência RS, painéis sobre as cheias de 2024)."],
    ["Link", "https://transparencia.rs.gov.br/ (acesso verificado, HTTP 200)."],
    ["Conteúdo", "Repasses do Fundo Estadual de Defesa Civil, execução orçamentária da calamidade e "
                 "balanços por município."],
    ["Ligação com o INCT", "Responde 'quais municípios do RS tiveram mais pessoas desalojadas ou mais danos "
                           "em 2024', mas em escala municipal, não de bairro."],
    ["Limitações", "Formato de exportação e licença a confirmar. Não se liga diretamente à Tela 1."],
])

story += ficha("3.7 Fique Sabendo · bases abertas sobre a tragédia no RS (curadoria)", [
    ["Origem", "Fique Sabendo (jornalismo de dados), matéria 'Um ano da tragédia no RS: bases abertas'."],
    ["Link", "https://news.fiquemsabendo.com.br/p/um-ano-da-tragedia-no-rs-bases-abertas"],
    ["Conteúdo", "Lista comentada de bases públicas sobre a enchente."],
    ["Uso", "Não é uma base de dados em si: serve como fonte para descobrir outras bases na Fase 2."],
])

story += [
    PageBreak(),
    p("4. Comparação e justificativa", H1),
    tabela([
        ["Base", "Coleta por código", "Liga à Tela 1", "Escala", "Esforço", "Decisão"],
        ["UFRGS / Zenodo", "Sim (API)", "Forte (bairro, nível, 2024)", "Quadra a bairro", "Médio", "<b>Escolhida</b>"],
        ["ObservaPOA bairros", "A confirmar", "Forte (chave)", "Bairro", "Baixo", "Apoio (mapa)"],
        ["IBGE SIDRA", "Sim (API)", "Média", "Município a setor", "Médio/alto", "Extensão"],
        ["SGB/ANA nível", "Exige cadastro", "Média (nível)", "Estação", "Alto", "2ª etapa"],
        ["INPE Charter", "A confirmar", "Média", "Mancha", "Médio", "Reserva"],
        ["Transparência RS", "A confirmar", "Fraca", "Município", "Médio", "Descartada por ora"],
        ["Fique Sabendo", "Não se aplica", "Não se aplica", "Não se aplica", "Baixo", "Fonte de busca"],
    ], [3.3 * cm, 2.6 * cm, 3.4 * cm, 2.6 * cm, 2.1 * cm, 3 * cm]),
    Spacer(1, 8),
    p("<b>Por que a UFRGS/Zenodo:</b> é a única base que combina (a) o mesmo recorte geográfico do INCT, "
      "(b) a enchente real de maio de 2024 e (c) simulações em níveis parecidos com os do slider, "
      "além de escolas e abrigos. Tem licença aberta, versão e DOI citáveis e pode ser baixada por API, "
      "o que cumpre o requisito de coleta por código."),
    p("<b>Riscos e mitigação:</b>"),
    p("• Arquivo de 217,6 MB: o script baixa uma vez para <font face='Courier'>dados/originais/</font> "
      "(fora do Git) e gera arquivos pequenos em <font face='Courier'>dados/processados/</font> para o app.<br/>"
      "• Divergência de grafia dos bairros entre fontes: normalizar nomes (acentos, apóstrofos) e "
      "registrar o mapeamento.<br/>"
      "• Camada observada é de um único dia e foi produzida por voluntários: avisar no dashboard que "
      "se trata de estimativa, não de contagem oficial, conforme os cuidados éticos do enunciado."),

    p("5. Próximos passos (Fase 2)", H2),
    p("1. Script <font face='Courier'>scripts/coleta_zenodo.py</font> (download via API + metadados).<br/>"
      "2. Extrair camadas de bairros, mancha observada, simulação 530 cm, escolas e abrigos para "
      "<font face='Courier'>dados/processados/</font>.<br/>"
      "3. Limpar o <font face='Courier'>data.json</font> do INCT e documentar as inconsistências.<br/>"
      "4. EDA com 6 a 10 gráficos e wireframes das duas telas."),

    p("Registro de uso de IA", H2),
    p("Ferramenta de IA (Claude Code) foi usada em 28/10/2026 para pesquisar e verificar as bases "
      "(consultas às APIs do Zenodo e SIDRA, testes de acesso aos portais) e para gerar o script deste "
      "relatório. Todo o conteúdo deve ser revisado pela equipe antes da entrega.", SMALL),
]

SAIDA.parent.mkdir(exist_ok=True)
SimpleDocTemplate(str(SAIDA), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                  topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                  title="Fase 1 - Levantamento de bases", author="Equipe Enchentes POA").build(story)
print("gerado:", SAIDA)
