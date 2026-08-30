import numpy as np
from fastapi.testclient import TestClient

from src.api import app
from src.indexer import semantic_query
from src.pipeline import enrich_cep_record


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200 and response.json()["status"] == "ok"


def test_ask_validation():
    response = TestClient(app).post("/ask", json={"pergunta": "x"})
    assert response.status_code == 422


def test_semantic_query_accepts_protocol_filter(monkeypatch):
    captured = {}

    class DummyService:
        def __init__(self, model):
            self.model = model

        def encode(self, texts):
            return np.asarray([[0.0, 1.0] for _ in texts], dtype=float)

    class DummyStore:
        def __init__(self, *args, **kwargs):
            pass

        def query(self, embedding, top_k, where=None):
            captured["where"] = where
            return []

    monkeypatch.setattr("src.indexer.EmbeddingService", DummyService)
    monkeypatch.setattr("src.indexer.ChromaStore", DummyStore)

    cfg = {
        "_root": ".",
        "embeddings": {"modelo": "dummy"},
        "chromadb": {"diretorio": "database/chroma", "colecao": "atendimentos"},
    }
    assert semantic_query(cfg, "problema de python", top_k=3, protocolo="AT-001") == []
    assert captured["where"] == {"protocolo": "AT-001"}


def test_enrich_cep_record_uses_lookup(monkeypatch):
    captured = {}

    def fake_lookup_cep(cep, base_url, timeout=8):
        captured["cep"] = cep
        captured["base_url"] = base_url
        captured["timeout"] = timeout
        return {"municipio": "São Paulo", "uf": "SP", "logradouro": "Av. Paulista"}

    monkeypatch.setattr("src.pipeline.lookup_cep", fake_lookup_cep)

    cfg = {"api": {"cep_base_url": "https://viacep.com.br/ws", "timeout_segundos": 7}}
    result = enrich_cep_record({"cep": "01000-000"}, cfg)

    assert result["municipio"] == "São Paulo"
    assert result["uf"] == "SP"
    assert captured == {
        "cep": "01000-000",
        "base_url": "https://viacep.com.br/ws",
        "timeout": 7,
    }
