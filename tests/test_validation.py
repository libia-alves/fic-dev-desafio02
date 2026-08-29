from src.validation import validate_record, normalize_category, extract_fields

CATS={"categorias_oficiais":[{"nome":"Python e bibliotecas","variacoes":["python","pip"]}]}

def test_valid_record():
    record={"protocolo":"AT-001","data":"01/08/2026","email":"a@b.com","cep":"78200-000","categoria":"pip","tempo_minutos":"20","solicitante":"Ana","descricao":"Erro"}
    classification,reasons,normalized=validate_record(record,CATS)
    assert classification=="valido" and not reasons
    assert normalized["categoria_normalizada"]=="Python e bibliotecas"

def test_invalid_email():
    record={"protocolo":"AT-001","data":"01/08/2026","email":"invalido","cep":"78200-000","categoria":"python","tempo_minutos":"20","solicitante":"Ana","descricao":"Erro"}
    assert "email_invalido" in validate_record(record,CATS)[1]

def test_bug001_blank_marker_is_treated_as_missing_field():
    """Regressão do BUG-001: o PDF oficial usa o literal "[vazio]" para campos
    ausentes (ex.: "Solicitante [vazio]"). extract_fields deve normalizar isso
    para string vazia, e validate_record deve classificar como incompleto."""
    text="Protocolo AT-081 Data 2026-08-11 Solicitante [vazio] E-mail a@b.com Categoria pip Status Concluido CEP / cidade 78550-000 Tempo 26 min Problema Erro real Solucao Resolvido"
    fields=extract_fields(text)
    assert fields["solicitante"]==""
    classification,reasons,_=validate_record(fields,CATS)
    assert classification=="incompleto"
    assert "solicitante_ausente" in reasons

def test_bug001_blank_marker_case_insensitive():
    assert extract_fields("Solicitante [VAZIO] E-mail a@b.com")["solicitante"]==""
