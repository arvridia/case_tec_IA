# app/config.py

import os
from huggingface_hub import login

# URL da API usada pelo Streamlit
API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

# Replace 'your_token_here' with your actual token
login(token="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")

# Modelos locais HuggingFace
LOCAL_LLM_MODEL: str = os.getenv("LOCAL_LLM_MODEL", "google/gemma-2b-it")
EMBEDDING_MODEL_NAME: str = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)

# Versionamento (pra auditoria / doc)
PROMPT_VERSION: str = "v1.0.0"
POLICY_KB_VERSION: str = "2025-01"
