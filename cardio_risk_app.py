import streamlit as st
import json
import base64
import anthropic
import re
import time
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CardioAI — Risk Assessment",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── Root palette ── */
:root {
  --bg0:     #0a0d13;
  --bg1:     #0f1520;
  --bg2:     #141c2e;
  --bg3:     #1a2540;
  --border:  #1f3058;
  --border2: #2a4070;
  --text0:   #e8eef8;
  --text1:   #9aaec8;
  --text2:   #5a7499;
  --accent:  #3d7fff;
  --green:   #00d68f;
  --amber:   #ffb547;
  --red:     #ff4d6a;
  --teal:    #00c8c8;
  --purple:  #a78bfa;
  --font:    'IBM Plex Sans', sans-serif;
  --mono:    'IBM Plex Mono', monospace;
}

/* ── Base resets ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg0) !important;
  color: var(--text0) !important;
  font-family: var(--font) !important;
}

[data-testid="stSidebar"] {
  background: var(--bg1) !important;
  border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * { color: var(--text0) !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

/* ── Typography ── */
h1, h2, h3, h4 { font-family: var(--font) !important; font-weight: 600 !important; color: var(--text0) !important; }
p, li, label, span { font-family: var(--font) !important; color: var(--text0) !important; }

/* ── Metric overrides ── */
[data-testid="metric-container"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  padding: 1rem 1.25rem !important;
}
[data-testid="metric-container"] label { color: var(--text2) !important; font-size: 11px !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--text0) !important; font-family: var(--mono) !important; font-size: 1.6rem !important; }

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stSelectbox select {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  color: var(--text0) !important;
  border-radius: 6px !important;
  font-family: var(--font) !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(61,127,255,0.15) !important;
}

/* ── Sliders ── */
.stSlider [data-baseweb="slider"] { background: transparent !important; }
.stSlider [data-testid="stSlider"] { color: var(--accent) !important; }

/* ── Buttons ── */
.stButton button {
  background: var(--accent) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 8px !important;
  font-family: var(--font) !important;
  font-weight: 500 !important;
  padding: 0.55rem 1.4rem !important;
  letter-spacing: 0.02em !important;
  transition: all 0.2s !important;
}
.stButton button:hover { background: #2d6ee8 !important; transform: translateY(-1px) !important; }
.stButton button:active { transform: translateY(0) !important; }

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  margin-bottom: 0.75rem !important;
}

/* ── Expander ── */
details {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
}
summary { color: var(--text1) !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"] { background: var(--bg1) !important; border-bottom: 1px solid var(--border) !important; }
[data-baseweb="tab"] { color: var(--text2) !important; font-family: var(--font) !important; }
[aria-selected="true"][data-baseweb="tab"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; }

/* ── Warning/info boxes ── */
[data-testid="stAlert"] {
  background: var(--bg2) !important;
  border-left: 3px solid var(--amber) !important;
  border-radius: 0 8px 8px 0 !important;
  color: var(--text1) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg0); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 3px; }

