"""Limpeza do data.json do INCT SiMAI.

Lê dados/originais/data.json, converte para formato longo (uma linha por nível e
bairro), detecta e trata as inconsistências e grava:

  dados/processados/inct_limpo.csv           dados usados pelo dashboard
  dados/processados/inct_inconsistencias.csv registro de cada valor alterado

Decisões (justificadas em relatorios/limpeza_dados.pdf):
  1. Ordem dos bairros: nunca usar a posição, sempre a chave (o nível 5,3 m vem
     em outra ordem).
  2. Prédios afetados devem ser não decrescentes quando o rio sobe. Mantemos a
     maior subsequência não decrescente de cada bairro (o menor número possível
     de pontos descartados) e interpolamos linearmente os pontos descartados.
  3. percentage e affected_population são recalculados com precisão total a
     partir de affected_buildings / total_buildings (o original arredonda para
     cima e para inteiro, o que superestima a população afetada).

Uso: python scripts/limpeza_inct.py
"""
import json
from bisect import bisect_right
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "dados" / "originais" / "data.json"
SAIDA = RAIZ / "dados" / "processados"


def carregar_longo(caminho: Path = ENTRADA) -> pd.DataFrame:
    """JSON aninhado -> uma linha por (nível, bairro), ordenado por bairro e nível."""
    with open(caminho, encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame([
        {"nivel_m": float(nivel.removesuffix("m").replace("_", ".")),
         "bairro": bairro.strip(), **valores}
        for nivel, bairros in raw.items()
        for bairro, valores in bairros.items()
    ])
    return df.sort_values(["bairro", "nivel_m"], ignore_index=True)


def maior_subsequencia_nao_decrescente(valores) -> np.ndarray:
    """Máscara booleana dos pontos da maior subsequência não decrescente."""
    caudas, idx_caudas, anterior = [], [], [-1] * len(valores)
    for i, v in enumerate(valores):
        pos = bisect_right(caudas, v)
        if pos == len(caudas):
            caudas.append(v)
            idx_caudas.append(i)
        else:
            caudas[pos] = v
            idx_caudas[pos] = i
        anterior[i] = idx_caudas[pos - 1] if pos > 0 else -1
    manter = np.zeros(len(valores), dtype=bool)
    i = idx_caudas[-1]
    while i != -1:
        manter[i] = True
        i = anterior[i]
    return manter


def classificar(original: int, corrigido: int) -> str:
    if original == 0 and corrigido > 0:
        return "zero isolado (falha de registro)"
    if original > corrigido:
        return "valor acima da tendência (pico)"
    return "valor abaixo da tendência (queda)"


def limpar(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.rename(columns={"affected_buildings": "afetados_orig",
                            "percentage": "percentage_orig",
                            "affected_population": "affected_population_orig"})
    partes, registros = [], []
    for bairro, g in df.groupby("bairro", sort=False):
        g = g.copy()
        manter = maior_subsequencia_nao_decrescente(g["afetados_orig"].tolist())
        serie = g["afetados_orig"].where(manter).astype(float)
        # interpola dentro da série; nas pontas repete o valor válido mais próximo
        serie = serie.interpolate(method="linear", limit_direction="both")
        g["affected_buildings"] = serie.round().astype(int)
        g["corrigido"] = ~manter
        for i in np.flatnonzero(~manter):
            linha = g.iloc[i]
            registros.append({
                "bairro": bairro, "nivel_m": linha["nivel_m"],
                "valor_original": int(linha["afetados_orig"]),
                "valor_corrigido": int(linha["affected_buildings"]),
                "problema": classificar(int(linha["afetados_orig"]),
                                        int(linha["affected_buildings"])),
                "tratamento": "interpolação linear entre vizinhos válidos"
                              if 0 < i and manter[:i].any() else
                              "repetição do primeiro valor válido (início da série)",
            })
        partes.append(g)
    limpo = pd.concat(partes, ignore_index=True)

    fracao = limpo["affected_buildings"] / limpo["total_buildings"]
    limpo["percentage"] = (100 * fracao).round(2)
    limpo["affected_population"] = (limpo["population"] * fracao).round().astype(int)

    colunas = ["nivel_m", "bairro", "affected_buildings", "total_buildings", "percentage",
               "population", "affected_population", "corrigido",
               "afetados_orig", "percentage_orig", "affected_population_orig"]
    return limpo[colunas], pd.DataFrame(registros)


def validar(limpo: pd.DataFrame) -> None:
    assert limpo.shape[0] == 71 * 94, limpo.shape
    assert not limpo.duplicated(["nivel_m", "bairro"]).any()
    assert (limpo.groupby("bairro")["affected_buildings"].diff().dropna() >= 0).all()
    assert (limpo["affected_buildings"] <= limpo["total_buildings"]).all()
    assert limpo["percentage"].between(0, 100).all()
    assert (limpo["affected_population"] <= limpo["population"]).all()
    assert (limpo.groupby("bairro")[["total_buildings", "population"]].nunique() == 1).all().all()


def main() -> None:
    bruto = carregar_longo()
    print("formato longo:", bruto.shape)
    limpo, registro = limpar(bruto)
    validar(limpo)
    SAIDA.mkdir(parents=True, exist_ok=True)
    limpo.to_csv(SAIDA / "inct_limpo.csv", index=False)
    registro.to_csv(SAIDA / "inct_inconsistencias.csv", index=False)
    print(f"{len(registro)} valores corrigidos em {registro['bairro'].nunique()} bairros")
    print(registro.groupby(["bairro", "problema"]).size().to_string())


if __name__ == "__main__":
    main()
