import streamlit as st
from agent.helpdesk_agent import run_agent
from utils.helpers import confidence_label, confidence_color, escalation_badge, format_json_display

st.set_page_config(
    page_title="IT Help Desk Agent",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

.main-header {
    text-align: center;
    padding: 2.5rem 0 1rem 0;
    border-bottom: 1px solid #21262d;
    margin-bottom: 2rem;
}

.main-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: #58a6ff;
    letter-spacing: -0.5px;
    margin: 0;
}

.main-header p {
    color: #8b949e;
    font-size: 0.9rem;
    margin-top: 0.4rem;
    font-weight: 300;
}

.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    color: #58a6ff;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

.card {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
}

.card-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.8rem;
}

.rag-case {
    background: #0d1117;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 4px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.6rem;
}

.rag-case-issue {
    color: #e6edf3;
    font-size: 0.85rem;
    margin-bottom: 0.3rem;
}

.rag-case-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: #8b949e;
}

.score-badge {
    display: inline-block;
    background: #1c2e4a;
    color: #58a6ff;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    padding: 2px 7px;
    border-radius: 3px;
    margin-right: 6px;
}

.res-step {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    margin-bottom: 0.5rem;
    font-size: 0.88rem;
    color: #c9d1d9;
}

.step-num {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #58a6ff;
    background: #1c2e4a;
    border-radius: 3px;
    padding: 1px 6px;
    min-width: 22px;
    text-align: center;
    margin-top: 2px;
}

.cmd-block {
    font-family: 'IBM Plex Mono', monospace;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 4px;
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
    color: #79c0ff;
    margin-bottom: 0.4rem;
}

.measure-item {
    font-size: 0.85rem;
    color: #c9d1d9;
    padding: 0.3rem 0;
    border-bottom: 1px solid #21262d;
}

.metric-box {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
}

.metric-value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.4rem;
    font-weight: 600;
}

.metric-label {
    font-size: 0.72rem;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.2rem;
}

.raw-json {
    font-family: 'IBM Plex Mono', monospace;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 1rem;
    font-size: 0.78rem;
    color: #8b949e;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 300px;
    overflow-y: auto;
}

.stTextArea textarea {
    background-color: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 6px !important;
    color: #e6edf3 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.9rem !important;
}

.stTextArea textarea:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
}

.stButton > button {
    background-color: #238636 !important;
    color: white !important;
    border: 1px solid #2ea043 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 0.5rem 2rem !important;
    width: 100% !important;
    transition: background-color 0.15s !important;
}

.stButton > button:hover {
    background-color: #2ea043 !important;
}

.stSpinner > div {
    border-color: #58a6ff !important;
}

.no-cases {
    color: #8b949e;
    font-size: 0.85rem;
    font-style: italic;
    padding: 0.5rem 0;
}

