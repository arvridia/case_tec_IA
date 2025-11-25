from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_huggingface import HuggingFacePipeline
import torch

from .config import LOCAL_LLM_MODEL


def build_local_llm(model_name: str | None = None) -> HuggingFacePipeline:
    """
    Cria um LLM local usando HuggingFace + LangChain em text-generation.

    google/gemma-2b-it
    """
    model_name = model_name or LOCAL_LLM_MODEL

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    gen_pipeline = pipeline(
        task="text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,   # suficiente
        do_sample=False,
        return_full_text=False,
    )

    llm = HuggingFacePipeline(pipeline=gen_pipeline)
    return llm
