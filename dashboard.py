import os
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


API_URL = os.getenv("VCG_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(
    page_title="VoiceCloneGuard | AI Voice Security",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# STYLE
# -----------------------------------------------------------------------------

st.markdown(
    """
<style>
:root {
  --bg: #070b12;
  --panel: #0e1521;
  --panel-2: #111b2a;
  --border: #203047;
  --muted: #7f91a8;
  --text: #eaf2ff;
  --accent: #55a8ff;
  --accent-2: #7c6cff;
  --good: #39d98a;
  --warn: #ffbd4a;
  --danger: #ff6578;
}

.stApp {
  background:
    radial-gradient(circle at 12% 0%, rgba(85,168,255,.12), transparent 28%),
    radial-gradient(circle at 88% 5%, rgba(124,108,255,.10), transparent 25%),
    var(--bg);
  color: var(--text);
}

.block-container {
  max-width: 1320px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

.hero {
  padding: 8px 0 18px 0;
}

.brand-row {
  display:flex;
  align-items:center;
  gap:12px;
  margin-bottom:10px;
}

.brand-mark {
  width:42px;
  height:42px;
  border-radius:12px;
  display:flex;
  align-items:center;
  justify-content:center;
  background: linear-gradient(135deg, rgba(85,168,255,.20), rgba(124,108,255,.22));
  border:1px solid rgba(124,108,255,.30);
  font-size:22px;
}

.eyebrow {
  text-transform:uppercase;
  letter-spacing:.16em;
  color:#8fa7c7;
  font-size:.70rem;
  font-weight:800;
}

.title {
  font-size:3.0rem;
  line-height:1.03;
  letter-spacing:-.045em;
  font-weight:800;
  margin:0;
  color:#f5f9ff;
}

.subtitle {
  color:#91a1b8;
  font-size:1.02rem;
  margin-top:10px;
  max-width:820px;
  line-height:1.55;
}

.status {
  display:inline-flex;
  align-items:center;
  gap:8px;
  margin-top:16px;
  padding:7px 11px;
  border-radius:999px;
  border:1px solid rgba(57,217,138,.20);
  background:rgba(57,217,138,.07);
  color:#85e7b9;
  font-size:.78rem;
  font-weight:700;
}

.status-dot { width:8px; height:8px; border-radius:50%; background:#39d98a; box-shadow:0 0 14px rgba(57,217,138,.5); }

.section {
  margin-top:26px;
}

.section-head {
  display:flex;
  align-items:end;
  justify-content:space-between;
  gap:18px;
  margin-bottom:12px;
}

.section-title {
  font-size:1.20rem;
  font-weight:800;
  color:#f0f5fd;
  margin:0;
}

.section-copy {
  color:#71849d;
  font-size:.84rem;
  margin-top:4px;
}

.card {
  background:linear-gradient(180deg, rgba(17,27,42,.96), rgba(12,19,30,.96));
  border:1px solid var(--border);
  border-radius:16px;
  padding:18px;
  box-shadow:0 12px 40px rgba(0,0,0,.18);
}

.metric {
  min-height:126px;
}

.metric-label {
  color:#8296b1;
  text-transform:uppercase;
  letter-spacing:.11em;
  font-size:.68rem;
  font-weight:800;
}

.metric-value {
  font-size:2rem;
  font-weight:800;
  letter-spacing:-.03em;
  margin-top:10px;
  color:#f1f6fd;
}

.metric-note {
  font-size:.76rem;
  color:#6f8199;
  margin-top:7px;
}

.empty-value { color:#53647b; }

.pipeline {
  display:grid;
  grid-template-columns: repeat(5, 1fr);
  gap:10px;
  align-items:stretch;
}

.pipeline-step {
  position:relative;
  background:#0c1420;
  border:1px solid #203047;
  border-radius:14px;
  padding:14px 12px;
  min-height:92px;
}

.pipeline-step:after {
  content:'›';
  position:absolute;
  right:-9px;
  top:50%;
  transform:translateY(-50%);
  color:#49627f;
  font-size:24px;
  z-index:2;
}

.pipeline-step:last-child:after { display:none; }

.pipeline-num {
  color:#5fa9ff;
  font-weight:900;
  font-size:.67rem;
  letter-spacing:.12em;
}

.pipeline-name {
  color:#edf4ff;
  font-size:.90rem;
  font-weight:750;
  margin-top:8px;
}

.pipeline-desc {
  color:#71849d;
  font-size:.72rem;
  margin-top:5px;
  line-height:1.35;
}

.upload-card {
  border:1px solid rgba(85,168,255,.28);
  background:linear-gradient(180deg, rgba(18,31,50,.95), rgba(11,19,31,.95));
}

.decision {
  border-radius:16px;
  padding:20px;
  border:1px solid #23344c;
  background:#0c1420;
}

.decision-allow { border-color:rgba(57,217,138,.28); background:linear-gradient(180deg, rgba(11,31,25,.9), rgba(10,22,20,.9)); }
.decision-verify { border-color:rgba(255,189,74,.30); background:linear-gradient(180deg, rgba(39,31,13,.92), rgba(26,21,12,.92)); }
.decision-escalate { border-color:rgba(255,101,120,.30); background:linear-gradient(180deg, rgba(43,18,24,.92), rgba(26,14,19,.92)); }

.decision-kicker { font-size:.67rem; text-transform:uppercase; letter-spacing:.12em; font-weight:900; color:#8395ad; }
.decision-title { font-size:2.25rem; font-weight:900; letter-spacing:-.035em; margin-top:6px; }
.decision-sub { color:#8ea0b7; font-size:.83rem; margin-top:5px; }

.evidence {
  border:1px solid #213149;
  background:#0c1420;
  border-radius:11px;
  padding:11px 13px;
  margin:7px 0;
  color:#d7e2f0;
  font-size:.83rem;
}

.tiny {
  color:#6e8097;
  font-size:.73rem;
  line-height:1.45;
}

div[data-testid="stFileUploader"] {
  background:rgba(7,12,20,.45);
  border:1px dashed #385275;
  border-radius:13px;
  padding:10px;
}

.stButton > button {
  background:#101a28;
  color:#dce8f8;
  border:1px solid #28405e;
  border-radius:10px;
  font-weight:750;
}

.stButton > button:hover {
  border-color:#55a8ff;
  color:white;
  background:#132338;
}

[data-testid="stMetricValue"] { color:#eef6ff; }

hr { border-color:#1b2a3e; }

@media (max-width: 900px) {
  .pipeline { grid-template-columns: 1fr; }
  .pipeline-step:after { display:none; }
  .title { font-size:2.3rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def pct(value):
    if value is None:
        return "—"
    return f"{float(value) * 100:.1f}%"


def risk_pct(value):
    return pct(value)


def decision_meta(action):
    action = (action or "").lower()
    if action == "allow":
        return "decision-allow", "ALLOW", "Low impersonation risk"
    if action == "verify":
        return "decision-verify", "VERIFY IDENTITY", "Independent verification recommended"
    return "decision-escalate", "ESCALATE", "High-risk response recommended"


def safe_json(response):
    try:
        return response.json()
    except ValueError:
        return None


def analyze(uploaded_file):
    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            uploaded_file.type or "application/octet-stream",
        )
    }
    response = requests.post(f"{API_URL}/analyze", files=files, timeout=180)
    response.raise_for_status()
    return safe_json(response)


# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

st.markdown(
    """
<div class="hero">
  <div class="brand-row">
    <div class="brand-mark">🛡️</div>
    <div>
      <div class="eyebrow">Voice security intelligence</div>
      <div class="title">VoiceCloneGuard</div>
    </div>
  </div>
  <div class="subtitle">
    AI-powered voice authenticity screening that turns acoustic evidence into a proportionate security response.
  </div>
</div>
""",
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# ENGINE STATUS + PIPELINE
# -----------------------------------------------------------------------------

health_ok = False
health_data = {}
try:
    r = requests.get(f"{API_URL}/health", timeout=5)
    r.raise_for_status()
    health_data = r.json()
    health_ok = bool(health_data.get("model_connected"))
except requests.RequestException:
    health_ok = False

if health_ok:
    st.markdown('<div class="status"><span class="status-dot"></span>DETECTION ENGINE ONLINE</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status" style="border-color:rgba(255,189,74,.25);background:rgba(255,189,74,.06);color:#ffd88c"><span class="status-dot" style="background:#ffbd4a"></span>API CONNECTION REQUIRED</div>', unsafe_allow_html=True)

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-head"><div><div class="section-title">How the guard analyzes a voice</div><div class="section-copy">From raw audio to an operational security decision.</div></div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="card">
  <div class="pipeline">
    <div class="pipeline-step"><div class="pipeline-num">01</div><div class="pipeline-name">Audio Input</div><div class="pipeline-desc">Upload speech samples</div></div>
    <div class="pipeline-step"><div class="pipeline-num">02</div><div class="pipeline-name">Normalize</div><div class="pipeline-desc">Decode + 16 kHz mono</div></div>
    <div class="pipeline-step"><div class="pipeline-num">03</div><div class="pipeline-name">Acoustic Analysis</div><div class="pipeline-desc">MFCC + spectral features</div></div>
    <div class="pipeline-step"><div class="pipeline-num">04</div><div class="pipeline-name">Rolling Risk</div><div class="pipeline-desc">Temporal evidence fusion</div></div>
    <div class="pipeline-step"><div class="pipeline-num">05</div><div class="pipeline-name">Security Action</div><div class="pipeline-desc">Allow / verify / escalate</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# LIVE STATE METRICS
# -----------------------------------------------------------------------------

last_result = st.session_state.get("last_result")

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-head"><div><div class="section-title">Security overview</div><div class="section-copy">Current analysis state.</div></div></div>',
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)

final = last_result.get("final", {}) if isinstance(last_result, dict) else {}

with m1:
    value = pct(final.get("spoof_probability"))
    st.markdown(f'<div class="card metric"><div class="metric-label">AI likelihood</div><div class="metric-value {"empty-value" if value == "—" else ""}">{value}</div><div class="metric-note">Synthetic-voice probability</div></div>', unsafe_allow_html=True)
with m2:
    value = risk_pct(final.get("risk_score"))
    st.markdown(f'<div class="card metric"><div class="metric-label">Risk score</div><div class="metric-value {"empty-value" if value == "—" else ""}">{value}</div><div class="metric-note">Temporal + policy fusion</div></div>', unsafe_allow_html=True)
with m3:
    value = pct(final.get("confidence"))
    st.markdown(f'<div class="card metric"><div class="metric-label">Decision confidence</div><div class="metric-value {"empty-value" if value == "—" else ""}">{value}</div><div class="metric-note">Uncertainty-aware score</div></div>', unsafe_allow_html=True)
with m4:
    value = str(last_result.get("windows_analyzed", "—")) if isinstance(last_result, dict) else "—"
    st.markdown(f'<div class="card metric"><div class="metric-label">Windows analyzed</div><div class="metric-value {"empty-value" if value == "—" else ""}">{value}</div><div class="metric-note">4 s windows · 1 s hop</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# INPUT
# -----------------------------------------------------------------------------

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-head"><div><div class="section-title">Analyze a voice sample</div><div class="section-copy">Test the complete detection and risk pipeline.</div></div></div>',
    unsafe_allow_html=True,
)

with st.container():
    st.markdown('<div class="card upload-card">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Upload audio",
        type=["wav", "flac", "mp3", "ogg", "m4a", "aac", "mpeg", "mpg"],
        help="Supported: WAV, FLAC, MP3, OGG, M4A, AAC, MPEG, MPG.",
        label_visibility="collapsed",
    )
    col_a, col_b = st.columns([1, 3])
    with col_a:
        analyze_clicked = st.button("Analyze voice", use_container_width=True, disabled=uploaded is None)
    with col_b:
        st.markdown('<div class="tiny">Audio is processed temporarily for analysis. The prototype does not use raw audio as an application event-log payload.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if analyze_clicked and uploaded is not None:
    with st.spinner("Analyzing acoustic evidence…"):
        try:
            st.session_state.last_result = analyze(uploaded)
            st.session_state.last_filename = uploaded.name
            st.session_state.last_analyzed_at = datetime.now().strftime("%d %b %Y, %H:%M:%S")
            st.rerun()
        except requests.HTTPError as exc:
            detail = "The API rejected the request."
            if exc.response is not None:
                body = safe_json(exc.response)
                if isinstance(body, dict) and body.get("detail"):
                    detail = str(body["detail"])
            st.error(detail)
        except requests.RequestException as exc:
            st.error(f"Could not reach the VoiceCloneGuard API: {exc}")
        except Exception as exc:
            st.error(f"Unexpected analysis error: {exc}")

st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# RESULTS
# -----------------------------------------------------------------------------

if last_result:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-head"><div><div class="section-title">Analysis result</div><div class="section-copy">Evidence from the latest audio sample.</div></div></div>',
        unsafe_allow_html=True,
    )

    action = final.get("action", "verify")
    card_cls, action_label, action_sub = decision_meta(action)

    left, right = st.columns([1.05, 1.8])
    with left:
        st.markdown(
            f"""
<div class="decision {card_cls}">
  <div class="decision-kicker">Security decision</div>
  <div class="decision-title">{action_label}</div>
  <div class="decision-sub">{action_sub}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        filename = last_result.get("filename", st.session_state.get("last_filename", "Audio sample"))
        duration = last_result.get("duration_seconds", 0)
        model_type = last_result.get("model_type", "Unknown")
        st.markdown(
            f"""
<div class="card" style="margin-top:12px">
  <div class="tiny">FILE</div><div style="font-weight:750;margin-top:3px">{filename}</div>
  <div style="height:10px"></div>
  <div class="tiny">DURATION</div><div style="font-weight:750;margin-top:3px">{float(duration):.2f} sec</div>
  <div style="height:10px"></div>
  <div class="tiny">MODEL</div><div style="font-weight:750;margin-top:3px">{model_type}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with right:
        a, b, c = st.columns(3)
        with a:
            st.metric("AI likelihood", pct(final.get("spoof_probability")))
        with b:
            st.metric("Risk score", pct(final.get("risk_score")))
        with c:
            st.metric("Confidence", pct(final.get("confidence")))

        windows = last_result.get("windows", [])
        if windows:
            timeline = pd.DataFrame(
                {
                    "Window": [f'{w.get("start_seconds", 0):.1f}s' for w in windows],
                    "AI likelihood": [float(w.get("spoof_probability", 0)) for w in windows],
                    "Risk": [float(w.get("risk_score", 0)) for w in windows],
                }
            ).set_index("Window")
            st.markdown("**Rolling evidence timeline**")
            st.line_chart(timeline, height=230)

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    ev_left, ev_right = st.columns(2)
    with ev_left:
        st.markdown("**Why the guard responded this way**")
        reasons = final.get("reasons") or []
        explanation = final.get("explanation") or []
        items = reasons or explanation or ["No additional evidence was returned."]
        for item in items:
            st.markdown(f'<div class="evidence">{item}</div>', unsafe_allow_html=True)

    with ev_right:
        st.markdown("**Security interpretation**")
        if action == "allow":
            message = "Current evidence remains below the verification threshold. Continue normal controls."
        elif action == "verify":
            message = "The signal is elevated enough to require an independent identity check before a sensitive action."
        else:
            message = "The risk policy indicates a high-risk state. Route to an established human or organizational escalation process."
        st.markdown(f'<div class="card"><div style="color:#dbe6f4;line-height:1.55">{message}</div><div class="tiny" style="margin-top:10px">A model score is evidence, not proof of identity.</div></div>', unsafe_allow_html=True)

    with st.expander("Window-level evidence"):
        if windows:
            table = pd.DataFrame(windows)
            keep = [c for c in ["start_seconds", "end_seconds", "spoof_probability", "risk_score", "confidence", "action"] if c in table.columns]
            if keep:
                table = table[keep].copy()
                for c in ["spoof_probability", "risk_score", "confidence"]:
                    if c in table.columns:
                        table[c] = (table[c] * 100).round(1).astype(str) + "%"
                table.columns = [c.replace("_", " ").title() for c in table.columns]
                st.dataframe(table, use_container_width=True, hide_index=True)

    if st.session_state.get("last_analyzed_at"):
        st.caption(f"Analyzed {st.session_state.last_analyzed_at}")

    st.markdown('</div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# PRODUCT / SECURITY NOTES
# -----------------------------------------------------------------------------

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown(
    '<div class="section-head"><div><div class="section-title">Security controls built into the prototype</div><div class="section-copy">Designed for a defensive workflow rather than a bare classifier.</div></div></div>',
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)
for col, icon, title, desc in [
    (c1, "🎙️", "Rich acoustic analysis", "MFCC, dynamics, spectral and energy statistics."),
    (c2, "⏱️", "Rolling evidence", "Overlapping windows reduce single-frame decisions."),
    (c3, "🛡️", "Risk-aware response", "Scores become allow, verify or escalate actions."),
    (c4, "🔐", "Privacy-first handling", "Temporary processing with metadata-oriented evidence."),
]:
    with col:
        st.markdown(f'<div class="card" style="height:100%"><div style="font-size:1.4rem">{icon}</div><div style="font-weight:800;margin-top:8px">{title}</div><div class="tiny" style="margin-top:6px">{desc}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown(
    """
<div style="margin-top:34px;padding-top:18px;border-top:1px solid #18263a;color:#61748d;font-size:.73rem;line-height:1.5">
  VoiceCloneGuard is a research/demo prototype. Detection results should be treated as risk signals and combined with independent verification for consequential decisions.
</div>
""",
    unsafe_allow_html=True,
)
