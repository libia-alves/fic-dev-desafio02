"""Recuperação local e resposta RAG opcional com OpenAI/LangChain."""
from __future__ import annotations
from dotenv import load_dotenv

import os

load_dotenv()

SYSTEM="Responda somente com base no contexto. Se a resposta não estiver sustentada, diga que não há informação suficiente. Cite os protocolos utilizados."

def local_answer(question:str,sources:list[dict]) -> dict:
    # BUG-006 (corrigido): quando nao ha nenhum chunk relevante, o RF13 exige
    # informar explicitamente que os documentos nao sustentam uma resposta, em
    # vez de reaproveitar a mesma mensagem usada quando ha fontes.
    if not sources:
        return {"resposta":"Os documentos indexados não contêm informação suficiente para responder a essa pergunta.","modo":"recuperacao_local","pergunta":question,"fontes":[],"sustentada_pelos_documentos":False}
    return {"resposta":"Modo local: foram recuperados os trechos mais semelhantes. Configure OPENAI_API_KEY (ou GOOGLE_API_KEY) para gerar uma síntese.","modo":"recuperacao_local","pergunta":question,"fontes":sources,"sustentada_pelos_documentos":True}

def _build_chat_model(model:str|None):
    """Seleciona o provedor de LLM. RF14 pede OpenAI; Gemini foi adicionado como
    alternativa configuravel (LLM_PROVIDER=gemini ou GOOGLE_API_KEY presente),
    porque a chave disponivel para testes da equipe e do Gemini. OpenAI continua
    sendo o padrao quando nenhum provedor e forcado explicitamente."""
    provider=os.getenv("LLM_PROVIDER","openai" if os.getenv("OPENAI_API_KEY") else ("gemini" if os.getenv("GOOGLE_API_KEY") else "")).lower()
    if provider=="gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model or os.getenv("GEMINI_MODEL","gemini-3.6-flash"),google_api_key=os.getenv("GOOGLE_API_KEY"),temperature=0)
    if provider=="openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model or os.getenv("OPENAI_MODEL","gpt-4.1-mini"),temperature=0)
    return None

def answer(question:str,sources:list[dict],model:str|None=None) -> dict:
    if not sources: return local_answer(question,sources)
    chat=None
    try:
        chat=_build_chat_model(model)
    except Exception:
        chat=None
    if chat is None: return local_answer(question,sources)
    try:
        from langchain_core.prompts import ChatPromptTemplate
        prompt=ChatPromptTemplate.from_messages([("system",SYSTEM),("human","Pergunta: {question}\n\nContexto:\n{context}")])
        chain=prompt|chat
        context="\n\n".join(f"[Fonte {s.get('protocolo')} p.{s.get('pagina')}] {s.get('conteudo')}" for s in sources)
        response=chain.invoke({"question":question,"context":context})
        return {"resposta":response.content,"modo":"rag","fontes":sources}
    except Exception as exc:
        result=local_answer(question,sources); result["aviso"]=f"Falha no modelo: {type(exc).__name__}"; return result