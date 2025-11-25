# app/api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging, time

from .models import Processo, DecisionResult
from .decision_service import DecisionEngine

logger = logging.getLogger("juscash")

app = FastAPI(
    title="JusCash Credit Validator",
    version="0.1.0",
    description="API para validação de processos judiciais com IA (RAG + LLM local).",
)

# CORS simples (para UI em outra porta)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # em prod, restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# instancia única do engine
decision_engine = DecisionEngine()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate_process", response_model=DecisionResult)
def validate_process(processo: Processo):
    """
    Recebe um processo e retorna a decisão de compra de crédito
    (approved | rejected | incomplete), com justificativa e citações da política.
    """
    start = time.time()
    result = decision_engine.decide(processo)
    elapsed = time.time() - start
    logger.info(
        "decision_made",
        extra={
            "numeroProcesso": processo.numeroProcesso,
            "decision": result.decision,
            "citacoes": result.citacoes,
            "model": result.model_name,
            "prompt_version": result.prompt_version,
            "policy_kb_version": result.policy_kb_version,
            "latency_s": round(elapsed, 3),
        },
    )
    return result