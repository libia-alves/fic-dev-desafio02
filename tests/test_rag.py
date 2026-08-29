from src.rag import local_answer, answer


def test_bug006_no_sources_says_documents_do_not_support_answer():
    """Regressão do BUG-006 (RF13): sem fontes, a resposta deve avisar
    explicitamente que os documentos não sustentam uma resposta."""
    result = local_answer("pergunta sem correspondencia", [])
    assert result["sustentada_pelos_documentos"] is False
    assert "não" in result["resposta"].lower()


def test_with_sources_marks_answer_as_supported():
    sources = [{"protocolo": "AT-001", "pagina": 1, "conteudo": "texto"}]
    result = local_answer("pergunta", sources)
    assert result["sustentada_pelos_documentos"] is True
    assert result["fontes"] == sources


def test_answer_without_sources_never_calls_llm(monkeypatch):
    called = {"value": False}
    def fake_build(model):
        called["value"] = True
        return None
    monkeypatch.setattr("src.rag._build_chat_model", fake_build)
    result = answer("pergunta sem contexto", [])
    assert called["value"] is False
    assert result["modo"] == "recuperacao_local"
