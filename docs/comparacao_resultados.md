# Aplicação dos dados oficiais: antes x depois das correções

Seção 5.3 do edital. Os 4 PDFs oficiais (`data/pdfs/`) foram processados duas vezes:
uma com o código como recebido, outra após as correções do
`docs/catalogo_defeitos.md`. Arquivos completos em `docs/evidencias/antes/` e
`docs/evidencias/depois/`.

## Resultados esperados (a partir da especificação, RF04/RF07/RF08)

- Todo registro deve receber exatamente uma classificação entre `valido`,
  `incompleto`, `invalido` e `duplicado`, com os motivos explicitados.
- Um registro com campo obrigatório ausente (mesmo representado por um marcador
  como `[vazio]` no formulário de origem) deve cair em `incompleto`.
- Município/UF devem ser preenchidos sempre que o CEP for válido e resolver na
  API pública.
- `indicadores.json` deve conter todos os indicadores listados na seção 8 do
  edital: totais de documentos/páginas, total e percentual por classificação,
  por categoria/status/município/UF, tempo médio/mediano/desvio-padrão,
  categoria de maior volume e de maior tempo médio, percentual de páginas por
  OCR, erros por tipo e por etapa.

## Resultados obtidos antes das correções

| Indicador | Valor |
|---|---|
| Total de registros | 75 |
| Válido / Inválido / Duplicado / **Incompleto** | 51 / 13 / 11 / **0** |
| Município / UF | ausentes (sempre `None`) |
| Indicadores presentes em `indicadores.json` | 8 de ~15 esperados |
| Erros por tipo/etapa | não calculados (existiam no banco, não no relatório) |

**Divergências identificadas:** nenhum registro `incompleto` mesmo com o PDF
contendo casos claramente projetados para isso (BUG-001); município/UF sempre
vazios apesar do CEP estar presente no PDF e o cliente de API já existir no
código (BUG-002); indicadores obrigatórios da seção 8 incompletos (BUG-003).

## Resultados obtidos depois das correções

| Indicador | Valor |
|---|---|
| Total de registros | 75 (inalterado — nenhuma correção adiciona/remove registro, só reclassifica) |
| Válido / Inválido / Duplicado / Incompleto | 50 / 12 / 11 / **2** |
| Município / UF | `Cáceres`: 8, `Cuiabá`: 8 — UF `MT`: 16 |
| Indicadores presentes em `indicadores.json` | 17 (todos os exigidos pela seção 8) |
| Erros por tipo/etapa | `CepIndisponivel`: 6, `PDFInfoNotInstalledError`: 7 (OCR), `Duplicidade`: 11 |

**O que mudou e por quê:** os 2 registros que passaram a `incompleto` (AT-081 e
AT-088) tinham `Solicitante` ou eram afetados pelo marcador `[vazio]`; um saiu de
`valido` e o outro de `invalido` (a lista de motivos de cada um passou a incluir
`solicitante_ausente`, que tem prioridade sobre `invalido` na regra de
classificação já existente no código). `tempo_desvio_padrao` mudou de
`22.77` para `22.94` porque a correção também trocou o cálculo de desvio-padrão
populacional (`ddof=0`) para amostral (`ddof=1`), mais adequado para um conjunto
de dados que representa uma amostra do fluxo de atendimentos.

## Divergências ainda não resolvidas e seus impactos

| Divergência | Impacto | Por quê não foi corrigida agora |
|---|---|---|
| `percentual_ocr` = 0% mesmo com 7 páginas roteadas para OCR | O indicador reflete OCR **bem-sucedido**, não OCR **tentado**; sem Poppler instalado, essas duas métricas coincidem sempre em 0% neste ambiente | Depende de instalar o Poppler no ambiente de execução (item de infraestrutura, não de código — ver BUG-004/005); o cálculo em si está semanticamente correto |
| Apenas 16 de ~66 CEPs válidos resolveram município/UF | Indicador "por município/UF" fica sub-representado | Os dados são fictícios (`"Dados totalmente ficticios"`); muitos CEPs não existem na base real do ViaCEP. Comportamento esperado do cliente tolerante a falha, não um bug |
| `rag.local_answer()` não distingue "sem fontes" de "fontes encontradas" | Pode violar a letra do RF13 em casos de busca sem resultado | Correção de escopo maior (afeta `rag.py`, `api.py`, `app_streamlit.py`); registrada como melhoria P2 em `docs/criticas_melhorias.md` em vez de aplicada às pressas |
| `Documento.nome_arquivo unique=True` frágil (BUG-008) | Risco latente, não observado com os 4 arquivos oficiais atuais (nomes distintos) | Não reproduzido com os dados fornecidos; registrada como melhoria P3 |
