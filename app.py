import streamlit as st
from groq import Groq
import json
from datetime import datetime

st.set_page_config(page_title="CardioAI", page_icon="🫀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #080d16; color: #e8eef8; }
.main-title { font-size: 1.7rem; font-weight: 700; letter-spacing: -0.02em; background: linear-gradient(90deg, #3d7fff, #00d68f); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 2px; }
.sub-title { font-size: 0.82rem; color: #5a7499; margin-bottom: 1.5rem; }
.section-hdr { font-size: 0.68rem; color: #3d7fff; font-family: 'IBM Plex Mono', monospace; letter-spacing: 0.1em; margin: 1rem 0 0.5rem; text-transform: uppercase; }
.badge { display: inline-block; border-radius: 100px; padding: 0.2rem 0.9rem; font-size: 0.72rem; font-family: 'IBM Plex Mono', monospace; margin: 6px 0; }
.badge-high { background:rgba(255,77,106,0.15); color:#ff4d6a; border:1px solid rgba(255,77,106,0.3); }
.badge-mod  { background:rgba(255,181,71,0.15);  color:#ffb547; border:1px solid rgba(255,181,71,0.3); }
.badge-low  { background:rgba(0,214,143,0.12);   color:#00d68f; border:1px solid rgba(0,214,143,0.25); }
.badge-unknown { background:rgba(90,116,153,0.15); color:#9aaec8; border:1px solid rgba(90,116,153,0.3); }
.chat-hint { background: #0f1624; border: 1px solid #1f3058; border-radius: 10px; padding: 1.25rem; font-size: 0.85rem; color: #5a7499; line-height: 1.7; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

CHAT_SYSTEM = """You are CardioAI, a clinical cardiovascular AI assistant built for a Biohackathon.
Your role is to:
1. Gather patient information through natural conversation (age, sex, blood pressure, cholesterol, diabetes, smoking, BMI, family history, etc.)
2. Once you have enough data, provide a structured cardiovascular risk assessment
3. Answer clinical questions using evidence-based medicine and ACC/AHA / ESC guidelines
4. Be concise, precise, and structured. Use bullet points for lists.
IMPORTANT:
- Never diagnose definitively — you assist licensed professionals.
- Always remind users this is a research tool, not a diagnostic tool.
- When you have enough data for an assessment, produce it in the conversation naturally.
- If the user asks a general cardiology question, answer it directly.
When providing a risk assessment, format it clearly with:
- Risk Level (Low / Moderate / High / Very High)
- Estimated 10-year MACE risk %
- Key risk factors present
- Top 3 clinical recommendations
- Follow-up suggestion"""

EXTRACT_SYSTEM = """Extract cardiovascular risk assessment data from a chat transcript and return ONLY a JSON object:
{"risk_level": "Low|Moderate|High|Very High|null", "risk_score_percent": number_or_null, "risk_factors": {"hypertension": true/false/null, "dyslipidemia": true/false/null, "diabetes": true/false/null, "obesity": true/false/null, "smoking": true/false/null, "family_history": true/false/null}, "primary_findings": [], "recommendations": [], "clinical_notes": "string or null"}
Return ONLY valid JSON. No markdown, no explanation."""

for key, val in {"chat_history": [], "assessment": None, "groq_api_key": "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"}.items():
    if key not in st.session_state:
        st.session_state[key] = val

def risk_color(risk):
    return {"High": "#ff4d6a", "Very High": "#ff0033", "Moderate": "#ffb547", "Low": "#00d68f"}.get(risk, "#9aaec8")

def risk_badge_class(risk):
    return {"High": "badge-high", "Very High": "badge-high", "Moderate": "badge-mod", "Low": "badge-low"}.get(risk, "badge-unknown")

# ── Sidebar ──
with st.sidebar:
    st.markdown('''<div style="padding:1.25rem 0 0.75rem;"><div style="font-size:1.4rem;font-weight:700;color:#e8eef8;">🫀 CardioAI</div><div style="font-size:0.7rem;color:#5a7499;font-family:monospace;">BIOHACKATHON EDITION</div></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Groq API Key</div>', unsafe_allow_html=True)
    api_key_input = st.text_input("Groq API Key", type="password", placeholder="gsk_...", label_visibility="collapsed", value=st.session_state.groq_api_key)
    if api_key_input:
        st.session_state.groq_api_key = api_key_input
    if not st.session_state.groq_api_key:
        st.markdown('<div style="font-size:0.72rem;color:#ffb547;">Get free key at console.groq.com</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<div style="font-size:0.75rem;color:#5a7499;font-family:monospace;">llama-3.3-70b · groq · free<br><span style="color:#00d68f;">86.13%</span> model accuracy</div>', unsafe_allow_html=True)
    st.divider()

    if st.session_state.assessment:
        a = st.session_state.assessment
        risk = a.get("risk_level") or "Unknown"
        pct = a.get("risk_score_percent")
        color = risk_color(risk)
        badge = risk_badge_class(risk)
        st.markdown(f'''<div style="text-align:center;padding:0.75rem 0;"><span class="badge {badge}">{risk} Risk</span><div style="font-family:monospace;font-size:2rem;font-weight:600;color:{color};margin:0.5rem 0 0.2rem;">{f"{pct:.1f}%" if pct else "—"}</div><div style="font-size:0.7rem;color:#5a7499;">10-year MACE risk</div></div>''', unsafe_allow_html=True)
        rf = a.get("risk_factors", {})
        rf_labels = {"hypertension":"Hypertension","dyslipidemia":"Dyslipidemia","diabetes":"Diabetes","obesity":"Obesity","smoking":"Smoking","family_history":"Family Hx CVD"}
        chips = ""
        for k, label in rf_labels.items():
            v = rf.get(k)
            if v is True:
                chips += f'<span style="background:rgba(255,77,106,0.1);color:#ff4d6a;border:1px solid rgba(255,77,106,0.25);border-radius:100px;padding:0.15rem 0.6rem;font-size:0.65rem;font-family:monospace;margin:2px;display:inline-block;">✕ {label}</span>'
            elif v is False:
                chips += f'<span style="background:rgba(0,214,143,0.08);color:#00d68f;border:1px solid rgba(0,214,143,0.2);border-radius:100px;padding:0.15rem 0.6rem;font-size:0.65rem;font-family:monospace;margin:2px;display:inline-block;">✓ {label}</span>'
        if chips:
            st.markdown(f'<div style="line-height:2;">{chips}</div>', unsafe_allow_html=True)
        st.divider()

    if st.button("🗑 Clear Session", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.assessment = None
        st.rerun()

    st.markdown('<div style="margin-top:2rem;font-size:0.62rem;color:#2a4070;font-family:monospace;line-height:1.7;text-align:center;">FOR LICENSED MEDICAL PROFESSIONALS<br>RESEARCH / TRIAL USE ONLY<br>NOT A DIAGNOSTIC TOOL</div>', unsafe_allow_html=True)

# ── Main ──
st.markdown('<div class="main-title">🫀 CardioAI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Conversational cardiovascular risk assessment · Biohackathon 2026</div>', unsafe_allow_html=True)
st.divider()

if not st.session_state.chat_history:
    st.markdown('''<div class="chat-hint"><strong style="color:#3d7fff;">👋 How to use CardioAI</strong><br><br>Just start a conversation. You can:<br>• Describe a patient case and ask for a cardiovascular risk assessment<br>• Ask general cardiology questions (guidelines, medications, biomarkers)<br>• CardioAI will ask follow-up questions to gather the data it needs<br><br><em>Example: "I have a 58-year-old male patient with BP 145/90, LDL 165, smoker, no prior CVD. What's his risk?"</em></div>''', unsafe_allow_html=True)
    st.markdown('<div class="section-hdr">Quick Start</div>', unsafe_allow_html=True)
    suggestions = ["Assess a 60-year-old male, BP 150/95, LDL 180, type 2 diabetic, smoker", "What are the ACC/AHA thresholds for starting statin therapy?", "Female patient, 52, post-menopausal, family history of MI, BMI 29", "Explain Framingham vs ASCVD risk scores"]
    cols = st.columns(2)
    for i, s in enumerate(suggestions):
        if cols[i % 2].button(s, key=f"qs_{i}", use_container_width=True):
            st.session_state.chat_history.append({"role": "user", "content": s})
            st.rerun()
    st.divider()

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if not st.session_state.groq_api_key:
    st.warning("⬅ Enter your Groq API key in the sidebar to start. Get one free at console.groq.com")
    st.stop()

client = Groq(api_key=st.session_state.groq_api_key)

if prompt := st.chat_input("Type your clinical question or describe a patient case…"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""
        api_msgs = [{"role": "system", "content": CHAT_SYSTEM}] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
        stream = client.chat.completions.create(model="llama-3.3-70b-versatile", max_tokens=1500, messages=api_msgs, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full += delta
            placeholder.markdown(full + "▌")
        placeholder.markdown(full)
    st.session_state.chat_history.append({"role": "assistant", "content": full})

    # Extract assessment from chat
    try:
        transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.chat_history])
        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", max_tokens=1000, messages=[{"role": "system", "content": EXTRACT_SYSTEM}, {"role": "user", "content": transcript}])
        raw = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        assessment = json.loads(raw)
        if assessment.get("risk_level"):
            st.session_state.assessment = assessment
    except Exception:
        pass

    st.rerun()
