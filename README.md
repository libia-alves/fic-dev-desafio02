# Sistema Inteligente de Processamento e Consulta de Atendimentos de Suporte

Desafio FIC_DEV — Auditoria, correção e implantação de um sistema gerado por IA
(Módulo COD 001). 
Discente: **Libia Canhete Alves e Cruz, Kevin Medeiros e Leandro**

> Esta base de código foi recebida como um projeto "aparentemente completo,
> informado como gerado por Inteligência Artificial, mas ainda não validado"
> (edital, seção 2). Este README documenta o resultado da auditoria: o que foi
> executado, os defeitos encontrados e corrigidos, e o que continua pendente.
> Relatórios completos em `docs/`:
> [`diagnostico_inicial.md`](docs/diagnostico_inicial.md) ·
> [`catalogo_defeitos.md`](docs/catalogo_defeitos.md) ·
> [`comparacao_resultados.md`](docs/comparacao_resultados.md) ·
> [`criticas_melhorias.md`](docs/criticas_melhorias.md) ·
> [`arquitetura.md`](docs/arquitetura.md)

## Funcionalidades

- extração direta de PDFs com `pypdf`;
- encaminhamento de páginas sem texto para Tesseract;
- regex, normalização, validação e deduplicação;
- SQLite e SQLAlchemy;
- limpeza textual, stopwords e lematização leve;
- Pandas, NumPy, CSV, JSON e três gráficos;
- chunks com metadados rastreáveis;
- embeddings locais com `sentence-transformers`;
- coleção persistente no ChromaDB;
- recuperação local e RAG opcional com LangChain/OpenAI;
- FastAPI, Streamlit e testes com Pytest.

## Preparação

### Linux/Ubuntu

```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-por
```

### Windows (não documentado na versão original recebida — BUG-005)

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
```

Instale, além do Python, dois programas externos (não são pacotes `pip`) e
adicione ambos ao `PATH`:

- **Tesseract OCR**: instalador em https://github.com/UB-Mannheim/tesseract/wiki
- **Poppler para Windows**: binários em https://github.com/oschwartz10612/poppler-windows/releases
  (sem isso, toda página roteada para OCR falha com
  `PDFInfoNotInstalledError: Is poppler installed and in PATH?`)

**Se a instalação do `pip` falhar com `OSError: [WinError 206]` (nome de arquivo
ou caminho muito longo)** — comum quando o projeto está em uma pasta bem aninhada
(ex.: dentro do OneDrive) — é o limite de 260 caracteres do Windows sendo
estourado por arquivos internos do `torch`. Duas soluções, sem precisar mover o
projeto nem mexer em configuração do sistema:

```powershell
# Mapeia uma letra de unidade temporária para o caminho atual do projeto
subst Y: "%cd%"
Y:
venv\Scripts\python.exe -m pip install -r requirements.txt
subst Y: /D    # desfaz o mapeamento depois de instalar (não é mais necessário)
```

Alternativa permanente (requer privilégio de administrador): habilitar
"Enable Win32 long paths" — veja https://pip.pypa.io/warnings/enable-long-paths.

## Execução

Pipeline sem indexação vetorial:

```bash
python -m src.main
```

Pipeline e indexação:

```bash
python -m src.main --indexar
```

Consulta por linha de comando:

```bash
python -m src.main --pergunta "Quais problemas mencionam instalação do Python?"
```

API e interface:

```bash
uvicorn src.api:app --reload
streamlit run src/app_streamlit.py
```

Testes:

```bash
pytest
```

## Modo sem chave da OpenAI

Os embeddings são locais. Sem `OPENAI_API_KEY`, o sistema recupera e apresenta os chunks mais semelhantes com suas fontes. Com a chave configurada, LangChain e o modelo definido em `OPENAI_MODEL` produzem uma síntese fundamentada no contexto.

## Decisões de referência

- Registros repetidos pelo protocolo são classificados como duplicados e não são reinseridos.
- O texto original é preservado; a versão limpa serve para recuperação.
- O chunk utiliza 500 caracteres e sobreposição de 80, configuráveis.
- Erros de OCR são persistidos e não interrompem os outros arquivos.
- A API de CEP é chamada a partir do pipeline (`cep_client.lookup_cep`, cache em
  memória, sem interromper o processamento em caso de falha) — corrigido durante
  esta auditoria; ver BUG-002 em `docs/catalogo_defeitos.md`.

## Limitações conhecidas

Intencionais (da versão original):
- A lematização leve evita exigir o download de um modelo grande; uma solução com spaCy também é válida.
- A extração por regex foi ajustada ao formulário fornecido. Layouts diferentes exigem novos padrões.

Encontradas na auditoria e **ainda não corrigidas** (detalhes e severidade em
`docs/catalogo_defeitos.md`):
- `rag.local_answer()` não distingue explicitamente "nenhuma fonte encontrada" de
  "fontes recuperadas" (BUG-006).
- `Documento.nome_arquivo` tem `unique=True`, redundante com a deduplicação real
  por hash de conteúdo, e pode derrubar o pipeline inteiro se dois arquivos
  diferentes tiverem o mesmo nome (BUG-008).
- Cobertura de testes ainda não inclui um teste de integração do pipeline
  completo nem `tests/test_pdf_processor.py` (BUG-007).
- Muitos CEPs dos dados oficiais são fictícios e não resolvem na API pública
  real — comportamento esperado, não um defeito.
- O download do modelo de embeddings (`sentence-transformers`) na primeira
  execução requer acesso à internet (Hugging Face Hub); não há modo 100%
  offline documentado.

## Uso de ferramentas de IA

Esta base de código foi recebida como um projeto já gerado por IA (não
desenvolvido do zero nesta etapa). O trabalho de auditoria realizado usando
Claude (Anthropic), via Claude Code, incluiu:

- **Diagnóstico**: inspeção de todos os módulos de `src/`, execução dos testes
  existentes, execução do pipeline/API/Streamlit contra os 4 PDFs oficiais.
- **Correções aceitas e aplicadas**: BUG-001 (marcador `[vazio]` não reconhecido),
  BUG-002 (API de CEP nunca chamada) e BUG-003 (indicadores da seção 8
  incompletos) — ver `docs/catalogo_defeitos.md` para evidência e reprodução de
  cada um.
- **Sugestões não aplicadas**: correções mais amplas de RF13 (BUG-006) e do
  `unique=True` (BUG-008) foram identificadas mas deixadas como propostas de
  melhoria (`docs/criticas_melhorias.md`), por exigirem mudanças de escopo maior
  do que uma correção pontual.
- **Limitação encontrada na ferramenta**: nenhum erro de código gerado
  incorretamente pela IA durante a correção; o principal obstáculo foi de
  ambiente (limite de caminho longo do Windows ao instalar dependências),
  não relacionado à geração de código.
- **Revisão e teste**: toda correção foi validada rodando o pipeline contra os
  dados oficiais antes/depois (`docs/comparacao_resultados.md`) e com testes de
  regressão automatizados (`tests/test_validation.py`,
  `tests/test_analytics.py`), todos executados via `pytest` antes de serem
  considerados concluídos.

O discente/equipe é responsável por compreender, executar, testar e explicar
todo o código entregue — inclusive o que já veio pronto na base recebida.
