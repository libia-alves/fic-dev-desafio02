"""Indicadores, exportações e gráficos."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def build_indicators(
    df: pd.DataFrame,
    total_documentos: int | None = None,
    total_paginas: int | None = None,
    erros_por_tipo: dict | None = None,
    erros_por_etapa: dict | None = None,
) -> dict:
    times=pd.to_numeric(df.get("tempo_minutos"),errors="coerce").dropna().to_numpy(dtype=float)
    total_registros=len(df)
    por_classificacao=df.get("classificacao",pd.Series(dtype=str)).value_counts(dropna=False).to_dict()
    por_categoria=df.get("categoria",pd.Series(dtype=str)).value_counts(dropna=False).to_dict()

    # BUG-003 (corrigido): indicadores obrigatórios (seção 8 do edital) que
    # não eram calculados: total de documentos/páginas, percentual por
    # classificação, categoria com maior volume/tempo médio, erros por
    # tipo/etapa e atendimentos por município/UF.
    percentual_classificacao={k:round(100*v/total_registros,2) for k,v in por_classificacao.items()} if total_registros else {}
    categoria_maior_volume=max(por_categoria,key=por_categoria.get) if por_categoria else None
    tempo_por_categoria={}
    categoria_maior_tempo_medio=None
    if total_registros and "categoria" in df.columns:
        agrupado=df.assign(tempo=pd.to_numeric(df.get("tempo_minutos"),errors="coerce")).dropna(subset=["categoria"]).groupby("categoria")["tempo"].mean().dropna()
        tempo_por_categoria={k:round(v,2) for k,v in agrupado.to_dict().items()}
        if tempo_por_categoria: categoria_maior_tempo_medio=max(tempo_por_categoria,key=tempo_por_categoria.get)

    return {
      "total_documentos":total_documentos,
      "total_paginas":total_paginas,
      "total_registros":int(total_registros),
      "por_classificacao":por_classificacao,
      "percentual_por_classificacao":percentual_classificacao,
      "por_categoria":por_categoria,
      "por_status":df.get("status",pd.Series(dtype=str)).value_counts(dropna=False).to_dict(),
      "por_municipio":df.get("municipio",pd.Series(dtype=str)).dropna().value_counts().to_dict() if "municipio" in df.columns else {},
      "por_uf":df.get("uf",pd.Series(dtype=str)).dropna().value_counts().to_dict() if "uf" in df.columns else {},
      "tempo_medio":float(np.mean(times)) if times.size else None,
      "tempo_mediano":float(np.median(times)) if times.size else None,
      "tempo_desvio_padrao":float(np.std(times,ddof=1)) if times.size>1 else None,
      "categoria_maior_volume":categoria_maior_volume,
      "categoria_maior_tempo_medio":categoria_maior_tempo_medio,
      "tempo_medio_por_categoria":tempo_por_categoria,
      "percentual_ocr":float((df.get("metodo",pd.Series(dtype=str))=="ocr").mean()*100) if len(df) else 0.0,
      "erros_por_tipo":erros_por_tipo or {},
      "erros_por_etapa":erros_por_etapa or {},
    }

def export_results(
    df: pd.DataFrame,
    output_dir: str | Path,
    csv_name: str,
    json_name: str,
    total_documentos: int | None = None,
    total_paginas: int | None = None,
    erros_por_tipo: dict | None = None,
    erros_por_etapa: dict | None = None,
) -> dict:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    indicators=build_indicators(df,total_documentos,total_paginas,erros_por_tipo,erros_por_etapa)
    df.to_csv(out/csv_name,index=False,encoding="utf-8")
    (out/json_name).write_text(json.dumps(indicators,ensure_ascii=False,indent=2,default=float),encoding="utf-8")
    return indicators

def generate_charts(df: pd.DataFrame, directory: str | Path) -> None:
    path=Path(directory); path.mkdir(parents=True,exist_ok=True)
    plots=[("categoria","Atendimentos por categoria","atendimentos_categoria.png"),("status","Atendimentos por status","atendimentos_status.png")]
    for column,title,name in plots:
        ax=df[column].fillna("Sem informação").value_counts().sort_values().plot.barh(color="#1F4E78",figsize=(9,5))
        ax.set_title(title); ax.set_xlabel("Quantidade"); ax.set_ylabel(""); plt.tight_layout(); plt.savefig(path/name,dpi=160); plt.close()
    temp=df.assign(tempo=pd.to_numeric(df["tempo_minutos"],errors="coerce")).groupby("categoria")["tempo"].mean().dropna().sort_values()
    ax=temp.plot.barh(color="#D6A84B",figsize=(9,5)); ax.set_title("Tempo médio por categoria"); ax.set_xlabel("Minutos"); ax.set_ylabel(""); plt.tight_layout(); plt.savefig(path/"tempo_medio_categoria.png",dpi=160); plt.close()

    if "municipio" in df.columns and df["municipio"].notna().any():
        por_municipio=df["municipio"].dropna().value_counts().sort_values()
        ax=por_municipio.plot.barh(color="#5B8C5A",figsize=(9,5)); ax.set_title("Atendimentos por município"); ax.set_xlabel("Quantidade"); ax.set_ylabel(""); plt.tight_layout(); plt.savefig(path/"atendimentos_municipio.png",dpi=160); plt.close()
