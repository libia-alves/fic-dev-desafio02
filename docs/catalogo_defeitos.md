# Catálogo de defeitos

Levantado durante a auditoria da solução recebida (gerada com apoio de IA), rodando o
pipeline contra os 4 PDFs oficiais em `data/pdfs/`. Todos os itens marcados como
**Corrigido** têm evidência reproduzível em `docs/evidencias/antes/` (estado original)
e `docs/evidencias/depois/` (após a correção) — ver `docs/comparacao_resultados.md`.

---

## BUG-001 — Marcador de campo ausente ("[vazio]") não é reconhecido, registros incompletos são classificados como válidos ou inválidos

| Campo | Conteúdo |
|---|---|
| **Severidade** | Alta |
| **RF afetado** | RF04 (classificação válido/incompleto/inválido/duplicado) |
| **Status** | **Corrigido** |
| **Local** | `src/validation.py`, função `extract_fields` |

**Descrição (comportamento observado):** o PDF oficial `atendimentos_incompletos.pdf`
usa o texto literal `[vazio]` para representar um campo propositalmente ausente (ex.:
`Solicitante\n[vazio]`, `Tempo\n[vazio] min`). O código original só verificava se o
valor extraído era uma string vazia (`""`); como `"[vazio]"` é uma string não vazia,
a checagem de campo obrigatório ausente nunca disparava. Resultado: nenhum dos 75
registros processados era classificado como `incompleto` — a categoria inteira
exigida pelo RF04 nunca era usada.

**Como reproduzir (antes da correção):** processar `data/pdfs/atendimentos_incompletos.pdf`
e observar o registro `AT-081` (protocolo página 2) — extração bruta confirmada via
`pypdf`:
```
AT-081
Data 2026-08-11
Solicitante
[vazio]
E-mail rafael.batista@aluno.exemplo.br
...
```
Antes da correção: classificado como `valido`. Depois: `incompleto`, com
`solicitante_ausente` na lista de motivos.

**Evidência quantitativa:** `docs/evidencias/antes/indicadores.json` não tem a chave
`incompleto` em `por_classificacao`. `docs/evidencias/depois/indicadores.json` mostra
`"incompleto": 2` (registros AT-081 e AT-088).

**Correção aplicada:** `extract_fields` agora normaliza qualquer valor extraído cujo
texto (case-insensitive) seja `"[vazio]"` para string vazia, antes de seguir para
`validate_record`. Teste de regressão: `tests/test_validation.py::test_bug001_*`.

---

## BUG-002 — API de CEP implementada mas nunca chamada; município e UF sempre nulos

| Campo | Conteúdo |
|---|---|
| **Severidade** | Alta |
| **RF afetado** | RF07 (consumo de API HTTP de CEP), RF08 (indicador "por município/UF") |
| **Status** | **Corrigido** |
| **Local** | `src/pipeline.py` (não chamava `src/cep_client.py`) |

**Descrição (comportamento observado):** `src/cep_client.py` contém uma implementação
completa e correta de `lookup_cep()` (tolerante a falha, timeout, trata CEP
inexistente) — mas **nenhum outro módulo do projeto a importa ou chama**. Em
`pipeline.py`, o `Atendimento` era sempre criado com `municipio=None,uf=None`
hardcoded, mesmo quando o PDF trazia essa informação junto ao CEP (ex.:
`CEP / cidade 78550-000 - Sinop/MT`). Como consequência, o indicador obrigatório
"atendimentos por município ou UF" (seção 8 do edital) não podia ser calculado —
nem sequer aparecia no `indicadores.json`.

**Como reproduzir (antes da correção):** `grep -c "lookup_cep\|cep_client" src/pipeline.py`
retornava 0 ocorrências. Todo registro no CSV tinha município/UF vazios.

**Correção aplicada:** `pipeline.py` agora chama `cep_client.lookup_cep()` para todo
CEP com formato válido, com cache em memória (evita repetir a mesma consulta) e
registro de erro em `ErroProcessamento` quando o CEP não resolve — sem interromper
o pipeline (RF07). `Atendimento.municipio/uf` e a linha do CSV passam a ser
preenchidos quando a consulta tem sucesso.

