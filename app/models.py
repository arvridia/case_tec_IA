from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel


class Documento(BaseModel):
    id: str
    dataHoraJuntada: datetime
    nome: str
    texto: str


class Movimento(BaseModel):
    dataHora: datetime
    descricao: str


class Processo(BaseModel):
    numeroProcesso: str
    classe: str
    orgaoJulgador: str
    ultimaDistribuicao: datetime
    valorCausa: Optional[float] = None
    assunto: Optional[str] = None
    segredoJustica: bool
    justicaGratuita: bool
    siglaTribunal: str
    esfera: str
    valorCondenacao: Optional[float] = None

    documentos: List[Documento]
    movimentos: List[Movimento]


DecisionType = Literal["approved", "rejected", "incomplete"]


class DecisionResult(BaseModel):
    decision: DecisionType
    rationale: str
    citacoes: List[str]

    # metadados opcionais pra auditoria
    model_name: Optional[str] = None
    prompt_version: Optional[str] = None
    policy_kb_version: Optional[str] = None
