from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from .policy_store import get_policy_chunks, PolicyChunk
from .config import EMBEDDING_MODEL_NAME


def build_policy_vectorstore() -> FAISS:
    """
    Cria um vectorstore FAISS com as políticas (POL-1...POL-8)
    usando embeddings locais da HuggingFace.
    """
    policy_chunks: List[PolicyChunk] = get_policy_chunks()

    texts = [c.text for c in policy_chunks]
    metadatas = [
        {"id": c.id, "title": c.title}
        for c in policy_chunks
    ]

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    vectorstore = FAISS.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
    )
    return vectorstore


def build_policy_retriever():
    """
    Retorna um retriever LangChain para ser usado no DecisionEngine.
    """
    vectorstore = build_policy_vectorstore()
    return vectorstore.as_retriever() #search_kwargs={"k": 3}
