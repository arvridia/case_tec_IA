

````markdown
# ⚖️ JusCash – Validador de Processos com IA

Projeto do case técnico para vaga de Analista de Machine Learning com foco em IA.

Sistema que recebe um **JSON de processo judicial** e decide se o crédito é:
- `approved` – apto para compra,
- `rejected` – não deve ser comprado,
- `incomplete` – documentação insuficiente,

com base em **políticas internas (POL-x)** e em um **modelo de linguagem (LLM) HuggingFace**.

---

## 🧱 Arquitetura

- **FastAPI** (`app/api.py`): expõe a API REST:
  - `GET /health` – healthcheck
  - `POST /validate_process` – recebe um `Processo` em JSON e retorna um `DecisionResult` em JSON.
- **Motor de decisão** (`app/decision_service.py`):
  - Carrega todas as políticas internas (`policy_store`).
  - Monta o prompt com políticas + resumo do processo.
  - Chama o LLM (HuggingFace) para classificar (`approved/rejected/incomplete`), justificar e citar `POL-x`.
- **UI em Streamlit** (`app/ui_streamlit.py`):
  - Editor para colar o JSON do processo.
  - Chama a API `/validate_process`.
  - Exibe decisão, justificativa, regras citadas e metadados (modelo, versão de prompt/política).

---

## ▶️ Como rodar localmente (sem Docker)

```bash
# criar/ativar venv (exemplo Windows)
python -m venv .venv
.\.venv\Scripts\activate

# instalar dependências
pip install -r requirements.txt

# subir API
uvicorn app.api:app --reload --host 0.0.0.0 --port 8000
````

Em outro terminal (com a venv ativa):

```bash
streamlit run app/ui_streamlit.py
```

* API: [http://localhost:8000/docs](http://localhost:8000/docs)
* UI: [http://localhost:8501](http://localhost:8501)

---

## 🐳 Como rodar com Docker

```bash
docker build -t juscash-case .
docker run -p 8000:8000 -p 8501:8501 juscash-case
```

* API: [http://localhost:8000/docs](http://localhost:8000/docs)
* UI: [http://localhost:8501](http://localhost:8501)

---

## 📬 Exemplo de requisição /validate_process

```bash
curl -X POST "http://localhost:8000/validate_process" ^
  -H "Content-Type: application/json" ^
  -d "{
    \"numeroProcesso\": \"0000000-00.0000.0.00.0000\",
    \"classe\": \"Ação de Indenização\",
    \"orgaoJulgador\": \"1ª Vara Cível\",
    \"ultimaDistribuicao\": \"2024-11-18T23:15:44.130Z\",
    \"assunto\": \"Danos morais\",
    \"segredoJustica\": false,
    \"justicaGratuita\": true,
    \"siglaTribunal\": \"TJSP\",
    \"esfera\": \"Cível\",
    \"valorCondenacao\": 15000.0,
    \"documentos\": [],
    \"movimentos\": []
  }"
```

Resposta (exemplo):

```json
{
  "decision": "approved",
  "rationale": "O valor da condenação é superior a R$ 1.000,00 e não há restrições adicionais nas políticas.",
  "citacoes": ["POL-2", "POL-3"],
  "model_name": "google/gemma-2b-it",
  "prompt_version": "v1.0.0",
  "policy_kb_version": "2025-01"
}
```

---

## 🔍 Observabilidade (LangSmith)

Opcional para o case, mas incluído:

* Uso de LangSmith com variáveis `LANGSMITH_TRACING`, `LANGSMITH_API_KEY` etc. para:

  * registrar prompts,
  * acompanhar respostas do modelo,
  * monitorar latência.

---

## ✅ Cobertura de cenários

O sistema foi testado com exemplos representativos:

* Processo cível com valor > R$ 1.000,00 → `approved`.
* Processo sem certidão de trânsito em julgado → `incomplete` (POL-8).
* Processo trabalhista → `rejected` (POL-4).

