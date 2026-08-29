# Crítica e plano de melhorias

Baseado nos defeitos catalogados em `docs/catalogo_defeitos.md`. Nem todas as
melhorias abaixo foram implementadas — a equipe deve escolher pelo menos 1–2,
conforme pede a seção 7 do edital. As marcadas como "Implementada nesta auditoria"
já estão no código.

| ID | Prioridade | Problema | Justificativa | Benefício | Esforço | Risco | Estratégia |
|---|---|---|---|---|---|---|---|
| M1 | **P0** | BUG-001: campos ausentes representados por marcador de texto não são detectados | Quebra diretamente um requisito funcional (RF04) com dado oficial real, e distorce todos os indicadores derivados da classificação | Classificação correta, indicadores confiáveis | Baixo (1 função) | Baixo | Normalizar marcadores de "vazio" na extração, antes da validação. **Implementada nesta auditoria.** |
| M2 | **P0** | BUG-002: RF07 (API de CEP) implementado e nunca usado | Indicador obrigatório (por município/UF) impossível de calcular; código morto no repositório | Cumpre RF07 e RF08 por completo | Baixo/Médio (uma função de pipeline + cache) | Baixo (cliente já tolerante a falha) | Chamar `cep_client.lookup_cep` a partir de `pipeline.py`, com cache e registro de erro. **Implementada nesta auditoria.** |
| M3 | **P1** | BUG-003: indicadores obrigatórios da seção 8 ausentes | Entregável de indicadores incompleto frente ao edital | Relatório de indicadores completo e auditável | Médio (refatora `analytics.py` e assinatura de `export_results`) | Baixo (mudança aditiva, não remove campos existentes) | Acumular contadores durante o pipeline e agregá-los em `build_indicators`. **Implementada nesta auditoria.** |
| M4 | **P1** | BUG-004/005: instalação não reproduzível no Windows (caminho longo, Poppler/Tesseract não documentados) | Viola o requisito não funcional de reprodutibilidade via README; a maioria da turma usa Windows | Onboarding sem suporte manual | Baixo (documentação) | Nenhum | Documentar pré-requisitos e o contorno com `subst` no README. **Implementada nesta auditoria (documentação).** |
| M5 | **P2** | BUG-006: resposta local não distingue "sem fontes" | Pode violar a letra do RF13 em consultas sem resultado relevante | Resposta mais correta e transparente para o usuário final | Baixo | Baixo | Em `rag.local_answer`, checar `if not sources` e retornar mensagem explícita de "documentos não sustentam resposta". **Implementada nesta auditoria.** |
| M6 | **P2** | BUG-007: cobertura de testes insuficiente (sem teste de `incompleto`, sem teste de integração do pipeline) | O BUG-001 só foi encontrado rodando contra dados reais, não pelos testes existentes | Reduz risco de regressão futura | Médio (testes de integração exigem banco/Chroma temporários) | Baixo | Adicionar `tests/test_pdf_processor.py` e um teste de integração de `pipeline.process_all` com um PDF de fixture pequeno. **Parcialmente implementada**: `test_pdf_processor.py`, `test_rag.py` e `test_models.py` adicionados (18 testes no total, contra 6 originais); um teste de integração ponta a ponta de `pipeline.process_all` continua pendente — é o item #1 da lista "o que falta" abaixo. |
| M7 | **P3** | BUG-008: `nome_arquivo unique=True` frágil | Risco latente de `IntegrityError` não tratado interrompendo o pipeline inteiro | Robustez do RF06 (não travar por causa de um registro) | Baixo | Baixo | Remover `unique=True` de `nome_arquivo` (a deduplicação real já é por `hash_sha256`). **Implementada nesta auditoria.** |
| M8 | **P3** | Porta da API fixa (`127.0.0.1:8000`) hardcoded em `app_streamlit.py` | Dificulta rodar API/UI em portas diferentes (ex.: múltiplos ambientes, CI) | Configuração mais flexível | Baixo | Nenhum | Ler a URL da API de uma variável de ambiente com valor padrão. **Não implementada.** |
| M9 | **P3** | `PROTO_RE = ^AT-\d{3}$` aceita só 3 dígitos | Assunção rígida ao formato atual dos dados de treinamento; qualquer novo lote com mais de 999 protocolos quebra a validação | Validação mais robusta a longo prazo | Baixo | Baixo | Ajustar o regex para uma faixa de dígitos (`\d{3,5}`) ou tornar configurável via `config.json`. **Não implementada** — mantido como está para não divergir do formato oficial atual sem necessidade comprovada. |

## Vulnerabilidade ou risco mais relevante

**M7 (BUG-008)** era o mais preocupante do ponto de vista de disponibilidade: uma
`IntegrityError` não tratada em `session.add(doc); session.flush()` propagaria para
fora do `with session_scope(...)`, e como esse bloco envolve o loop inteiro sobre
todos os PDFs, um único arquivo com nome repetido (mas conteúdo diferente)
interromperia o processamento de **todos** os documentos ainda não processados —
violação direta do requisito não funcional "a aplicação não poderá encerrar todo o
processamento por causa de um único registro inválido". Não havia sido reproduzido
com os 4 arquivos oficiais atuais (nomes únicos), por isso havia ficado como P3 e
não P0/P1 — **mas foi corrigido nesta auditoria** (ver `tests/test_models.py`).

Com M7 resolvido, o risco remanescente mais relevante passa a ser de
**infraestrutura, não de código**: BUG-004 (limite de caminho longo do Windows)
impede a instalação das dependências do zero em qualquer máquina Windows com o
projeto em um caminho suficientemente aninhado (comum em pastas do OneDrive) —
ou seja, viola a reprodutibilidade exigida pelo RNF sem que exista, ainda, um
contorno automático embutido no `requirements.txt`/README além da instrução
manual com `subst`.
