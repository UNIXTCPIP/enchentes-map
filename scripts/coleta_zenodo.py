"""Coleta da base externa (Tela 2) pela API REST do Zenodo.

Base: "Banco de dados das cheias na Região Hidrográfica do Lago Guaíba em Maio de 2024"
(UFRGS e colaboradores), licença CC-BY-4.0, DOI do conceito 10.5281/zenodo.11164049.

O script consulta os metadados do registro, baixa os arquivos necessários para
dados/originais/zenodo/ e grava um arquivo de metadados com fonte, versão, licença,
data de coleta e checksum. Arquivos já baixados e íntegros não são baixados de novo
(coleta responsável: não repetir requisições).

Uso: python scripts/coleta_zenodo.py
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

# Registro fixado (v1.4, 08/01/2025) para o resultado ser reprodutível.
RECORD_ID = "14617475"
API = f"https://zenodo.org/api/records/{RECORD_ID}"
DESTINO = Path(__file__).resolve().parents[1] / "dados" / "originais" / "zenodo"
ARQUIVOS = [
    "cheias_rhguaiba_2024_db_v14.gpkg",           # banco principal (bairros, manchas, simulações)
    "cheias_rhguaiba_2024_db_v14_glossario.csv",  # descrição das camadas
    "insumos_inep_escolas_2023_rs.gpkg",          # escolas (INEP 2023)
    "rs_crise_abrigos_24052024_20h.csv",          # abrigos em 24/05/2024
]
HEADERS = {"User-Agent": "enchentes-map (projeto academico PUCRS; coleta unica)"}


def md5(caminho: Path) -> str:
    h = hashlib.md5()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def baixar(url: str, caminho: Path) -> None:
    parcial = caminho.with_suffix(caminho.suffix + ".part")
    with requests.get(url, headers=HEADERS, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(parcial, "wb") as f:
            for bloco in r.iter_content(1 << 20):
                f.write(bloco)
    parcial.rename(caminho)


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    registro = requests.get(API, headers=HEADERS, timeout=60).json()
    meta = registro["metadata"]
    disponiveis = {f["key"]: f for f in registro["files"]}

    coletados = []
    for nome in ARQUIVOS:
        info = disponiveis[nome]
        caminho = DESTINO / nome
        esperado = info["checksum"].removeprefix("md5:")
        if caminho.exists() and md5(caminho) == esperado:
            print(f"ok (já baixado): {nome}")
        else:
            print(f"baixando {nome} ({info['size'] / 1e6:.1f} MB)...")
            baixar(info["links"]["self"], caminho)
            if md5(caminho) != esperado:
                raise RuntimeError(f"checksum não confere: {nome}")
        coletados.append({"arquivo": nome, "bytes": info["size"], "md5": esperado,
                          "url": info["links"]["self"]})

    metadados = {
        "fonte": meta["title"],
        "autores": [c["name"] for c in meta["creators"]],
        "versao": meta.get("version"),
        "publicado_em": meta["publication_date"],
        "licenca": meta["license"]["id"],
        "doi": registro["doi"],
        "link": f"https://zenodo.org/records/{RECORD_ID}",
        "forma_de_coleta": "API REST do Zenodo (scripts/coleta_zenodo.py)",
        "data_coleta": datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %z"),
        "arquivos": coletados,
    }
    (DESTINO / "metadados_coleta.json").write_text(
        json.dumps(metadados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("metadados gravados em", DESTINO / "metadados_coleta.json")


if __name__ == "__main__":
    main()
