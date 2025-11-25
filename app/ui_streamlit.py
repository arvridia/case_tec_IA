import json
from typing import Optional

import requests
import streamlit as st

from config import API_BASE_URL 



def check_health() -> bool:
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def call_validate_process(raw_json: str) -> dict:
    """
    Envia o JSON de processo para a API /validate_process.
    Retorna um dict com chaves: ok (bool), data (dict|None), error (str|None)
    """
    # tenta parsear JSON
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "data": None,
            "error": f"JSON inválido: {e}",
        }

    try:
        resp = requests.post(
            f"{API_BASE_URL}/validate_process",
            json=payload,
            timeout=200,
        )
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"Erro ao chamar API: {e}",
        }

    if resp.status_code != 200:
        msg = f"Erro na API ({resp.status_code}): {resp.text}"
        return {
            "ok": False,
            "data": None,
            "error": msg,
        }

    try:
        data = resp.json()
    except Exception as e:
        return {
            "ok": False,
            "data": None,
            "error": f"Erro ao interpretar resposta da API: {e}",
        }

    return {"ok": True, "data": data, "error": None}



def render_header():
    st.set_page_config(
        page_title="JusCash – Validação de Processos",
        page_icon="⚖️",
        layout="wide",
    )

    # pro set_page_config funcionar em recarga
    st.markdown(
        """
        <style>
        /* Esconde o menu padrão do Streamlit (opcional) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Container principal mais “card” */
        .main > div {
            padding-top: 1rem;
        }

        /* Badge de decisão */
        .decision-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .decision-approved {
            background: #e6ffed;
            color: #046c4e;
            border: 1px solid #46b37b;
        }
        .decision-rejected {
            background: #ffe6e6;
            color: #9b1c1c;
            border: 1px solid #f56565;
        }
        .decision-incomplete {
            background: #fff8e1;
            color: #975a16;
            border: 1px solid #ecc94b;
        }

        /* Chips de citações */
        .chip {
            display: inline-block;
            padding: 0.1rem 0.5rem;
            margin: 0 0.3rem 0.3rem 0;
            border-radius: 999px;
            background: #dc8125;
            font-size: 0.8rem;
            font-weight: 500;
        }

        /* Caixa de resultado */
        .result-card {
            padding: 1rem 1.2rem;
            border-radius: 0.75rem;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.08);
        }

        .result-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }

        .small-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #718096;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
          <div>
            <h1 style="margin-bottom:0.2rem;">⚖️ JusCash – Validador de Processos</h1>
            <p style="margin-top:0; color:#4A5568; font-size:0.95rem;">
              Interface para inspecionar e validar processos judiciais para compra de créditos,
              utilizando políticas internas e modelo de IA.
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    st.sidebar.markdown("### ⚙️ Configuração & Status")

    api_ok = check_health()
    if api_ok:
        st.sidebar.success("API online")
    else:
        st.sidebar.error("API offline")

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ℹ️ Como usar")
    st.sidebar.markdown(
        """
        1. Cole um JSON de processo no painel à direita.  
        2. Clique em **Validar processo**.  
        3. Veja a decisão da IA, justificativa e regras utilizadas.
        """
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🧠 Modelo & versão")
    st.sidebar.markdown(
        """
        - Backend: FastAPI  
        - Motor de decisão: LLM (HuggingFace) + políticas internas  
        - Entrada/Saída: JSON
        """
    )


def render_decision_badge(decision: Optional[str]):
    if not decision:
        return

    decision = decision.lower()
    label = decision.capitalize()
    css_class = "decision-incomplete"
    if decision == "approved":
        css_class = "decision-approved"
        label = "Approved"
    elif decision == "rejected":
        css_class = "decision-rejected"
        label = "Rejected"
    elif decision == "incomplete":
        css_class = "decision-incomplete"
        label = "Incomplete"

    st.markdown(
        f'<span class="decision-badge {css_class}">{label}</span>',
        unsafe_allow_html=True,
    )


def render_result_card(result: dict):
    """
    Renderiza o resultado retornado pela API de forma visualmente agradável.
    Espera um dict no formato do DecisionResult.
    """
    decision = result.get("decision")
    rationale = result.get("rationale")
    citacoes = result.get("citacoes", []) or []
    model_name = result.get("model_name")
    prompt_version = result.get("prompt_version")
    policy_kb_version = result.get("policy_kb_version")

    st.markdown('<div class="result-card">', unsafe_allow_html=True)

    # linha 1 – decisão + badge
    cols = st.columns([0.4, 0.6])
    with cols[0]:
        st.markdown('<div class="result-title">Decisão do modelo</div>', unsafe_allow_html=True)
        render_decision_badge(decision)
    with cols[1]:
        st.markdown('<div class="small-label">Resumo da decisão</div>', unsafe_allow_html=True)
        st.write(rationale or "Sem justificativa retornada.")

    # linha 2 – citações de políticas
    st.markdown("---")
    st.markdown('<div class="small-label">Regras aplicadas (citadas)</div>', unsafe_allow_html=True)
    if citacoes:
        chips_html = "".join(f'<span class="chip">{c}</span>' for c in citacoes)
        st.markdown(chips_html, unsafe_allow_html=True)
    else:
        st.write("Nenhuma regra específica citada pelo modelo.")

    # linha 3 – metadados técnicos
    st.markdown("---")
    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.markdown('<div class="small-label">Modelo</div>', unsafe_allow_html=True)
        st.write(model_name or "-")
    with meta_cols[1]:
        st.markdown('<div class="small-label">Versão do prompt</div>', unsafe_allow_html=True)
        st.write(prompt_version or "-")
    with meta_cols[2]:
        st.markdown('<div class="small-label">Versão da política</div>', unsafe_allow_html=True)
        st.write(policy_kb_version or "-")

    st.markdown("</div>", unsafe_allow_html=True)


def render_input_section():
    st.markdown("### 📝 JSON do processo")

    default_json = """{
  "numeroProcesso": "0000000-00.0000.0.00.0000",
  "classe": "Ação de Indenização",
  "orgaoJulgador": "1ª Vara Cível",
  "ultimaDistribuicao": "2024-11-18T23:15:44.130Z",
  "assunto": "Danos morais",
  "segredoJustica": false,
  "justicaGratuita": true,
  "siglaTribunal": "TJSP",
  "esfera": "Cível",
  "valorCondenacao": 15000.0,
  "documentos": [],
  "movimentos": []
}"""

    raw_json = st.text_area(
        label="Cole aqui o JSON do processo",
        value=default_json,
        height=320,
        placeholder="Cole o JSON do processo retornado pelo sistema de origem...",
    )

    col_btn, col_info = st.columns([0.3, 0.7])
    with col_btn:
        clicked = st.button("✅ Validar processo", type="primary", use_container_width=True)
    with col_info:
        st.caption("A API irá validar o processo com base nas políticas internas e no modelo de IA.")

    return raw_json, clicked


def main():
    render_header()
    render_sidebar()

    # layout principal
    col_input, col_output = st.columns([0.55, 0.45])

    with col_input:
        raw_json, clicked = render_input_section()

    with col_output:
        st.markdown("### 📊 Resultado da validação")
        if clicked:
            with st.spinner("Consultando motor de decisão..."):
                resp = call_validate_process(raw_json)

            if not resp["ok"]:
                st.error(resp["error"])
            else:
                render_result_card(resp["data"])
        else:
            st.info(
                "Cole um JSON de processo à esquerda e clique em **Validar processo** "
                "para ver a decisão aqui."
            )


if __name__ == "__main__":
    main()
