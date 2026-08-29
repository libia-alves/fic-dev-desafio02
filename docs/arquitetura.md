# Arquitetura da aplicação

Diagrama técnico exigido no item 4 dos entregáveis do edital. Renderiza nativamente
no GitHub, GitLab e na extensão Mermaid do VS Code.

## Visão geral do pipeline e das interfaces de consulta

```mermaid
flowchart TD
    subgraph Entrada
        PDFs[("data/pdfs/*.pdf")]
        Categorias[("data/auxiliares/categorias.json")]
        Config[("config.json + .env")]
    end

    subgraph Pipeline["src/pipeline.py — python -m src.main"]
        PDFProc["pdf_processor.py\nextração direta (pypdf)"]
        OCR["ocr_processor.py\nOCR (pdf2image + pytesseract)"]
        Extract["validation.py\nextração por regex"]
        Validate["validation.py\nvalidação + classificação"]
        CEP["cep_client.py\nRF07: consulta ViaCEP"]
        Text["text_processor.py\nlimpeza, tokens, chunks"]
    end

    subgraph Persistencia["Persistência"]
        DB[("SQLite\ndatabase/atendimentos.db\nDocumento / Atendimento / Chunk / ErroProcessamento")]
    end

    subgraph Analise["src/analytics.py"]
        Indicadores["indicadores.json"]
        CSV["atendimentos_processados.csv"]
        Graficos["output/graficos/*.png"]
    end

    subgraph Indexacao["src/indexer.py"]
        Embed["embeddings.py\nsentence-transformers"]
        Chroma[("ChromaDB\ndatabase/chroma/")]
    end

    subgraph Consulta["Consulta (RF13-16)"]
        RAG["rag.py\nmodo local ou LLM (LangChain)"]
        API["api.py — FastAPI\nGET /health · POST /ask"]
        UI["app_streamlit.py"]
        CLI["main.py --pergunta"]
    end

    PDFs --> PDFProc
    PDFProc -- "texto insuficiente" --> OCR
    PDFProc --> Extract
    OCR --> Extract
    Extract --> Validate
    Categorias --> Validate
    Validate --> CEP
    CEP --> DB
    Validate --> DB
    Validate --> Text
    Text --> DB
    DB --> Analise
    Config -.-> Pipeline

    DB -- "chunks (--indexar)" --> Embed --> Chroma
    Chroma --> RAG
    RAG --> API --> UI
    RAG --> CLI
```

## Camadas e responsabilidades

| Camada | Módulos | Responsabilidade |
|---|---|---|
| Configuração | `config.py` | Carrega `config.json` e segredos de `.env` |
| Extração | `pdf_processor.py`, `ocr_processor.py` | Texto selecionável direto ou via OCR, por página |
| Domínio/validação | `validation.py` | Regex, normalização, classificação em válido/incompleto/inválido/duplicado |
| Enriquecimento | `cep_client.py` | Município/UF via API pública, tolerante a falha |
| Texto/RAG prep | `text_processor.py` | Limpeza, tokenização leve, divisão em chunks com metadados |
| Persistência | `models.py`, `database.py` | SQLAlchemy — 4 tabelas, sessão/transação por documento |
| Indicadores | `analytics.py` | Pandas/NumPy — indicadores, CSV, gráficos |
| Busca semântica | `embeddings.py`, `vector_store.py`, `indexer.py` | Embeddings locais + ChromaDB persistente |
| RAG | `rag.py` | Recuperação + síntese opcional via LangChain/OpenAI, com modo local |
| Interfaces | `api.py`, `app_streamlit.py`, `main.py` | FastAPI, Streamlit, CLI |

## Fluxo de uma pergunta em linguagem natural

```mermaid
sequenceDiagram
    participant U as Usuário
    participant ST as Streamlit
    participant API as FastAPI (/ask)
    participant IDX as indexer.semantic_query
    participant CH as ChromaDB
    participant R as rag.answer

    U->>ST: digita pergunta
    ST->>API: POST /ask {pergunta, top_k}
    API->>IDX: semantic_query(pergunta, top_k)
    IDX->>CH: query(embedding, top_k)
    CH-->>IDX: chunks + similaridade
    IDX-->>API: fontes (protocolo, documento, página, score)
    API->>R: answer(pergunta, fontes)
    alt OPENAI_API_KEY configurada
        R->>R: LangChain + ChatOpenAI
    else sem chave / falha
        R->>R: modo local (só recuperação)
    end
    R-->>API: resposta + fontes
    API-->>ST: JSON
    ST-->>U: resposta + fontes exibidas
```
