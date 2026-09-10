"""
VOICE CLONING GUARD — Detection Console
Industrial-style Streamlit frontend for the Render-hosted detection API.
"""

import time
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────
API_BASE_URL = "https://voice-cloning-guard.onrender.com"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
PREDICT_ENDPOINT = f"{API_BASE_URL}/predict"  # adjust if your route differs

st.set_page_config(
    page_title="VOICE CLONING GUARD // CONSOLE",
    page_icon="⚠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# INDUSTRIAL THEME (CSS)
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

    html, body, [class*="css"]  {
        font-family: 'JetBrains Mono', monospace;
    }

    .stApp {
        background-color: #14161a;
        background-image:
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
        background-size: 28px 28px;
        color: #e6e6e6;
    }

    /* Header bar */
    .console-header {
        border: 1px solid #3a3d42;
        border-left: 6px solid #ff9500;
        background: linear-gradient(90deg, #1c1f24 0%, #16181c 100%);
        padding: 18px 22px;
        margin-bottom: 24px;
    }
    .console-header h1 {
        font-size: 22px;
        letter-spacing: 3px;
        margin: 0;
        color: #ff9500;
        font-weight: 800;
        text-transform: uppercase;
    }
    .console-header p {
        margin: 4px 0 0 0;
        color: #8a8f98;
        font-size: 12px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    /* Status panel */
    .status-panel {
        border: 1px solid #3a3d42;
        background: #1a1c20;
        padding: 14px 18px;
        margin-bottom: 18px;
        display: flex;
        justify-content: space-between;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        color: #b8bcc4;
    }

    .led {
        display: inline-block;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        margin-right: 6px;
        vertical-align: middle;
    }
    .led-green { background: #34d399; box-shadow: 0 0 8px #34d39988; }
    .led-red { background: #f87171; box-shadow: 0 0 8px #f8717188; }
    .led-amber { background: #ff9500; box-shadow: 0 0 8px #ff950088; }

    /* Panel boxes */
    .panel {
        border: 1px solid #3a3d42;
        background: #1a1c20;
        padding: 20px;
        margin-bottom: 18px;
    }
    .panel-title {
        font-size: 12px;
        letter-spacing: 2px;
        color: #ff9500;
        text-transform: uppercase;
        margin-bottom: 14px;
        border-bottom: 1px solid #3a3d42;
        padding-bottom: 8px;
    }

    /* Verdict block */
    .verdict-box {
        border: 2px solid;
        padding: 22px;
        text-align: center;
        margin-top: 10px;
    }
    .verdict-authentic {
        border-color: #34d399;
        background: rgba(52, 211, 153, 0.08);
        color: #34d399;
    }
    .verdict-cloned {
        border-color: #f87171;
        background: rgba(248, 113, 113, 0.08);
        color: #f87171;
    }
    .verdict-unknown {
        border-color: #ff9500;
        background: rgba(255, 149, 0, 0.08);
        color: #ff9500;
    }
    .verdict-label {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: 3px;
        text-transform: uppercase;
    }
    .verdict-sub {
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 6px;
        opacity: 0.8;
    }

    /* Metric readouts */
    .readout {
        border: 1px solid #3a3d42;
        background: #16181c;
        padding: 10px 14px;
        text-align: center;
    }
    .readout-value {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }
    .readout-label {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: #8a8f98;
        text-transform: uppercase;
        margin-top: 4px;
    }

    div.stButton > button {
        background: #ff9500;
        color: #14161a;
        border: none;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
        padding: 10px 24px;
        border-radius: 2px;
    }
    div.stButton > button:hover {
        background: #ffab33;
        color: #14161a;
    }

    section[data-testid="stSidebar"] {
        background: #16181c;
        border-right: 1px solid #3a3d42;
    }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #14161a; }
    ::-webkit-scrollbar-thumb { background: #3a3d42; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="console-header">
        <h1>⚠ Voice Cloning Guard</h1>
        <p>Synthetic Speech Detection Console // Rich-Feature Random Forest Engine</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# BACKEND STATUS CHECK
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def check_health():
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=10)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)

healthy, health_data = check_health()

status_col1, status_col2 = st.columns([3, 1])
with status_col1:
    if healthy:
        led = '<span class="led led-green"></span>'
        text = f"BACKEND ONLINE — MODEL: {health_data.get('model_type', 'N/A')}"
    else:
        led = '<span class="led led-red"></span>'
        text = "BACKEND UNREACHABLE — CHECK RENDER SERVICE"
    st.markdown(
        f'<div class="status-panel"><div>{led}{text}</div>'
        f'<div>{API_BASE_URL}</div></div>',
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# SIDEBAR — SYSTEM INFO
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="panel-title">System Parameters</div>', unsafe_allow_html=True)
    if healthy:
        st.markdown(f"**Feature count:** {health_data.get('feature_count', '—')}")
        st.markdown(f"**Feature version:** {health_data.get('feature_version', '—')}")
        st.markdown(f"**Training samples:** {health_data.get('training_sample_count', '—')}")
        st.markdown(f"**Window:** {health_data.get('window_seconds', '—')}s / hop {health_data.get('hop_seconds', '—')}s")
        formats = health_data.get("supported_formats", [])
        st.markdown(f"**Formats:** {', '.join(formats) if formats else '—'}")
    else:
        st.warning("No telemetry — backend offline.")

    st.markdown("---")
    if st.button("↻ Refresh Status"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# MAIN — UPLOAD & ANALYZE
# ─────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Audio Input</div>', unsafe_allow_html=True)

    supported = health_data.get("supported_formats", ["wav", "mp3", "flac", "m4a"]) if healthy else ["wav", "mp3", "flac", "m4a"]
    uploaded_file = st.file_uploader(
        "Upload audio sample",
        type=supported,
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.audio(uploaded_file)

    analyze = st.button("▶ RUN DETECTION", disabled=(uploaded_file is None or not healthy))
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Detection Result</div>', unsafe_allow_html=True)

    result_placeholder = st.empty()
    if "last_result" not in st.session_state:
        result_placeholder.info("Awaiting sample. Upload audio and run detection.")
    st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# RUN DETECTION
# ─────────────────────────────────────────────────────────────
def parse_result(data: dict):
    """Best-effort parsing across likely response shapes."""
    label = (
        data.get("prediction")
        or data.get("label")
        or data.get("result")
        or ("cloned" if data.get("is_cloned") else "authentic" if "is_cloned" in data else None)
    )
    confidence = (
        data.get("confidence")
        or data.get("probability")
        or data.get("score")
    )
    return label, confidence


if uploaded_file and analyze:
    with st.spinner("PROCESSING SAMPLE — EXTRACTING FEATURES..."):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            start = time.time()
            resp = requests.post(PREDICT_ENDPOINT, files=files, timeout=60)
            elapsed = time.time() - start
            resp.raise_for_status()
            data = resp.json()
            st.session_state["last_result"] = (data, elapsed)
        except Exception as e:
            st.session_state["last_result"] = ({"error": str(e)}, 0)

if "last_result" in st.session_state:
    data, elapsed = st.session_state["last_result"]

    with col_right:
        if "error" in data:
            result_placeholder.error(f"REQUEST FAILED: {data['error']}")
        else:
            label, confidence = parse_result(data)
            label_str = str(label).lower() if label else "unknown"

            if "clone" in label_str or "fake" in label_str or "synthetic" in label_str:
                verdict_class = "verdict-cloned"
                verdict_text = "SYNTHETIC / CLONED"
            elif "authentic" in label_str or "real" in label_str or "human" in label_str:
                verdict_class = "verdict-authentic"
                verdict_text = "AUTHENTIC"
            else:
                verdict_class = "verdict-unknown"
                verdict_text = label_str.upper() if label else "INCONCLUSIVE"

            conf_display = f"{confidence * 100:.1f}%" if isinstance(confidence, (int, float)) and confidence <= 1 else (
                f"{confidence:.1f}%" if isinstance(confidence, (int, float)) else "—"
            )

            with result_placeholder.container():
                st.markdown(
                    f"""
                    <div class="verdict-box {verdict_class}">
                        <div class="verdict-label">{verdict_text}</div>
                        <div class="verdict-sub">Detection Verdict</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.write("")
                r1, r2 = st.columns(2)
                with r1:
                    st.markdown(
                        f'<div class="readout"><div class="readout-value">{conf_display}</div>'
                        f'<div class="readout-label">Confidence</div></div>',
                        unsafe_allow_html=True,
                    )
                with r2:
                    st.markdown(
                        f'<div class="readout"><div class="readout-value">{elapsed:.2f}s</div>'
                        f'<div class="readout-label">Processing Time</div></div>',
                        unsafe_allow_html=True,
                    )

                with st.expander("Raw response"):
                    st.json(data)

st.markdown(
    """
    <div style="margin-top: 40px; text-align: center; color: #4a4d52; font-size: 11px; letter-spacing: 1px;">
        VOICE CLONING GUARD // SIH26104 // BACKEND: RENDER.COM
    </div>
    """,
    unsafe_allow_html=True,
)