hr {
    border: none;
    border-top: 1px solid #21262d;
    margin: 1.5rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🖥️ IT Help Desk Agent</h1>
    <p>RAG-powered diagnostics · Groq LLM · Structured resolution</p>
</div>
""", unsafe_allow_html=True)

col_input, col_results = st.columns([1, 1.6], gap="large")

with col_input:
    st.markdown('<div class="section-label">Describe Your Issue</div>', unsafe_allow_html=True)

    issue_text = st.text_area(
        label="issue_input",
        placeholder="e.g. My laptop won't connect to the office WiFi after a Windows update...",
        height=130,
        label_visibility="collapsed",
    )

    st.markdown('<div class="section-label" style="margin-top:0.8rem;">Your System</div>', unsafe_allow_html=True)

    os_col1, os_col2 = st.columns(2)
    with os_col1:
        os_choice = st.selectbox(
            "Operating System",
            ["Windows", "macOS", "Linux"],
            label_visibility="collapsed",
        )
    with os_col2:
        version_placeholders = {
            "Windows": "e.g. 11 23H2, 10 22H2",
            "macOS": "e.g. Sonoma 14.5, Ventura 13.6",
            "Linux": "e.g. Ubuntu 24.04, Fedora 40",
        }
        os_version = st.text_input(
            "Version",
            placeholder=version_placeholders.get(os_choice, ""),
            label_visibility="collapsed",
        )

    diagnose = st.button("⚡ Diagnose Issue", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">System Info</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.8rem; color:#8b949e; line-height:1.8;">
        <span style="color:#58a6ff;">Model</span> · llama-3.1-8b-instant<br>
        <span style="color:#58a6ff;">Embeddings</span> · all-MiniLM-L6-v2<br>
        <span style="color:#58a6ff;">Vector DB</span> · FAISS (cosine sim)<br>
        <span style="color:#58a6ff;">Memory</span> · MongoDB<br>
        <span style="color:#58a6ff;">Top-K Retrieval</span> · 3 cases<br>
        <span style="color:#58a6ff;">Knowledge Base</span> · 30 OS-aware cases
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_results:
    if diagnose:
        if not issue_text.strip():
            st.warning("Please describe your issue before diagnosing.")
        else:
            with st.spinner("Analyzing issue and retrieving similar cases..."):
                try:
                    os_info = {"os": os_choice, "version": os_version}
                    response, similar_cases = run_agent(issue_text.strip(), os_info=os_info)

                    st.markdown('<div class="section-label">Retrieved Cases (RAG Context)</div>', unsafe_allow_html=True)

                    if similar_cases:
                        for case in similar_cases:
                            score = case.get("similarity_score", 0)
                            st.markdown(f"""
                            <div class="rag-case">
                                <div class="rag-case-issue">{case['issue']}</div>
                                <div class="rag-case-meta">
                                    <span class="score-badge">score {score:.2f}</span>
                                    {case.get('issue_class', 'Unknown')}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="no-cases">No similar cases found — cold inference used.</div>', unsafe_allow_html=True)

                    st.markdown("<hr>", unsafe_allow_html=True)
                    st.markdown('<div class="section-label">Diagnosis Result</div>', unsafe_allow_html=True)

                    confidence = response.get("confidence", 0)
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"""
                        <div class="metric-box">
                            <div class="metric-value" style="color:{confidence_color(confidence)};">{confidence:.0%}</div>
                            <div class="metric-label">Confidence</div>
                        </div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class="metric-box">
                            <div class="metric-value" style="color:#58a6ff; font-size:1rem;">{response.get('issue_class','—')}</div>
                            <div class="metric-label">Category</div>
                        </div>""", unsafe_allow_html=True)
                    with c3:
                        esc = response.get("escalation_required", False)
                        st.markdown(f"""
                        <div class="metric-box">
                            <div class="metric-value" style="color:{'#ef4444' if esc else '#22c55e'}; font-size:1.2rem;">{'YES' if esc else 'NO'}</div>
                            <div class="metric-label">Escalate</div>
                        </div>""", unsafe_allow_html=True)

                    st.markdown("<br>", unsafe_allow_html=True)

                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown('<div class="card-title">📋 Diagnosis Summary</div>', unsafe_allow_html=True)
                    st.markdown(f'<div style="font-size:0.88rem; color:#c9d1d9; line-height:1.6;">{response.get("diagnosis_summary", "")}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    steps = response.get("resolution_steps", [])
                    if steps:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<div class="card-title">🔧 Resolution Steps</div>', unsafe_allow_html=True)
                        for i, step in enumerate(steps, 1):
                            st.markdown(f'<div class="res-step"><span class="step-num">{i}</span><span>{step}</span></div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    commands = response.get("commands", [])
                    if commands:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<div class="card-title">💻 Commands to Run</div>', unsafe_allow_html=True)
                        for cmd in commands:
                            st.markdown(f'<div class="cmd-block">$ {cmd}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    measures = response.get("preventive_measures", [])
                    if measures:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown('<div class="card-title">🛡️ Preventive Measures</div>', unsafe_allow_html=True)
                        for m in measures:
                            st.markdown(f'<div class="measure-item">• {m}</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                    with st.expander("View Raw JSON Response"):
                        st.markdown(f'<div class="raw-json">{format_json_display(response)}</div>', unsafe_allow_html=True)

                    if response.get("_saved_to_kb"):
                        st.success("✅ Case saved to knowledge base for future retrieval.")
                    else:
                        st.info("ℹ️ Low confidence — case was not saved to knowledge base.")

                except ValueError as e:
                    st.error(f"Configuration error: {e}")
                except Exception as e:
                    st.error(f"Agent error: {e}")
    else:
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:350px; color:#30363d; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🖥️</div>
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.85rem; color:#484f58;">
                Describe your issue and click Diagnose<br>to get an AI-powered resolution.
            </div>
        </div>
        """, unsafe_allow_html=True)
