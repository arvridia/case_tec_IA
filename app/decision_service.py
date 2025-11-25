# app/decision_service.py
import json
from typing import List

from langchain_core.prompts import PromptTemplate

import re
from json import JSONDecodeError
from .models import Processo, DecisionResult
from .rag import build_policy_retriever
from .llm import build_local_llm
from .config import PROMPT_VERSION, POLICY_KB_VERSION, LOCAL_LLM_MODEL
import os
from langsmith import traceable

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "default"
#MAX_PROMPT_CHARS = 1500

def summarize_processo(processo: Processo) -> str:
    """
    Cria um resumo textual do processo para usar como query no RAG
    e também no prompt do LLM.
    """
    doc_nomes = [d.nome for d in processo.documentos]
    mov_descs = [m.descricao for m in processo.movimentos]  # primeiros 5

    lines = [
        f"Número do processo: {processo.numeroProcesso}",
        f"Classe: {processo.classe}",
        f"Órgão julgador: {processo.orgaoJulgador}",
        f"Esfera: {processo.esfera}",
        f"Sigla tribunal: {processo.siglaTribunal}",
        f"Valor da condenação: {processo.valorCondenacao}",
        f"Segredo de justiça: {processo.segredoJustica}",
        f"Justiça gratuita: {processo.justicaGratuita}",
        "",
        "Nomes dos documentos:",
        *[f"- {n}" for n in doc_nomes],
        "",
        "Primeiros movimentos registrados:",
        *[f"- {d}" for d in mov_descs],
    ]
    return "\n".join(lines)


DECISION_PROMPT = """
Você é um assistente jurídico que analisa processos para compra de créditos.

Use APENAS as regras da política abaixo para decidir.

POLÍTICA (trechos relevantes):
{policy_context}

DADOS DO PROCESSO (resumo):
{process_summary}

TAREFA:
- Decida se o processo é "approved", "rejected" ou "incomplete".
- Explique brevemente o motivo em português.
- Liste quais regras (POL-x) usou.

INSTRUÇÕES IMPORTANTES:
- Responda SOMENTE com UM ÚNICO objeto JSON.
- NÃO escreva nada fora do JSON.
- O JSON DEVE TER exatamente estes campos:
  - "decision": uma string, com valor "approved", "rejected" ou "incomplete".
  - "rationale": string com explicação curta dos motivos que utilizou para tomar a decisão em português.
  - "citacoes": lista de strings com IDs das regras, por exemplo ["POL-1","POL-3"].

Agora gere a resposta PARA ESTE PROCESSO ESPECÍFICO.
NÃO repita instruções.
NÃO mostre exemplo.
"""



class DecisionEngine:
    def __init__(self, llm=None, retriever=None):
        # LLM local (HuggingFace)
        self.llm = llm or build_local_llm()
        # Retriever de políticas (LangChain + FAISS)
        self.retriever = retriever or build_policy_retriever()
        # Template de prompt (LangChain)
        self.prompt = PromptTemplate(
            input_variables=["policy_context", "process_summary"],
            template=DECISION_PROMPT,
        )

    def _build_policy_context(self, process_summary: str) -> str:
        """
        Usa o RAG para buscar as políticas mais relevantes
        e montar um contexto textual para o LLM.
        Funciona tanto com retrievers antigos (get_relevant_documents)
        quanto com retrievers novos (invoke).
        """
        # Compatível com diferentes versões do LangChain
        if hasattr(self.retriever, "get_relevant_documents"):
            docs = self.retriever.get_relevant_documents(process_summary)
        else:
            # Em versões novas, retriever é um Runnable
            docs = self.retriever.invoke(process_summary)

        parts: List[str] = []
        for d in docs:
            pid = d.metadata.get("id", "")
            title = d.metadata.get("title", "")
            header = f"{pid} - {title}".strip()
            parts.append(f"{header}\n{d.page_content}")
        return "\n\n".join(parts)

    @staticmethod
    def _heuristic_from_text(raw_text: str) -> dict:
        """
        Fallback quando o modelo NÃO devolve JSON:
        - deduz a decisão por palavras-chave,
        - extrai POL-x com regex,
        - usa o texto como rationale (cortado).
        """
        text = raw_text.strip()
        text_lower = text.lower()

        # decide
        if "approved" in text_lower or "aprovad" in text_lower:
            decision = "approved"
        elif "incomplete" in text_lower or "incomplet" in text_lower:
            decision = "incomplete"
        elif (
            "rejected" in text_lower
            or "rejeitad" in text_lower
            or "recusad" in text_lower
        ):
            decision = "rejected"
        else:
            # se não achar nada, assume incomplete por segurança
            decision = "incomplete"

        # citacoes POL-x

        citacoes = sorted(set(re.findall(r"POL-\d+", text)))
        if not citacoes:
            citacoes = []

        # rationale: texto completo, mas limitado
        rationale = text
        #if len(rationale) > 400:
        #    rationale = rationale[:400] + "..."

        return {
            "decision": decision,
            "rationale": rationale,
            "citacoes": citacoes,
        }


    @staticmethod
    def _parse_json_output(raw_text: str) -> dict:
        """
        Tenta:
        1) interpretar como JSON (primeiro objeto);
        2) se não houver JSON, usa fallback heurístico.
        """
        # trata saídas claramente inválidas como vazias
        if raw_text in {"```", "``", "`", "**"}:
            raw_text = ""

        if not raw_text:
            return {
                "decision": "incomplete",
                "rationale": "Não foi possível obter uma análise confiável do modelo para este caso. O processo deve ser revisado manualmente.",
                "citacoes": [],
            }


        decoder = json.JSONDecoder()

        # 1) tentar ler JSON desde o início
        try:
            obj, _ = decoder.raw_decode(raw_text)
            return obj
        except JSONDecodeError:
            pass

        # 2) procurar primeiro '{' e tentar a partir dali
        start = raw_text.find("{")
        if start != -1:
            try:
                obj, _ = decoder.raw_decode(raw_text[start:])
                return obj
            except JSONDecodeError:
                pass

        # 3) se não tem '{' nenhum ou não deu pra parsear -> heurística
        return DecisionEngine._heuristic_from_text(raw_text)


    @traceable
    def decide(self, processo: Processo) -> DecisionResult:
        """
        Ponto único de decisão:
        - sumariza o processo,
        - usa RAG para pegar as políticas relevantes,
        - monta o prompt,
        - chama o LLM local via LangChain,
        - parseia o JSON e retorna DecisionResult.
        """
        process_summary = summarize_processo(processo)
        policy_context = self._build_policy_context(process_summary)

        prompt_str = self.prompt.format(
            policy_context=policy_context,
            process_summary=process_summary,
        )
        
        # 🔹 GARANTIR que o Flan-T5 não vai estourar o limite de contexto
        
        #if len(prompt_str) > MAX_PROMPT_CHARS:
        #    prompt_str = prompt_str[:MAX_PROMPT_CHARS]

        raw_output = self.llm.invoke(prompt_str)
        # 👇 debug aqui
        print("\n================ RAW OUTPUT DO MODELO ================")
        print(raw_output)
        print("=====================================================\n")
        data = self._parse_json_output(raw_output)

        return DecisionResult(
            decision=data["decision"],
            rationale=data["rationale"],
            citacoes=data.get("citacoes", []),
            model_name=LOCAL_LLM_MODEL,
            prompt_version=PROMPT_VERSION,
            policy_kb_version=POLICY_KB_VERSION,
        )
