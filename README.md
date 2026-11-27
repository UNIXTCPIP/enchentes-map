# Dashboard interativo de enchentes em Porto Alegre

Projeto extensionista da disciplina Coleta, Preparação e Análise de Dados (PUCRS), em parceria com o INCT SiMAI.

**Aluno:** Renato Trindade

**Dashboard publicado:** https://enchentes-porto-alegre.streamlit.app

> Os números são estimativas de uma simulação, não previsões nem contagens oficiais.

## O que o dashboard responde

- **Tela 1 · Simulação do INCT:** se o Guaíba chegar a X metros, quais bairros e quantas pessoas são afetados?
- **Tela 2 · Simulação × enchente de 2024:** a simulação do INCT bate com a inundação observada em maio de 2024, e quais bairros divergem?

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app.py
```

Os dados processados já estão em `dados/processados/`, então o dashboard roda sem baixar nada.

## Como refazer os dados do zero

```bash
python scripts/limpeza_inct.py      # limpa o data.json do INCT
python scripts/coleta_bairros.py    # baixa a malha de bairros do ObservaPOA
python scripts/coleta_zenodo.py     # baixa a base da UFRGS pela API do Zenodo (cerca de 220 MB)
python scripts/processa_tela2.py    # cruza a base da UFRGS com os bairros (cerca de 2 min)
python scripts/gerar_relatorios.py  # gera relatorios/limpeza_dados.pdf e dashboard.pdf
jupyter nbconvert --to notebook --execute --inplace notebooks/eda.ipynb
```

## Fontes dos dados

| Dado | Fonte | Coleta |
|---|---|---|
| Simulação por bairro e nível | INCT SiMAI, `data.json` fornecido na disciplina | arquivo fornecido |
| Manchas de inundação, escolas (INEP 2023) e abrigos | [Banco de dados das cheias na Região Hidrográfica do Lago Guaíba em Maio de 2024](https://zenodo.org/records/14617475), UFRGS e colaboradores, v1.4, CC-BY-4.0 | API do Zenodo, em 11/11/2026 |
| Limites oficiais dos bairros | [ObservaPOA / Prefeitura de Porto Alegre](https://prefeitura.poa.br/smpg/observapoa/mapas) | download automatizado, em 11/11/2026 |

## Estrutura do repositório

```
enchentes-map/
├── README.md
├── requirements.txt
├── AI_LOG.md             # registro de uso de IA
├── dados/
│   ├── originais/        # data.json do INCT; bases externas são baixadas pelos scripts
│   └── processados/      # dados limpos usados pelo dashboard
├── scripts/              # coleta, limpeza, processamento e geração dos relatórios
├── notebooks/            # eda.ipynb
├── relatorios/           # base_dados.pdf, limpeza_dados.pdf, dashboard.pdf
└── app/                  # código do dashboard (Streamlit)
```

## Publicação

Publicado no Streamlit Community Cloud em https://enchentes-porto-alegre.streamlit.app (repositório `UNIXTCPIP/enchentes-map`, branch `main`, arquivo principal `app/app.py`, dependências do app em `app/requirements.txt`). Cada push na `main` atualiza o app.

## Uso de IA

O projeto usou o Claude Code. Cada uso está registrado em [AI_LOG.md](AI_LOG.md).
