import json
import shutil
from pathlib import Path

from src.pipeline import process_all


def test_process_all_runs_end_to_end_on_real_pdf(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    root = tmp_path / "project"

    (root / "data" / "auxiliares").mkdir(parents=True)
    (root / "data" / "pdfs").mkdir(parents=True)
    shutil.copytree(
        project_root / "data" / "auxiliares",
        root / "data" / "auxiliares",
        dirs_exist_ok=True,
    )
    shutil.copy2(
        project_root / "data" / "pdfs" / "atendimentos_digitais.pdf",
        root / "data" / "pdfs" / "atendimentos_digitais.pdf",
    )
    shutil.copy2(project_root / "config.json", root / "config.json")

    cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
    cfg["_root"] = str(root)

    monkeypatch.setattr(
        "src.pipeline.lookup_cep",
        lambda cep, base_url, timeout=8: {"municipio": "Brasília", "uf": "DF"},
    )

    df = process_all(cfg)

    assert not df.empty
    assert {"protocolo", "categoria", "documento", "municipio", "uf"}.issubset(
        df.columns
    )
    assert df["municipio"].dropna().str.contains("Brasília", case=False).any()
    assert (root / "output" / "atendimentos_processados.csv").exists()
    assert (root / "output" / "indicadores.json").exists()