**Evidência quantitativa:** `docs/evidencias/depois/indicadores.json` agora tem
`"por_municipio": {"Cáceres": 8, "Cuiabá": 8}` e `"por_uf": {"MT": 16}`.
Nem todos os CEPs resolvem porque os dados são fictícios (`"erros_por_tipo":
{"CepIndisponivel": 6, ...}`) — comportamento esperado e tolerado.

---

## BUG-003 — Indicadores obrigatórios da seção 8 do edital não eram calculados

| Campo | Conteúdo |
|---|---|
| **Severidade** | Média/Alta |
| **RF afetado** | RF08, seção 8 (indicadores e gráficos obrigatórios) |
| **Status** | **Corrigido** |
| **Local** | `src/analytics.py` (`build_indicators`, `export_results`), `src/pipeline.py` |

**Descrição (comportamento observado):** comparando `indicadores.json` original
contra a lista de indicadores obrigatórios do edital, faltavam:
- total de documentos e páginas processados;
- percentual (não só contagem) por classificação;
- categoria com maior volume e categoria com maior tempo médio;
- erros por tipo e por etapa (apesar da tabela `ErroProcessamento` já existir no banco);
- atendimentos por município ou UF (consequência do BUG-002).

**Correção aplicada:** `pipeline.py` passou a acumular `total_documentos`,
`total_paginas` e `erros_por_tipo`/`erros_por_etapa` durante o processamento (a
partir dos mesmos eventos que já geravam `ErroProcessamento`) e repassá-los para
`build_indicators`, que agora também calcula percentuais, categoria de maior
volume/tempo médio e as contagens por município/UF. Também foi adicionado um
gráfico de atendimentos por município (`output/graficos/atendimentos_municipio.png`).

**Evidência:** comparar `docs/evidencias/antes/indicadores.json` (8 chaves) com
`docs/evidencias/depois/indicadores.json` (17 chaves). Teste de regressão:
`tests/test_analytics.py::test_bug003_*`.

---

## BUG-004 — `pip install -r requirements.txt` falha no Windows (limite de caminho longo)

| Campo | Conteúdo |
|---|---|
| **Severidade** | Alta (bloqueia RF01 — reprodutibilidade) |
| **RF afetado** | RF01, RNF "execução reproduzível a partir do README" |
| **Status** | **Contornado**; não é um defeito de código, é uma limitação de ambiente não documentada |

**Descrição (comportamento observado):** instalar as dependências (`torch`,
usado por `sentence-transformers`) falha com
`OSError: [WinError 206] O nome do arquivo ou a extensão é muito longa`. Causa: o
caminho do projeto dentro do OneDrive já é longo por si só, e alguns arquivos
internos do `torch` (ex.: `torch\include\ATen\native\transformers\cuda\
mem_eff_attention\iterators\predicated_tile_access_iterator_residual_last.h`) somados
a esse caminho ultrapassam o limite de 260 caracteres do Windows. Evidência de que
isso já havia acontecido antes desta auditoria: `pip_install_log.txt` (na raiz do
projeto) já continha o mesmo erro de uma tentativa anterior.

**Por que isso é um defeito da entrega, não só "azar de ambiente":** o README só
documenta pré-requisitos para Ubuntu; não há nenhuma orientação para Windows (nem
sobre este problema, nem sobre Poppler/Tesseract — ver BUG-005). Como a maioria dos
discentes usa Windows, a instalação documentada **não é reproduzível** como o RNF exige.

**Contorno usado nesta auditoria:** mapear uma letra de unidade temporária para a
pasta do projeto com `subst Y: "<caminho completo>"` (não precisa de administrador,
não move nada) e instalar via `Y:\venv\Scripts\python.exe -m pip install -r
Y:\requirements.txt`, o que encurta o caminho o suficiente para não estourar o limite.
Documentado no README na seção de pré-requisitos para Windows.