/* ── Custom components ── */
.risk-badge {
  display: inline-block;
  padding: 0.35rem 1rem;
  border-radius: 100px;
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.risk-low    { background: rgba(0,214,143,0.12); color: #00d68f; border: 1px solid rgba(0,214,143,0.25); }
.risk-moderate { background: rgba(255,181,71,0.12); color: #ffb547; border: 1px solid rgba(255,181,71,0.25); }
.risk-high   { background: rgba(255,77,106,0.12); color: #ff4d6a; border: 1px solid rgba(255,77,106,0.25); }
.risk-very-high { background: rgba(255,77,106,0.2); color: #ff2244; border: 1px solid rgba(255,77,106,0.4); }

.section-header {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text2);
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.kv-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.45rem 0;
  border-bottom: 1px solid rgba(31,48,88,0.6);
  font-size: 0.88rem;
}
.kv-key { color: var(--text2); }
.kv-val { color: var(--text0); font-family: var(--mono); font-size: 0.82rem; }

.gauge-bar-bg {
  background: var(--bg3);
  border-radius: 100px;
  height: 8px;
  width: 100%;
  margin-top: 6px;
  overflow: hidden;
}
.gauge-bar-fill {
  height: 100%;
  border-radius: 100px;
  transition: width 1s ease;
}

.vitals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 1rem;
}
.vital-card {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  text-align: center;
}
.vital-label { color: var(--text2); font-size: 0.7rem; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 4px; }
.vital-value { color: var(--text0); font-family: var(--mono); font-size: 1.2rem; font-weight: 500; }
.vital-unit  { color: var(--text2); font-size: 0.7rem; margin-left: 2px; }

.model-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(61,127,255,0.1);
  border: 1px solid rgba(61,127,255,0.25);
  border-radius: 100px;
  padding: 0.2rem 0.75rem;
  font-size: 0.7rem;
  color: var(--accent);
  font-family: var(--mono);
  letter-spacing: 0.04em;
}
.pulse-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

/* ── Chat input area ── */
[data-testid="stChatInputContainer"] {
  background: var(--bg1) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
[data-testid="stChatInputContainer"] textarea {
  background: transparent !important;
  color: var(--text0) !important;
  font-family: var(--font) !important;
}

/* ── Select boxes ── */
[data-baseweb="select"] { background: var(--bg2) !important; }
[data-baseweb="select"] * { background: var(--bg2) !important; color: var(--text0) !important; }

/* ── Number input buttons ── */
[data-testid="stNumberInput"] button {
  background: var(--bg3) !important;
  border: 1px solid var(--border) !important;
  color: var(--text1) !important;
  padding: 0.25rem 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def risk_color(level: str) -> str:
    level = level.lower()
    if "very high" in level or "critical" in level: return "#ff2244"
    if "high" in level:   return "#ff4d6a"
    if "moderate" in level or "medium" in level: return "#ffb547"
    return "#00d68f"

def risk_class(level: str) -> str:
    level = level.lower()
    if "very high" in level or "critical" in level: return "risk-very-high"
    if "high" in level:   return "risk-high"
    if "moderate" in level or "medium" in level: return "risk-moderate"
    return "risk-low"

def bar_color(level: str) -> str:
    level = level.lower()
    if "very high" in level or "critical" in level: return "#ff2244"
    if "high" in level:   return "#ff4d6a"
    if "moderate" in level or "medium" in level: return "#ffb547"
    return "#00d68f"

def pct_from_level(level: str) -> int:
    level = level.lower()
    if "very high" in level or "critical" in level: return 92
    if "high" in level:   return 72
    if "moderate" in level or "medium" in level: return 48
    return 18

def make_gauge(level: str):
    pct   = pct_from_level(level)
    color = bar_color(level)
    st.markdown(f"""
    <div class="gauge-bar-bg">
      <div class="gauge-bar-fill" style="width:{pct}%; background:{color};"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:4px;font-size:0.7rem;color:var(--text2);font-family:var(--mono)">
      <span>LOW</span><span>MODERATE</span><span>HIGH</span><span>CRITICAL</span>
    </div>
    """, unsafe_allow_html=True)

def vitals_grid(patient: dict):
    age  = patient.get("age", "—")
    sbp  = patient.get("systolic_bp", patient.get("sbp", "—"))
    dbp  = patient.get("diastolic_bp", patient.get("dbp", "—"))
    hr   = patient.get("heart_rate", "—")
    chol = patient.get("total_cholesterol", patient.get("cholesterol", "—"))
    bmi  = patient.get("bmi", "—")

    st.markdown(f"""
    <div class="vitals-grid">
      <div class="vital-card"><div class="vital-label">Age</div><div class="vital-value">{age}<span class="vital-unit">yrs</span></div></div>
      <div class="vital-card"><div class="vital-label">Systolic BP</div><div class="vital-value">{sbp}<span class="vital-unit">mmHg</span></div></div>
      <div class="vital-card"><div class="vital-label">Diastolic BP</div><div class="vital-value">{dbp}<span class="vital-unit">mmHg</span></div></div>
      <div class="vital-card"><div class="vital-label">Heart Rate</div><div class="vital-value">{hr}<span class="vital-unit">bpm</span></div></div>
      <div class="vital-card"><div class="vital-label">Total Cholesterol</div><div class="vital-value">{chol}<span class="vital-unit">mg/dL</span></div></div>
      <div class="vital-card"><div class="vital-label">BMI</div><div class="vital-value">{bmi}<span class="vital-unit">kg/m²</span></div></div>
    </div>
    """, unsafe_allow_html=True)


# ── Claude API wrappers ────────────────────────────────────────────────────────

def analyze_report(pdf_bytes: bytes | None, manual_data: dict | None, client: anthropic.Anthropic):
    """Send lab data to Claude and return parsed JSON assessment."""
    system_prompt = """You are CardioAI, an expert cardiovascular risk assessment engine used by medical professionals in a biohackathon research context (86.13% accuracy). 

Analyze the provided lab report / patient data and return a SINGLE valid JSON object with EXACTLY this structure — no markdown fences, no extra text:

{
  "patient": {
    "age": <int or null>,
    "sex": "<Male/Female/Unknown>",
    "systolic_bp": <int or null>,
    "diastolic_bp": <int or null>,
    "heart_rate": <int or null>,
    "total_cholesterol": <float or null>,
    "hdl": <float or null>,
    "ldl": <float or null>,
    "triglycerides": <float or null>,
    "bmi": <float or null>,
    "hba1c": <float or null>,
    "glucose": <float or null>,
    "creatinine": <float or null>,
    "egfr": <float or null>
  },
  "risk_level": "<Low | Moderate | High | Very High>",
  "risk_score_percent": <float 0-100>,
  "framingham_score": <float or null>,
  "ascvd_score": <float or null>,
  "primary_findings": ["<finding 1>", "<finding 2>", ...],
  "risk_factors": {
    "hypertension": <true/false/null>,
    "dyslipidemia": <true/false/null>,
    "diabetes": <true/false/null>,
    "obesity": <true/false/null>,
    "smoking": <true/false/null>,
    "family_history": <true/false/null>,
    "ckd": <true/false/null>
  },
  "red_flags": ["<urgent concern if any>"],
  "recommendations": [
    {"category": "<Medication|Lifestyle|Monitoring|Referral>", "action": "<concise action>", "priority": "<High|Medium|Low>"}
  ],
  "biomarker_summary": [
    {"name": "<biomarker>", "value": "<value with unit>", "status": "<Normal|Borderline|Abnormal|Critical>", "interpretation": "<1-line note>"}
  ],
  "differential_diagnoses": ["<if relevant>"],
  "follow_up_timeline": "<e.g. 3 months>",
  "clinical_notes": "<2-3 sentences of overall clinical impression>"
}"""

    messages = []

    if pdf_bytes:
        b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        messages.append({
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
                {"type": "text", "text": "Analyze this lab report and return the JSON assessment."}
            ]
        })
    elif manual_data:
        messages.append({
            "role": "user",
            "content": f"Analyze this patient data and return the JSON assessment:\n\n{json.dumps(manual_data, indent=2)}"
        })
    else:
        return None

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        system=system_prompt,
        messages=messages,
    )
    raw = resp.content[0].text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def chat_response(messages: list, assessment: dict | None, client: anthropic.Anthropic):
    """Stream a clinical assistant response."""
    system = """You are CardioAI, a clinical cardiovascular AI assistant. You speak precisely, use evidence-based medicine, cite clinical guidelines (ACC/AHA, ESC) where relevant, and keep answers structured. Never diagnose definitively — you assist licensed professionals. Use bullet points for lists. Be concise."""
    if assessment:
        system += f"\n\nCurrent patient assessment:\n{json.dumps(assessment, indent=2)}"

    stream = client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        system=system,
        messages=messages,
    )
    return stream


# ── State init ────────────────────────────────────────────────────────────────

for key, val in {
    "assessment": None,
    "chat_history": [],
    "patient_name": "",
    "analysis_done": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding:1.25rem 0 1rem;">
      <div style="font-size:1.4rem;font-weight:700;letter-spacing:-0.02em;color:#e8eef8;margin-bottom:2px;">🫀 CardioAI</div>
      <div style="font-size:0.72rem;color:#5a7499;font-family:'IBM Plex Mono',monospace;letter-spacing:0.08em;">BIOHACKATHON EDITION</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">System</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="model-badge"><div class="pulse-dot"></div>claude-sonnet-4 · live</div>
    <div style="font-size:0.72rem;color:#5a7499;margin-top:8px;">Accuracy: <span style="color:#00d68f;font-family:monospace">86.13%</span> · Research mode</div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="section-header">Patient Info</div>', unsafe_allow_html=True)
    st.session_state.patient_name = st.text_input("Patient ID / Name", value=st.session_state.patient_name, placeholder="e.g. PT-00142")

    st.divider()
    st.markdown('<div class="section-header">Input Method</div>', unsafe_allow_html=True)
    input_mode = st.radio("", ["📄 Upload Lab PDF", "✏️ Manual Entry"], label_visibility="collapsed")

    st.divider()
    if st.session_state.assessment:
        risk = st.session_state.assessment.get("risk_level", "Unknown")
        pct  = st.session_state.assessment.get("risk_score_percent", 0)
        rc   = risk_class(risk)
        st.markdown(f"""
        <div class="section-header">Active Assessment</div>
        <div style="text-align:center;padding:1rem 0;">
          <div class="risk-badge {rc}">{risk} Risk</div>
          <div style="font-family:monospace;font-size:2rem;font-weight:600;color:#e8eef8;margin:0.75rem 0 0.25rem;">{pct:.1f}%</div>
          <div style="font-size:0.72rem;color:#5a7499;">composite risk score</div>
        </div>
        """, unsafe_allow_html=True)
        make_gauge(risk)
        st.divider()

    if st.button("🗑 Clear Session"):
        st.session_state.assessment = None
        st.session_state.chat_history = []
        st.session_state.analysis_done = False
        st.rerun()

    st.markdown("""
    <div style="position:fixed;bottom:1rem;left:0;right:0;width:240px;margin:auto;text-align:center;">
      <div style="font-size:0.65rem;color:#2a4070;font-family:monospace;line-height:1.6;">
        FOR LICENSED MEDICAL PROFESSIONALS<br>RESEARCH / TRIAL USE ONLY<br>NOT A DIAGNOSTIC TOOL
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── Main Layout ───────────────────────────────────────────────────────────────

client = anthropic.Anthropic()

col_header, col_badge = st.columns([4, 1])
with col_header:
    st.markdown("""
    <div style="padding:0.5rem 0 0;">
      <h1 style="font-size:1.6rem;margin-bottom:0.15rem;letter-spacing:-0.02em;">
        Cardiovascular Risk Assessment
      </h1>
      <div style="color:#5a7499;font-size:0.85rem;">AI-powered clinical decision support · Biohackathon 2025</div>
    </div>
    """, unsafe_allow_html=True)
with col_badge:
    if st.session_state.patient_name:
        st.markdown(f"""
        <div style="text-align:right;padding-top:1rem;">
          <div style="font-size:0.7rem;color:#5a7499;font-family:monospace;margin-bottom:4px;">PATIENT</div>
          <div style="font-size:0.95rem;font-weight:600;color:#3d7fff;">{st.session_state.patient_name}</div>
          <div style="font-size:0.7rem;color:#5a7499;font-family:monospace;">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ── WHO Guidelines Notice ─────────────────────────────────────────────────────
st.markdown("""
<div style="background:#0f1a2e;border:1px solid #1f3058;border-left:3px solid #3d7fff;border-radius:0 10px 10px 0;padding:1rem 1.25rem;margin-bottom:1.25rem;">
  <div style="font-size:0.7rem;color:#3d7fff;font-family:'IBM Plex Mono',monospace;letter-spacing:0.1em;margin-bottom:0.75rem;">
    ℹ IMPORTANT NOTICE — WHO / ACC / AHA CLINICAL REFERENCE THRESHOLDS
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem 1.5rem;font-size:0.78rem;">

    <div>
      <div style="color:#5a7499;font-family:monospace;font-size:0.65rem;letter-spacing:0.08em;margin-bottom:6px;">BLOOD PRESSURE (WHO)</div>
      <div style="color:#00d68f;">Normal &lt; 120/80 mmHg</div>
      <div style="color:#ffb547;">Elevated 120–129 / &lt;80</div>
      <div style="color:#ff8c42;">Stage 1 HT 130–139 / 80–89</div>
      <div style="color:#ff4d6a;">Stage 2 HT ≥ 140/90 mmHg</div>
      <div style="color:#ff0033;">Crisis ≥ 180/120 mmHg</div>
    </div>

    <div>
      <div style="color:#5a7499;font-family:monospace;font-size:0.65rem;letter-spacing:0.08em;margin-bottom:6px;">LIPIDS (ACC/AHA)</div>
      <div style="color:#00d68f;">LDL Optimal &lt; 100 mg/dL</div>
      <div style="color:#ffb547;">LDL Borderline 130–159</div>
      <div style="color:#ff4d6a;">LDL High ≥ 160 mg/dL</div>
      <div style="color:#00d68f;">HDL Protective ≥ 60 mg/dL</div>
      <div style="color:#ff4d6a;">HDL Low &lt; 40 mg/dL (M) / &lt;50 (F)</div>
      <div style="color:#ffb547;">Triglycerides Borderline 150–199</div>
    </div>

    <div>
      <div style="color:#5a7499;font-family:monospace;font-size:0.65rem;letter-spacing:0.08em;margin-bottom:6px;">GLUCOSE / HbA1c (WHO)</div>
      <div style="color:#00d68f;">Fasting Normal &lt; 100 mg/dL</div>
      <div style="color:#ffb547;">Pre-diabetes 100–125 mg/dL</div>
      <div style="color:#ff4d6a;">Diabetes ≥ 126 mg/dL</div>
      <div style="color:#00d68f;">HbA1c Normal &lt; 5.7%</div>
      <div style="color:#ffb547;">HbA1c Pre-DM 5.7–6.4%</div>
      <div style="color:#ff4d6a;">HbA1c Diabetes ≥ 6.5%</div>
    </div>

    <div>
      <div style="color:#5a7499;font-family:monospace;font-size:0.65rem;letter-spacing:0.08em;margin-bottom:6px;">BMI / RENAL (WHO)</div>
      <div style="color:#00d68f;">BMI Normal 18.5–24.9</div>
      <div style="color:#ffb547;">BMI Overweight 25–29.9</div>
      <div style="color:#ff4d6a;">BMI Obese ≥ 30</div>
      <div style="color:#00d68f;">eGFR Normal ≥ 90 mL/min</div>
      <div style="color:#ffb547;">eGFR Mild CKD 60–89</div>
      <div style="color:#ff4d6a;">eGFR Mod CKD 30–59</div>
      <div style="color:#ff0033;">eGFR Severe &lt; 30</div>
    </div>

  </div>
  <div style="margin-top:0.9rem;padding-top:0.75rem;border-top:1px solid #1f3058;font-size:0.72rem;color:#5a7499;">
    This AI system is intended for use by <strong style="color:#9aaec8;">licensed medical professionals only</strong>.
    All parameters are evaluated against WHO / ACC / AHA 2023 guidelines. Results are for
    <strong style="color:#9aaec8;">trial / research purposes only</strong> and do <strong style="color:#9aaec8;">NOT</strong>
    replace professional medical diagnosis. Model Accuracy: <span style="color:#00d68f;font-family:monospace;">86.13%</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab_analysis, tab_chat, tab_trends = st.tabs(["📊  Analysis", "💬  Clinical Chat", "📈  Biomarkers"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANALYSIS
# ════════════════════════════════════════════════════════════════════════════
with tab_analysis:
    if input_mode == "📄 Upload Lab PDF":
        uploaded = st.file_uploader("Upload Lab Report (PDF)", type=["pdf"], label_visibility="collapsed")
        if uploaded and not st.session_state.analysis_done:
            if st.button("🔬 Run Risk Assessment", use_container_width=True):
                with st.spinner("Analyzing report with CardioAI…"):
                    try:
                        result = analyze_report(uploaded.read(), None, client)
                        st.session_state.assessment = result
                        st.session_state.analysis_done = True
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

    else:  # Manual Entry
        st.markdown('<div class="section-header">Patient Demographics & Vitals</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        age  = c1.number_input("Age (years)", 1, 120, 55)
        sex  = c2.selectbox("Sex", ["Male", "Female", "Other"])
        sbp  = c3.number_input("Systolic BP (mmHg)", 60, 280, 130)
        dbp  = c1.number_input("Diastolic BP (mmHg)", 40, 180, 85)
        hr   = c2.number_input("Heart Rate (bpm)", 30, 250, 72)
        bmi  = c3.number_input("BMI (kg/m²)", 10.0, 70.0, 26.5)

        st.markdown('<div class="section-header" style="margin-top:1rem;">Lipid Panel & Metabolic</div>', unsafe_allow_html=True)
        c4, c5, c6 = st.columns(3)
        chol = c4.number_input("Total Cholesterol (mg/dL)", 50, 600, 210)
        hdl  = c5.number_input("HDL (mg/dL)", 10, 150, 45)
        ldl  = c6.number_input("LDL (mg/dL)", 10, 400, 140)
        trig = c4.number_input("Triglycerides (mg/dL)", 20, 2000, 160)
        gluc = c5.number_input("Fasting Glucose (mg/dL)", 50, 600, 95)
        hba1c= c6.number_input("HbA1c (%)", 3.0, 20.0, 5.6)

        st.markdown('<div class="section-header" style="margin-top:1rem;">Renal Function</div>', unsafe_allow_html=True)
        c7, c8 = st.columns(2)
        creat = c7.number_input("Creatinine (mg/dL)", 0.1, 20.0, 0.9)
        egfr  = c8.number_input("eGFR (mL/min/1.73m²)", 1, 150, 85)

        st.markdown('<div class="section-header" style="margin-top:1rem;">Risk Factor History</div>', unsafe_allow_html=True)
        r1, r2, r3, r4 = st.columns(4)
        smoking  = r1.checkbox("Current Smoker")
        diabetes = r2.checkbox("Diabetes")
        fam_hx   = r3.checkbox("Family History CVD")
        prev_cvd = r4.checkbox("Prior CVD Event")

        manual = {
            "age": age, "sex": sex, "systolic_bp": sbp, "diastolic_bp": dbp,
            "heart_rate": hr, "bmi": bmi, "total_cholesterol": chol,
            "hdl": hdl, "ldl": ldl, "triglycerides": trig,
            "glucose": gluc, "hba1c": hba1c, "creatinine": creat, "egfr": egfr,
            "smoking": smoking, "diabetes": diabetes,
            "family_history_cvd": fam_hx, "prior_cvd": prev_cvd,
        }

        if st.button("🔬 Run Risk Assessment", use_container_width=True):
            with st.spinner("Computing cardiovascular risk profile…"):
                try:
                    result = analyze_report(None, manual, client)
                    st.session_state.assessment = result
                    st.session_state.analysis_done = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # ── Results ──
    if st.session_state.assessment:
        a = st.session_state.assessment
        risk  = a.get("risk_level", "Unknown")
        pct   = a.get("risk_score_percent", 0)
        patient = a.get("patient", {})

        st.divider()

        # ── Hero risk display ──
        hero_col, detail_col = st.columns([1, 2])

        with hero_col:
            color = risk_color(risk)
            rc    = risk_class(risk)
            fram  = a.get("framingham_score")
            ascvd = a.get("ascvd_score")

            st.markdown(f"""
            <div style="background:rgba(10,13,19,0.8);border:1px solid {color}33;border-radius:12px;padding:1.5rem;text-align:center;">
              <div style="font-size:0.7rem;color:#5a7499;font-family:monospace;letter-spacing:0.1em;margin-bottom:1rem;">RISK CLASSIFICATION</div>
              <div class="risk-badge {rc}" style="font-size:0.9rem;padding:0.5rem 1.5rem;">{risk} Risk</div>
              <div style="font-size:3.5rem;font-weight:700;color:{color};font-family:'IBM Plex Mono';margin:1rem 0 0.25rem;line-height:1;">{pct:.1f}<span style="font-size:1.5rem;opacity:0.7">%</span></div>
              <div style="font-size:0.72rem;color:#5a7499;margin-bottom:1.25rem;">10-year MACE risk</div>
            """, unsafe_allow_html=True)
            make_gauge(risk)
            st.markdown(f"""
              <div style="margin-top:1.25rem;display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="background:#141c2e;border:1px solid #1f3058;border-radius:8px;padding:0.6rem;text-align:center;">
                  <div style="font-size:0.65rem;color:#5a7499;font-family:monospace;">FRAMINGHAM</div>
                  <div style="font-size:1.2rem;font-family:monospace;color:#e8eef8;">{f"{fram:.1f}%" if fram else "N/A"}</div>
                </div>
                <div style="background:#141c2e;border:1px solid #1f3058;border-radius:8px;padding:0.6rem;text-align:center;">
                  <div style="font-size:0.65rem;color:#5a7499;font-family:monospace;">ASCVD</div>
                  <div style="font-size:1.2rem;font-family:monospace;color:#e8eef8;">{f"{ascvd:.1f}%" if ascvd else "N/A"}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        with detail_col:
            # Vitals
            st.markdown('<div class="section-header">Patient Vitals</div>', unsafe_allow_html=True)
            vitals_grid(patient)

            # Risk factors
            rf = a.get("risk_factors", {})
            rf_labels = {
                "hypertension": "Hypertension",
                "dyslipidemia": "Dyslipidemia",
                "diabetes": "Diabetes Mellitus",
                "obesity": "Obesity (BMI ≥30)",
                "smoking": "Active Smoking",
                "family_history": "Family History CVD",
                "ckd": "Chronic Kidney Disease",
            }
            present = [v for k, v in rf_labels.items() if rf.get(k) is True]
            absent  = [v for k, v in rf_labels.items() if rf.get(k) is False]

            if present or absent:
                st.markdown('<div class="section-header">Risk Factor Profile</div>', unsafe_allow_html=True)
                chips = ""
                for r in present:
                    chips += f'<span style="background:rgba(255,77,106,0.12);color:#ff4d6a;border:1px solid rgba(255,77,106,0.25);border-radius:100px;padding:0.2rem 0.75rem;font-size:0.72rem;font-family:monospace;margin:3px;display:inline-block;">✕ {r}</span>'
                for r in absent:
                    chips += f'<span style="background:rgba(0,214,143,0.08);color:#00d68f;border:1px solid rgba(0,214,143,0.2);border-radius:100px;padding:0.2rem 0.75rem;font-size:0.72rem;font-family:monospace;margin:3px;display:inline-block;">✓ {r}</span>'
                st.markdown(f'<div style="margin-bottom:0.75rem;">{chips}</div>', unsafe_allow_html=True)

        # ── Red flags ──
        red_flags = a.get("red_flags", [])
        if red_flags:
            st.markdown("---")
            flag_html = "".join([f'<div style="padding:0.4rem 0;border-bottom:1px solid rgba(255,34,68,0.1);color:#ff4d6a;font-size:0.88rem;">⚠ {f}</div>' for f in red_flags])
            st.markdown(f"""
            <div style="background:rgba(255,34,68,0.06);border:1px solid rgba(255,34,68,0.3);border-radius:10px;padding:1rem 1.25rem;">
              <div style="font-size:0.7rem;color:#ff4d6a;font-family:monospace;letter-spacing:0.1em;margin-bottom:0.75rem;">⚠ RED FLAGS — URGENT REVIEW</div>
              {flag_html}
            </div>
            """, unsafe_allow_html=True)

        # ── Findings & Recommendations ──
        st.markdown("---")
        fc, rc2 = st.columns(2)

        with fc:
            st.markdown('<div class="section-header">Primary Findings</div>', unsafe_allow_html=True)
            for f in a.get("primary_findings", []):
                st.markdown(f'<div class="kv-row"><span style="color:#9aaec8;font-size:0.88rem;">→ {f}</span></div>', unsafe_allow_html=True)

        with rc2:
            st.markdown('<div class="section-header">Clinical Recommendations</div>', unsafe_allow_html=True)
            for rec in a.get("recommendations", []):
                pri   = rec.get("priority", "Medium")
                cat   = rec.get("category", "")
                act   = rec.get("action", "")
                p_col = {"High": "#ff4d6a", "Medium": "#ffb547", "Low": "#00d68f"}.get(pri, "#5a7499")
                st.markdown(f"""
                <div class="kv-row" style="align-items:flex-start;gap:8px;">
                  <div style="min-width:56px;">
                    <span style="background:{p_col}1a;color:{p_col};border:1px solid {p_col}33;border-radius:4px;padding:0.1rem 0.4rem;font-size:0.65rem;font-family:monospace;">{pri}</span>
                  </div>
                  <div>
                    <div style="font-size:0.72rem;color:#5a7499;font-family:monospace;margin-bottom:2px;">{cat}</div>
                    <div style="font-size:0.85rem;color:#e8eef8;">{act}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

        # ── Clinical notes ──
        notes = a.get("clinical_notes", "")
        follow = a.get("follow_up_timeline", "")
        if notes:
            st.markdown("---")
            st.markdown(f"""
            <div style="background:#141c2e;border:1px solid #1f3058;border-radius:10px;padding:1.25rem;">
              <div style="font-size:0.7rem;color:#5a7499;font-family:monospace;letter-spacing:0.1em;margin-bottom:0.75rem;">CLINICAL IMPRESSION</div>
              <div style="color:#9aaec8;font-size:0.9rem;line-height:1.7;">{notes}</div>
              {"" if not follow else f'<div style="margin-top:0.75rem;font-size:0.75rem;color:#3d7fff;font-family:monospace;">Follow-up: {follow}</div>'}
            </div>
            """, unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;color:#2a4070;">
          <div style="font-size:3rem;margin-bottom:1rem;opacity:0.4;">🫀</div>
          <div style="font-size:1rem;font-weight:500;color:#5a7499;">No assessment loaded</div>
          <div style="font-size:0.82rem;color:#2a4070;margin-top:0.5rem;">Upload a lab PDF or enter patient data to begin</div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — CLINICAL CHAT
# ════════════════════════════════════════════════════════════════════════════
with tab_chat:
    if not st.session_state.assessment:
        st.info("Run an assessment first to enable context-aware clinical Q&A.")
    else:
        st.markdown("""
        <div style="font-size:0.82rem;color:#5a7499;margin-bottom:1rem;">
          Ask CardioAI about findings, medications, guidelines, or differential diagnoses.
          All responses are grounded in the current patient assessment.
        </div>
        """, unsafe_allow_html=True)

        # Suggested prompts
        sugg = [
            "Explain the primary risk drivers",
            "What medications should be considered?",
            "Interpret the lipid panel",
            "What does the Framingham score indicate?",
            "Outline a 6-month management plan",
            "Any red-flag signs to monitor?",
        ]
        cols = st.columns(3)
        for i, s in enumerate(sugg):
            if cols[i % 3].button(s, key=f"sugg_{i}"):
                st.session_state.chat_history.append({"role": "user", "content": s})
                st.rerun()

        st.divider()

        # Display history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input
        if prompt := st.chat_input("Ask a clinical question…"):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                placeholder = st.empty()
                full = ""
                api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_history]
                with chat_response(api_msgs, st.session_state.assessment, client) as stream:
                    for chunk in stream.text_stream:
                        full += chunk
                        placeholder.markdown(full + "▌")
                placeholder.markdown(full)

            st.session_state.chat_history.append({"role": "assistant", "content": full})


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — BIOMARKERS
# ════════════════════════════════════════════════════════════════════════════
with tab_trends:
    if not st.session_state.assessment:
        st.info("Run an assessment to view the biomarker panel.")
    else:
        biomarkers = st.session_state.assessment.get("biomarker_summary", [])
        if not biomarkers:
            st.warning("No biomarker data extracted. Try re-running with a detailed lab report.")
        else:
            st.markdown('<div class="section-header">Biomarker Panel</div>', unsafe_allow_html=True)

            status_color = {
                "Normal": "#00d68f",
                "Borderline": "#ffb547",
                "Abnormal": "#ff4d6a",
                "Critical": "#ff0033",
            }

            cols_per_row = 3
            rows = [biomarkers[i:i+cols_per_row] for i in range(0, len(biomarkers), cols_per_row)]
            for row in rows:
                cols = st.columns(cols_per_row)
                for col, bm in zip(cols, row):
                    name  = bm.get("name", "—")
                    val   = bm.get("value", "—")
                    stat  = bm.get("status", "Normal")
                    interp= bm.get("interpretation", "")
                    sc    = status_color.get(stat, "#9aaec8")
                    with col:
                        st.markdown(f"""
                        <div style="background:#141c2e;border:1px solid #1f3058;border-radius:10px;padding:1rem;margin-bottom:10px;">
                          <div style="font-size:0.7rem;color:#5a7499;font-family:monospace;letter-spacing:0.06em;margin-bottom:6px;">{name.upper()}</div>
                          <div style="font-size:1.35rem;font-family:'IBM Plex Mono';font-weight:500;color:#e8eef8;margin-bottom:6px;">{val}</div>
                          <div style="margin-bottom:6px;"><span style="background:{sc}1a;color:{sc};border:1px solid {sc}33;border-radius:100px;padding:0.15rem 0.6rem;font-size:0.65rem;font-family:monospace;">{stat}</span></div>
                          <div style="font-size:0.78rem;color:#5a7499;line-height:1.4;">{interp}</div>
                        </div>
                        """, unsafe_allow_html=True)

        # ── Patient summary export ──
        st.divider()
        st.markdown('<div class="section-header">Export</div>', unsafe_allow_html=True)
        if st.button("📋 Copy Assessment JSON"):
            st.code(json.dumps(st.session_state.assessment, indent=2), language="json")
