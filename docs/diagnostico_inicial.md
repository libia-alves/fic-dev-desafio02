# Diagnóstico inicial

Registrado **antes** de qualquer correção de código, conforme exigido na seção 5.1
do edital. As evidências brutas (logs e saídas) estão em `docs/evidencias/antes/`.

## Estrutura, tecnologias e dependências

- Python 3.12, `venv` já criada em `venv/`, mas com poucos pacotes instalados.
- `requirements.txt`: pydantic, sqlalchemy, pypdf, pdfplumber, pdf2image,
  pytesseract, pandas, numpy, matplotlib, requests, nltk, sentence-transformers,
  chromadb, fastapi, uvicorn, streamlit, langchain, langchain-openai, pytest, httpx.
- Estrutura de `src/`: `main.py`, `config.py`, `pipeline.py`, `models.py`,
  `database.py`, `pdf_processor.py`, `ocr_processor.py`, `validation.py`,
  `text_processor.py`, `cep_client.py`, `analytics.py`, `embeddings.py`,
  `vector_store.py`, `indexer.py`, `rag.py`, `api.py`, `app_streamlit.py`.
- `data/pdfs/` já continha os 4 PDFs oficiais; `data/auxiliares/` continha
  `categorias.json` e `config_original.json`.
- Git: 1 commit inicial (`a6b49d1`), sem branch de desenvolvimento, sem tag.

## Pontos de entrada e componentes externos

- CLI: `python -m src.main` (flags `--indexar`, `--pergunta`, `--top-k`).
- HTTP: `uvicorn src.api:app` (`GET /health`, `POST /ask`).
- UI: `streamlit run src/app_streamlit.py` (consome a API em `127.0.0.1:8000`, porta
  fixa no código).
- Componentes externos: banco SQLite local; ChromaDB persistente local;
  API pública ViaCEP; Tesseract + Poppler (sistema operacional, não Python);
  Hugging Face Hub (download do modelo de embeddings no primeiro uso, requer
  internet); OpenAI (opcional, via `OPENAI_API_KEY`).

## Execução dos testes existentes

`pytest` **antes de qualquer correção**: 6/6 testes passam
(`test_api.py`, `test_text_processor.py`, `test_validation.py`). Isso **não**
significa que o sistema esteja correto — os testes não cobrem o caminho de
classificação `incompleto` nem o pipeline ponta a ponta (ver BUG-007 no
catálogo de defeitos).

## Tentativa de iniciar pipeline, FastAPI e Streamlit

1. **Instalação de dependências**: falhou na primeira tentativa com
   `OSError: [WinError 206]` (caminho de arquivo longo do Windows, pacote
   `torch`). Havia evidência de uma tentativa anterior com o mesmo erro
   (`docs/evidencias/pip_install_log_tentativa_anterior.txt`, encontrado na raiz
   do projeto antes desta auditoria). Contornado com
   `subst` (letra de unidade temporária) — ver BUG-004.
2. **Pipeline** (`python -m src.main`): executou até o fim, processou os 4 PDFs,
   **75 registros encontrados**. Todas as 7 páginas de
   `atendimentos_digitalizados.pdf` falharam no OCR
   (`PDFInfoNotInstalledError: Is poppler installed and in PATH?` — Poppler não
   estava instalado). O erro foi tratado corretamente: cada falha foi registrada
   e o processamento continuou para as demais páginas/documentos (RF03 cumprido
   nesse aspecto).
3. **Indexação** (`--indexar`): funcionou, mas baixou o modelo de embeddings da
   Hugging Face na primeira execução (requer internet; não documentado no README
   como pré-requisito). 64 chunks indexados no ChromaDB.
4. **Consulta local** (`--pergunta`): funcionou, retornou trechos relevantes com
   pontuação de similaridade e fontes (protocolo/documento/página), em modo local
   (sem `OPENAI_API_KEY`), conforme RF14.
5. **API** (`uvicorn src.api:app`): subiu sem erro. `GET /health` e `POST /ask`
   responderam corretamente em modo `recuperacao_local`.
6. **Streamlit**: não travou na inspeção de código; não foi testado interativamente
   nesta rodada (depende da API já estar no ar na porta 8000, hardcoded).

## Erros, advertências e comportamentos inesperados observados

- Falha de instalação por caminho longo do Windows (BUG-004).
- 100% de falha de OCR por falta do Poppler, sem orientação de instalação no
  Windows no README (BUG-005).
- Nenhum registro classificado como `incompleto` apesar do PDF
  `atendimentos_incompletos.pdf` conter casos claramente projetados para isso
  (BUG-001).
- Município e UF sempre vazios no CSV/banco, mesmo com CEP presente no PDF
  (BUG-002).
- `indicadores.json` com menos da metade dos indicadores exigidos pela seção 8
  do edital (BUG-003).
- Aviso do Hugging Face Hub sobre symlinks não suportados no Windows sem modo
  desenvolvedor (não bloqueante, apenas ruído no log).

## Conclusão do diagnóstico

O núcleo do pipeline (extração, persistência, indexação, RAG local, API) **funciona
de ponta a ponta**. Os defeitos encontrados são principalmente de **integração
faltante** (API de CEP nunca chamada), **classificação incompleta** (marcador de
campo vazio não reconhecido) e **indicadores obrigatórios não implementados** —
não falhas estruturais de arquitetura. Ver `docs/catalogo_defeitos.md` para o
detalhamento e `docs/comparacao_resultados.md` para o efeito das correções nos
dados oficiais.