---

## BUG-005 — README não documenta pré-requisitos de OCR para Windows

| Campo | Conteúdo |
|---|---|
| **Severidade** | Média |
| **RF afetado** | RF03, seção 10 do edital ("pré-requisitos, inclusive instalação do mecanismo de OCR") |
| **Status** | **Corrigido** (documentação) |

**Descrição:** a seção "Preparação" do README só traz `apt install poppler-utils
tesseract-ocr tesseract-ocr-por` (Ubuntu). Sem Poppler instalado e no PATH, toda
página roteada para OCR falha com `PDFInfoNotInstalledError` — confirmado ao
processar `atendimentos_digitalizados.pdf` (7 páginas, 100% de falha nesta máquina).
O erro é tratado corretamente (não derruba o pipeline, RF03 cumprido nesse ponto),
mas o resultado prático é que a extração por OCR nunca funciona por padrão em
ambiente Windows sem essa orientação.

**Correção aplicada:** README atualizado com instruções de instalação do Poppler e
do Tesseract para Windows.

---

## BUG-006 — Resposta em modo local não avisa quando não há fontes (RF13 parcial)

| Campo | Conteúdo |
|---|---|
| **Severidade** | Baixa |
| **RF afetado** | RF13 ("informar quando os documentos não sustentarem uma resposta") |
| **Status** | Não corrigido (documentado como melhoria — ver `docs/criticas_melhorias.md`, P2) |

**Descrição:** `rag.local_answer()` sempre retorna a mesma mensagem ("foram
recuperados os trechos mais semelhantes...") mesmo quando `sources` está vazio
(nenhum chunk relevante encontrado, ex.: filtro de categoria sem correspondência).
O RF13 exige informar explicitamente quando os documentos não sustentam uma
resposta; hoje isso só é implícito pela lista de fontes vazia, não por uma mensagem
clara.

---

## BUG-007 — Cobertura de testes não exercitava o caminho "incompleto" nem o pipeline ponta a ponta

| Campo | Conteúdo |
|---|---|
| **Severidade** | Média (risco de processo, não falha em produção) |
| **RF afetado** | RNF "testes insuficientes" (citado no preâmbulo do desafio) |
| **Status** | **Parcialmente corrigido** — adicionados testes para os bugs encontrados |

**Descrição:** dos 6 testes originais, nenhum cobria a classificação `incompleto`
nem o marcador `[vazio]` — por isso o BUG-001 não foi pego antes da entrega. Também
não existe teste de integração do pipeline completo (`pipeline.process_all`) nem
`tests/test_pdf_processor.py` (previsto na estrutura sugerida pelo edital).

**Correção aplicada nesta auditoria:** adicionados `test_bug001_*` em
`tests/test_validation.py` e `tests/test_analytics.py` (novo arquivo, cobre
BUG-003). `tests/test_pdf_processor.py` e um teste de integração do pipeline
completo **continuam pendentes** — listados em `docs/criticas_melhorias.md`.

---

## BUG-008 — Constraint `unique=True` em `nome_arquivo` é redundante e frágil

| Campo | Conteúdo |
|---|---|
| **Severidade** | Baixa (latente — não se manifesta com os 4 arquivos oficiais atuais) |
| **RF afetado** | RF06 ("permitir recriar ou reutilizar o banco de forma previsível") |
| **Status** | Não corrigido (documentado como melhoria — ver `docs/criticas_melhorias.md`, P3) |

**Descrição:** `models.Documento.nome_arquivo` tem `unique=True`, mas a deduplicação
de documentos já é feita corretamente por `hash_sha256` (conteúdo, não nome) em
`pipeline.py`. Se dois arquivos com **nomes iguais mas conteúdos diferentes** forem
processados (ex.: reenvio de um PDF corrigido com o mesmo nome), a segunda
inserção falha com `IntegrityError` não tratado, interrompendo todo o pipeline —
o que viola o requisito não funcional "a aplicação não poderá encerrar todo o
processamento por causa de um único registro inválido".
