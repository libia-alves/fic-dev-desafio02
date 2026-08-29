import pandas as pd
from src.analytics import build_indicators


def _df():
    return pd.DataFrame([
        {"classificacao": "valido", "categoria": "Senha", "status": "Concluido", "tempo_minutos": 10, "metodo": "extracao_direta", "municipio": "Cuiaba", "uf": "MT"},
        {"classificacao": "valido", "categoria": "Senha", "status": "Pendente", "tempo_minutos": 30, "metodo": "extracao_direta", "municipio": "Cuiaba", "uf": "MT"},
        {"classificacao": "incompleto", "categoria": "Bibliotecas", "status": "Pendente", "tempo_minutos": None, "metodo": "ocr", "municipio": None, "uf": None},
    ])


def test_bug003_missing_indicators_are_now_computed():
    """Regressão do BUG-003: seção 8 do edital exige indicadores que o
    build_indicators original não calculava."""
    indicators = build_indicators(
        _df(), total_documentos=2, total_paginas=5,
        erros_por_tipo={"CepIndisponivel": 1}, erros_por_etapa={"consulta_cep": 1},
    )
    assert indicators["total_documentos"] == 2
    assert indicators["total_paginas"] == 5
    assert indicators["percentual_por_classificacao"]["valido"] == 66.67
    assert indicators["categoria_maior_volume"] == "Senha"
    assert indicators["categoria_maior_tempo_medio"] == "Senha"
    assert indicators["por_municipio"] == {"Cuiaba": 2}
    assert indicators["erros_por_tipo"] == {"CepIndisponivel": 1}
    assert indicators["erros_por_etapa"] == {"consulta_cep": 1}


def test_tempo_desvio_padrao_uses_sample_std():
    df = pd.DataFrame([
        {"classificacao": "valido", "categoria": "Senha", "status": "Concluido", "tempo_minutos": 10},
        {"classificacao": "valido", "categoria": "Senha", "status": "Concluido", "tempo_minutos": 20},
    ])
    indicators = build_indicators(df)
    assert indicators["tempo_desvio_padrao"] == pd.Series([10, 20]).std()
