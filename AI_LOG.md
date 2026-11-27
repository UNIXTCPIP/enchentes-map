# Registro de uso de IA

O enunciado permite ferramentas de IA desde que cada uso seja registrado e que o autor saiba explicar o código. Ferramenta usada: Claude Code (Anthropic).

| Data | Fase | O que a IA fez | Arquivos |
|---|---|---|---|
| 26/10/2026 | Preparação | Diagnóstico de autenticação do Git; leitura e resumo do enunciado; discussão sobre o mapa 3D | nenhum |
| 28/10/2026 | Fase 1 | Pesquisa e verificação de bases externas (API do Zenodo, SIDRA, portais); redação do relatório | `scripts/gerar_relatorio_base_dados.py`, `relatorios/base_dados.pdf` |
| 11/11/2026 | Fase 2 | Busca das inconsistências do `data.json`; script de limpeza; scripts de coleta (Zenodo e ObservaPOA); processamento da base da UFRGS; notebook de EDA; relatório | `scripts/limpeza_inct.py`, `scripts/coleta_zenodo.py`, `scripts/coleta_bairros.py`, `scripts/processa_tela2.py`, `notebooks/eda.ipynb`, `relatorios/limpeza_dados.pdf` |
| 11/11/2026 | Fase 3 | Código do dashboard (duas telas); relatório do dashboard; README | `app/*.py`, `scripts/gerar_relatorios.py`, `relatorios/dashboard.pdf`, `README.md` |
| 27/11/2026 | Versão final | Commit e push das Fases 2 e 3; dependências do app em `app/requirements.txt`; teste do dashboard a partir de um clone limpo; publicação no Streamlit Community Cloud (login e autorização feitos pelo autor); atualização do README e dos relatórios | `app/requirements.txt`, `README.md`, `scripts/gerar_relatorios.py`, `relatorios/dashboard.pdf` |

## Decisões que o autor precisa saber explicar

- **Limpeza:** prédios afetados não podem diminuir quando o rio sobe. Para cada bairro, mantém-se a maior sequência não decrescente de pontos e interpolam-se os demais (17 valores em 5 bairros).
- **Porcentagens:** o arquivo original arredonda para cima; `percentage` e `affected_population` foram recalculados a partir de `affected_buildings / total_buildings`.
- **Tela 2:** compara % de prédios (INCT) com % de área inundada (UFRGS). São medidas diferentes, e isso está avisado na tela.
- **Nível das manchas da UFRGS:** tirado do nome da camada, porque o glossário da base tem descrições trocadas.
