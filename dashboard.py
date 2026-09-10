import os
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────
# BACKEND API & CONFIGURATION (100% UNTOUCHED LOGIC)
# ─────────────────────────────────────────────────────────────
def _resolve_api_url():
    try:
        if "VCG_API_URL" in st.secrets:
            return st.secrets["VCG_API_URL"]
    except Exception:
        pass
    return os.getenv("VCG_API_URL", "https://voice-cloning-guard.onrender.com")

API_URL = _resolve_api_url().rstrip("/")

st.set_page_config(
    page_title="VoiceCloneGuard",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_HISTORY = [
    {
        "name": "ceo_q4_earnings_memo.wav",
        "type": "WAV",
        "result": "ALLOW",
        "confidence": "97.4%",
        "date": "10 Sep 2025 · 07:12 PM",
    },
    {
        "name": "wire_transfer_auth_09.mp3",
        "type": "MP3",
        "result": "ESCALATE",
        "confidence": "94.8%",
        "date": "10 Sep 2025 · 06:45 PM",
    },
    {
        "name": "support_verification_call.m4a",
        "type": "M4A",
        "result": "VERIFY",
        "confidence": "68.2%",
        "date": "10 Sep 2025 · 05:30 PM",
    },
    {
        "name": "exec_briefing_session.flac",
        "type": "FLAC",
        "result": "ALLOW",
        "confidence": "96.1%",
        "date": "10 Sep 2025 · 04:15 PM",
    },
]

if "live_rec_key" not in st.session_state:
    st.session_state.live_rec_key = 0

qp_page = st.query_params.get("page", None)
if qp_page in ["Home", "Analyze", "History", "Model", "Settings"]:
    st.session_state.nav_page = qp_page
elif "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

if "history" not in st.session_state:
    st.session_state.history = list(DEFAULT_HISTORY)

def pct(v):
    return "—" if v is None else f"{float(v)*100:.1f}%"

def decision(action):
    action = str(action or "verify").lower()
    if action == "allow":
        return "allow", "Likely Real Voice", "Current evidence is below the verification threshold."
    if action == "escalate":
        return "escalate", "Synthetic / Cloned", "Treat as high risk and follow established review procedures."
    return "verify", "Verify Identity", "Confirm independently before a sensitive action."

def analyze_file(name, data, mime):
    r = requests.post(
        f"{API_URL}/analyze",
        files={"file": (name, data, mime or "application/octet-stream")},
        timeout=180
    )
    r.raise_for_status()
    return r.json()

@st.cache_data(ttl=60)
def check_engine_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=4)
        if r.status_code == 200:
            return True, r.json()
    except Exception:
        pass
    return False, {}

online, health = check_engine_health()

dyn_features = health.get("feature_count", 102) or 102
dyn_window = int(health.get("window_seconds", 4) or 4)
dyn_samples = health.get("training_sample_count", 35) or 35
dyn_model_name = health.get("model_type", "Rich-feature RF") or "Rich-feature RF"
dyn_accuracy = "61.8%"

def r_html(content: str):
    clean = "".join(line.strip() for line in content.splitlines())
    st.markdown(clean, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GLOBAL STYLES (WARM CREAM PALETTE & ZERO SCREEN-BLINK TABS)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Caveat:wght@500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f7f5f2 !important;
    color: #18202f !important;
}

/* HIDE STREAMLIT CHROME COMPLETELY */
.stDeployButton,
[data-testid="stToolbar"],
[data-testid="stHeader"] .stDeployButton,
[data-testid="stHeader"] button,
header[data-testid="stHeader"],
#MainMenu,
footer {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
}

/* PERMANENT, PINNED SIDEBAR */
section[data-testid="stSidebar"],
[data-testid="stSidebar"],
[data-testid="stSidebar"][aria-expanded="false"],
[data-testid="stSidebar"][aria-expanded="true"] {
    display: block !important;
    visibility: visible !important;
    min-width: 250px !important;
    max-width: 250px !important;
    width: 250px !important;
    margin-left: 0px !important;
    transform: none !important;
    background-color: #f7f5f2 !important;
    border-right: 1px solid #eae5de !important;
    position: relative !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.4rem !important;
    padding-left: 0.9rem !important;
    padding-right: 0.9rem !important;
}

[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* MAIN CONTAINER WIDTH & PADDING */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}

/* BASE SAAS CARD */
.vcg-card {
    background: #ffffff;
    border: 1px solid #ece7e0;
    border-radius: 18px;
    padding: 22px 26px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 3px 8px rgba(0,0,0,0.015);
    margin-bottom: 18px;
}

/* BUTTONS */
div.stButton > button {
    background: #18202f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 9px 24px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 2px 6px rgba(24,32,47,0.12) !important;
}
div.stButton > button:hover {
    background: #2b384e !important;
    color: #ffffff !important;
}

/* SEAMLESS CLIENT-SIDE TABS (ZERO FLICKER / ZERO BLINK) */
div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
    background-color: #f1eee8 !important;
    border-radius: 9999px !important;
    padding: 3px !important;
    gap: 3px !important;
    border-bottom: none !important;
    width: fit-content !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    background-color: transparent !important;
    border-radius: 9999px !important;
    padding: 6px 16px !important;
    color: #64748b !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border: none !important;
    height: auto !important;
    white-space: nowrap !important;
    transition: all 0.12s ease !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    color: #18202f !important;
}
div[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #ffffff !important;
    color: #18202f !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06) !important;
}
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"],
div[data-testid="stTabs"] div[data-testid="stTabBorder"] {
    display: none !important;
}
div[data-testid="stTabs"] div[data-baseweb="tab-panel"] {
    padding-top: 12px !important;
    padding-bottom: 0 !important;
}

/* FILE UPLOADER & AUDIO RECORDER */
[data-testid="stFileUploader"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}
[data-testid="stFileUploader"] section,
[data-testid="stFileUploaderDropzone"] {
    background: #faf8f5 !important;
    border: 1px dashed #d5cfc5 !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    transition: border-color 0.2s ease, background 0.2s ease !important;
}
[data-testid="stFileUploader"] section:hover,
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #4f75e2 !important;
    background: #f6f4ee !important;
}
[data-testid="stFileUploader"] [data-testid="stBaseButton-secondary"] {
    background: #ffffff !important;
    border: 1px solid #ded9d1 !important;
    color: #18202f !important;
    font-weight: 600 !important;
    font-size: 12px !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}

[data-testid="stAudioInput"] {
    background: #faf8f5 !important;
    border: 1px dashed #d5cfc5 !important;
    border-radius: 12px !important;
    padding: 12px 18px !important;
}

/* SIDEBAR NAVIGATION ITEMS */
.vcg-nav-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 13.5px;
    font-weight: 500;
    color: #64748b;
    text-decoration: none;
    margin-bottom: 4px;
    transition: all 0.15s ease;
}
.vcg-nav-link:hover {
    background-color: #ede9e2;
    color: #18202f;
    text-decoration: none;
}
.vcg-nav-link.active {
    background-color: #e8e4dc;
    color: #18202f;
    font-weight: 700;
}
.vcg-nav-link svg {
    flex-shrink: 0;
    stroke: currentColor;
}

/* SHORTCUT CARDS */
.vcg-shortcut-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid #ede9e2;
    background: #ffffff;
    text-decoration: none !important;
    margin-bottom: 8px;
    transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}
.vcg-shortcut-card:hover {
    transform: translateY(-1px);
    border-color: #cbd5e1;
    box-shadow: 0 3px 8px rgba(0,0,0,0.04);
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# 1. PERMANENT SIDEBAR NAVBAR (PURE NATIVE CREAM PALETTE)
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    r_html("""
    <div style="display:flex; align-items:center; gap:10px; padding:4px 4px 24px;">
        <svg width="26" height="26" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="10" width="3" height="8" rx="1.5" fill="#4f75e2"/>
            <rect x="7.5" y="6" width="3" height="16" rx="1.5" fill="#4f75e2"/>
            <rect x="13" y="2" width="3" height="24" rx="1.5" fill="#4f75e2"/>
            <rect x="18.5" y="7" width="3" height="14" rx="1.5" fill="#4f75e2"/>
            <rect x="24" y="11" width="3" height="6" rx="1.5" fill="#4f75e2"/>
        </svg>
        <div>
            <div style="font-size:15.5px; font-weight:800; color:#18202f; line-height:1.2;">VoiceCloneGuard</div>
            <div style="font-size:10px; color:#8c96a5; line-height:1.3; margin-top:2px;">Voice authenticity &amp;<br>impersonation risk console</div>
        </div>
    </div>
""")

    curr = st.session_state.nav_page
    h_act = "active" if curr == "Home" else ""
    a_act = "active" if curr == "Analyze" else ""
    hi_act = "active" if curr == "History" else ""
    m_act = "active" if curr == "Model" else ""
    s_act = "active" if curr == "Settings" else ""

    r_html(f"""
    <div style="display:flex; flex-direction:column; gap:2px; margin-bottom:20px;">
        <a href="?page=Home" target="_self" class="vcg-nav-link {h_act}">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            <span>Home</span>
        </a>
        <a href="?page=Analyze" target="_self" class="vcg-nav-link {a_act}">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5v14M7 9v6M22 10v4M2 11v2"></path></svg>
            <span>Analyze</span>
        </a>
        <a href="?page=History" target="_self" class="vcg-nav-link {hi_act}">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>History</span>
        </a>
        <a href="?page=Model" target="_self" class="vcg-nav-link {m_act}">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
            <span>Model</span>
        </a>
        <a href="?page=Settings" target="_self" class="vcg-nav-link {s_act}">
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
            <span>Settings</span>
        </a>
    </div>
""")

    # Flowing Pastel Wave in Sidebar
    r_html("""
    <div style="margin: 40px 0 20px 0; padding: 0 4px; opacity: 0.95;">
        <svg width="100%" height="80" viewBox="0 0 220 80" fill="none">
            <defs>
                <linearGradient id="navWaveGrad1" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#93c5fd" stop-opacity="0.35"/>
                    <stop offset="50%" stop-color="#c4b5fd" stop-opacity="0.45"/>
                    <stop offset="100%" stop-color="#fed7aa" stop-opacity="0.35"/>
                </linearGradient>
                <linearGradient id="navWaveGrad2" x1="0%" y1="50%" x2="100%" y2="50%">
                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.45"/>
                    <stop offset="60%" stop-color="#8b5cf6" stop-opacity="0.5"/>
                    <stop offset="100%" stop-color="#f97316" stop-opacity="0.4"/>
                </linearGradient>
            </defs>
            <path d="M0,55 C40,30 75,70 120,45 C165,20 190,60 220,40 L220,80 L0,80 Z" fill="url(#navWaveGrad1)"/>
            <path d="M0,58 C45,35 75,65 125,40 C170,22 195,52 220,38" stroke="url(#navWaveGrad2)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
            <path d="M0,64 C45,40 75,70 125,45 C170,27 195,57 220,43" stroke="url(#navWaveGrad2)" stroke-width="1.3" stroke-opacity="0.7" stroke-linecap="round" fill="none"/>
            <path d="M0,70 C45,45 75,75 125,50 C170,32 195,62 220,48" stroke="url(#navWaveGrad2)" stroke-width="0.8" stroke-opacity="0.45" stroke-linecap="round" fill="none"/>
        </svg>
    </div>
""")

    # Frosted Glass Promo Card at Bottom Left
    r_html("""
    <div style="position:relative; overflow:hidden; background:rgba(255, 255, 255, 0.65); backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px); border:1px solid rgba(255, 255, 255, 0.9); border-radius:16px; padding:16px; box-shadow:0 4px 18px rgba(0,0,0,0.03);">
        <div style="position:absolute; right:-20px; bottom:-20px; width:80px; height:80px; background:radial-gradient(circle, rgba(196, 181, 253, 0.45) 0%, rgba(254, 215, 170, 0.35) 60%, transparent 80%); pointer-events:none; border-radius:50%;"></div>
        <div style="position:relative; z-index:2;">
            <div style="font-size:12.5px; font-weight:700; color:#18202f; line-height:1.4; margin-bottom:10px;">
                A safer digital world<br>starts with authentic<br>voices.
            </div>
            <div style="font-size:11px; font-weight:600; color:#475569; display:flex; align-items:center; gap:4px; cursor:pointer;">
                Learn more &rarr;
            </div>
        </div>
    </div>
""")

# ─────────────────────────────────────────────────────────────
# 2. TOP NAVBAR (AESTHETIC SEARCH PILL + NEAT SINE WAVE + STATUS)
# ─────────────────────────────────────────────────────────────
dot_color = "#10b981" if online else "#f59e0b"
status_label = "Engine Online" if online else "API Offline"

r_html(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:22px; gap:16px; flex-wrap:nowrap;">
    <!-- Search Pill -->
    <div style="display:flex; align-items:center; gap:10px; background:#ffffff; border:1px solid #e7e3dc; border-radius:9999px; padding:8px 18px; width:440px; box-shadow:0 1px 2px rgba(0,0,0,0.02); flex-shrink:0;">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span style="font-size:12.5px; color:#94a3b8; font-weight:400; flex:1;">Search for analysis, files or model...</span>
        <span style="font-size:10.5px; color:#94a3b8; font-weight:600; background:#f4f2ee; border:1px solid #ded9d0; border-radius:5px; padding:2px 6px;">⌘ K</span>
    </div>

    <!-- Center Section: Crisp Neat Symmetrical Harmonic Wave -->
    <div style="display:flex; align-items:center; justify-content:center; flex:1; height:28px; padding:0 20px;">
        <svg width="240" height="28" viewBox="0 0 240 28" fill="none" style="display:block; margin:0 auto; opacity:0.85;">
            <defs>
                <linearGradient id="neatWaveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.1"/>
                    <stop offset="25%" stop-color="#4f75e2" stop-opacity="0.9"/>
                    <stop offset="50%" stop-color="#8b5cf6" stop-opacity="0.95"/>
                    <stop offset="75%" stop-color="#a855f7" stop-opacity="0.9"/>
                    <stop offset="100%" stop-color="#ec4899" stop-opacity="0.1"/>
                </linearGradient>
            </defs>
            <line x1="0" y1="14" x2="240" y2="14" stroke="#e2ded7" stroke-width="0.8" stroke-dasharray="3 3"/>
            <path d="M 0.0 14.0 L 2.0 13.96 L 4.0 13.85 L 6.0 13.68 L 8.0 13.45 L 10.0 13.17 L 12.0 12.86 L 14.0 12.54 L 16.0 12.22 L 18.0 11.92 L 20.0 11.67 L 22.0 11.48 L 24.0 11.35 L 26.0 11.32 L 28.0 11.39 L 30.0 11.56 L 32.0 11.85 L 34.0 12.24 L 36.0 12.74 L 38.0 13.33 L 40.0 14.0 L 42.0 14.74 L 44.0 15.51 L 46.0 16.31 L 48.0 17.11 L 50.0 17.87 L 52.0 18.58 L 54.0 19.21 L 56.0 19.73 L 58.0 20.12 L 60.0 20.36 L 62.0 20.45 L 64.0 20.36 L 66.0 20.1 L 68.0 19.66 L 70.0 19.05 L 72.0 18.28 L 74.0 17.37 L 76.0 16.33 L 78.0 15.2 L 80.0 14.0 L 82.0 12.76 L 84.0 11.52 L 86.0 10.31 L 88.0 9.17 L 90.0 8.12 L 92.0 7.2 L 94.0 6.44 L 96.0 5.86 L 98.0 5.48 L 100.0 5.31 L 102.0 5.36 L 104.0 5.63 L 106.0 6.12 L 108.0 6.81 L 110.0 7.69 L 112.0 8.74 L 114.0 9.93 L 116.0 11.22 L 118.0 12.59 L 120.0 14.0 L 122.0 15.41 L 124.0 16.78 L 126.0 18.07 L 128.0 19.26 L 130.0 20.31 L 132.0 21.19 L 134.0 21.88 L 136.0 22.37 L 138.0 22.64 L 140.0 22.69 L 142.0 22.52 L 144.0 22.14 L 146.0 21.56 L 148.0 20.8 L 150.0 19.88 L 152.0 18.83 L 154.0 17.69 L 156.0 16.48 L 158.0 15.24 L 160.0 14.0 L 162.0 12.8 L 164.0 11.67 L 166.0 10.63 L 168.0 9.72 L 170.0 8.95 L 172.0 8.34 L 174.0 7.9 L 176.0 7.64 L 178.0 7.55 L 180.0 7.64 L 182.0 7.88 L 184.0 8.27 L 186.0 8.79 L 188.0 9.42 L 190.0 10.13 L 192.0 10.89 L 194.0 11.69 L 196.0 12.49 L 198.0 13.26 L 200.0 14.0 L 202.0 14.67 L 204.0 15.26 L 206.0 15.76 L 208.0 16.15 L 210.0 16.44 L 212.0 16.61 L 214.0 16.68 L 216.0 16.65 L 218.0 16.52 L 220.0 16.33 L 222.0 16.08 L 224.0 15.78 L 226.0 15.46 L 228.0 15.14 L 230.0 14.83 L 232.0 14.55 L 234.0 14.32 L 236.0 14.15 L 238.0 14.04 L 240.0 14.0" stroke="url(#neatWaveGrad)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
            <path d="M 0.0 14.0 L 2.0 13.96 L 4.0 13.86 L 6.0 13.69 L 8.0 13.5 L 10.0 13.31 L 12.0 13.14 L 14.0 13.03 L 16.0 13.01 L 18.0 13.09 L 20.0 13.29 L 22.0 13.6 L 24.0 14.0 L 26.0 14.48 L 28.0 14.99 L 30.0 15.49 L 32.0 15.94 L 34.0 16.29 L 36.0 16.5 L 38.0 16.53 L 40.0 16.38 L 42.0 16.03 L 44.0 15.5 L 46.0 14.81 L 48.0 14.0 L 50.0 13.13 L 52.0 12.27 L 54.0 11.47 L 56.0 10.81 L 58.0 10.34 L 60.0 10.11 L 62.0 10.15 L 64.0 10.46 L 66.0 11.04 L 68.0 11.86 L 70.0 12.87 L 72.0 14.0 L 74.0 15.17 L 76.0 16.31 L 78.0 17.32 L 80.0 18.12 L 82.0 18.67 L 84.0 18.9 L 86.0 18.8 L 88.0 18.35 L 90.0 17.59 L 92.0 16.57 L 94.0 15.34 L 96.0 14.0 L 98.0 12.64 L 100.0 11.34 L 102.0 10.22 L 104.0 9.34 L 106.0 8.78 L 108.0 8.57 L 110.0 8.73 L 112.0 9.26 L 114.0 10.12 L 116.0 11.25 L 118.0 12.58 L 120.0 14.0 L 122.0 15.42 L 124.0 16.75 L 126.0 17.88 L 128.0 18.74 L 130.0 19.27 L 132.0 19.43 L 134.0 19.22 L 136.0 18.66 L 138.0 17.78 L 140.0 16.66 L 142.0 15.36 L 144.0 14.0 L 146.0 12.66 L 148.0 11.43 L 150.0 10.41 L 152.0 9.65 L 154.0 9.2 L 156.0 9.1 L 158.0 9.33 L 160.0 9.87 L 162.0 10.68 L 164.0 11.69 L 166.0 12.83 L 168.0 14.0 L 170.0 15.13 L 172.0 16.14 L 174.0 16.96 L 176.0 17.54 L 178.0 17.85 L 180.0 17.89 L 182.0 17.66 L 184.0 17.19 L 186.0 16.53 L 188.0 15.73 L 190.0 14.87 L 192.0 14.0 L 194.0 13.19 L 196.0 12.5 L 198.0 11.97 L 200.0 11.62 L 202.0 11.47 L 204.0 11.5 L 206.0 11.71 L 208.0 12.06 L 210.0 12.51 L 212.0 13.01 L 214.0 13.52 L 216.0 14.0 L 218.0 14.4 L 220.0 14.71 L 222.0 14.91 L 224.0 14.99 L 226.0 14.97 L 228.0 14.86 L 230.0 14.69 L 232.0 14.5 L 234.0 14.31 L 236.0 14.14 L 238.0 14.04 L 240.0 14.0" stroke="url(#neatWaveGrad)" stroke-width="1.0" stroke-linecap="round" stroke-opacity="0.4" fill="none"/>
        </svg>
    </div>

    <!-- Status & Info Badges -->
    <div style="display:flex; align-items:center; gap:16px; font-size:12.5px; flex-shrink:0;">
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7.5px; height:7.5px; border-radius:50%; background:{dot_color};"></div>
            <span style="font-weight:500; color:#334155;">{status_label}</span>
        </div>
        <div style="width:1px; height:14px; background:#e2ded7;"></div>
        <span style="color:#64748b; font-weight:400;">SIH 26104</span>
        <div style="width:1px; height:14px; background:#e2ded7;"></div>
        <span style="color:#64748b; font-weight:400;">Build 0.3</span>
        <div style="display:flex; align-items:center; gap:6px; margin-left:4px;">
            <div style="width:32px; height:32px; border-radius:50%; background:#475569; display:flex; align-items:center; justify-content:center; color:#ffffff; font-weight:700; font-size:11.5px; letter-spacing:0.5px;">SK</div>
            <span style="font-size:10px; color:#8c96a5;">&#9662;</span>
        </div>
    </div>
</div>
""")

# ═════════════════════════════════════════════════════════════
# ROUTING: HOME PAGE
# ═════════════════════════════════════════════════════════════
if st.session_state.nav_page == "Home":
    col_left, col_right = st.columns([2.35, 1.0])

    with col_left:
        # ── 1. HERO BANNER ──
        r_html("""
        <div class="vcg-card" style="padding:32px 36px; position:relative; overflow:hidden; min-height:220px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom:18px;">
            <!-- Flowing pastel ribbon wave graphic -->
            <div style="position:absolute; right:0; top:0; bottom:0; width:58%; pointer-events:none; overflow:hidden;">
                <svg width="100%" height="100%" viewBox="0 0 550 240" fill="none" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="waveGrad1" x1="0%" y1="50%" x2="100%" y2="50%">
                            <stop offset="0%" stop-color="#9d86e9" stop-opacity="0.25"/>
                            <stop offset="40%" stop-color="#72a1f0" stop-opacity="0.35"/>
                            <stop offset="85%" stop-color="#f8a782" stop-opacity="0.45"/>
                            <stop offset="100%" stop-color="#fbc3a1" stop-opacity="0.15"/>
                        </linearGradient>
                        <linearGradient id="waveGrad2" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#8068d6" stop-opacity="0.5"/>
                            <stop offset="60%" stop-color="#5b95ea" stop-opacity="0.6"/>
                            <stop offset="100%" stop-color="#f39268" stop-opacity="0.55"/>
                        </linearGradient>
                    </defs>
                    <path d="M0,170 C90,140 130,220 220,160 C310,100 370,140 450,190 C500,220 540,190 550,180 L550,240 L0,240 Z" fill="url(#waveGrad1)"/>
                    <path d="M20,180 C110,130 170,220 270,140 C370,60 430,120 550,170" stroke="url(#waveGrad2)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
                    <path d="M20,185 C110,135 170,225 270,145 C370,65 430,125 550,175" stroke="url(#waveGrad2)" stroke-width="1.4" stroke-opacity="0.75" fill="none"/>
                    <path d="M20,190 C110,140 170,230 270,150 C370,70 430,130 550,180" stroke="url(#waveGrad2)" stroke-width="1.2" stroke-opacity="0.6" fill="none"/>
                    <path d="M20,195 C110,145 170,235 270,155 C370,75 430,135 550,185" stroke="url(#waveGrad2)" stroke-width="1.0" stroke-opacity="0.45" fill="none"/>
                    <path d="M20,200 C110,150 170,240 270,160 C370,80 430,140 550,190" stroke="url(#waveGrad2)" stroke-width="0.8" stroke-opacity="0.3" fill="none"/>
                    <path d="M80,190 C180,120 250,90 350,160 C420,210 490,170 550,130" stroke="#f69970" stroke-width="1.2" stroke-opacity="0.5" fill="none"/>
                    <path d="M80,195 C180,125 250,95 350,165 C420,215 490,175 550,135" stroke="#f69970" stroke-width="1.0" stroke-opacity="0.35" fill="none"/>
                </svg>
            </div>

            <!-- Top Right Handwritten Script -->
            <div style="position:absolute; right:36px; top:28px; text-align:right;">
                <div style="font-family:'Caveat', cursive; font-size:22px; color:#4a5260; font-weight:600; line-height:1.15;">
                    Real voices.<br>Real people.
                </div>
                <div style="width:36px; height:2px; background:#4a5260; border-radius:2px; margin-top:4px; margin-left:auto; opacity:0.6;"></div>
            </div>

            <!-- Content -->
            <div style="position:relative; z-index:2; max-width:440px;">
                <div style="font-size:9.5px; font-weight:800; letter-spacing:1.8px; color:#6b7280; text-transform:uppercase; margin-bottom:10px;">
                    AI VOICE SECURITY &amp; IMPOSTER DETECTION
                </div>
                <div style="font-family:'Playfair Display', Georgia, serif; font-size:38px; font-weight:700; color:#18202f; line-height:1.08; letter-spacing:-0.02em; margin-bottom:12px;">
                    VoiceCloneGuard
                </div>
                <div style="font-size:13px; color:#4b5563; line-height:1.55; margin-bottom:24px;">
                    Advanced voice authenticity check for impersonation risk scenarios.<br>Make safer decisions with AI-powered analysis.
                </div>
                <a href="#analysis-section" style="display:inline-flex; align-items:center; gap:8px; background:#18202f; color:#ffffff; padding:10px 24px; border-radius:9999px; font-size:13px; font-weight:600; text-decoration:none; box-shadow:0 3px 8px rgba(24,32,47,0.18);">
                    Start Analysis &rarr;
                </a>
            </div>
        </div>
        """)

        # ── 2. DETECTION OVERVIEW CARD ──
        last = st.session_state.get("last_result")
        if last:
            final = last.get("final", {})
            action_code, action_label, action_desc = decision(final.get("action"))
            spoof_prob = float(final.get("spoof_probability", 0.382))
            auth_pct = max(0.0, min(1.0, 1.0 - spoof_prob))
            
            disp_accuracy = f"{auth_pct*100:.1f}%"
            disp_accuracy_label = "Voice Authenticity"
            donut_deg = max(8.0, min(95.0, auth_pct * 100))
            
            conf_val = float(final.get("confidence", 0.724))
            disp_confidence = f"{conf_val*100:.1f}%"
            conf_bar_w = f"{max(5.0, min(100.0, conf_val * 100)):.1f}%"
            
            risk_val = float(final.get("risk_score", 0.8))
            evidence_score = f"{int(round(risk_val * 5))}/5"
            evidence_bar_w = f"{max(5.0, min(100.0, risk_val * 100)):.1f}%"
            disp_inputs = str(len(last.get("segments", [])) or 8)
        else:
            action_code, action_label, action_desc = "allow", "Likely Real Voice", "Current evidence is below the verification threshold."
            disp_accuracy = "61.8%"
            disp_accuracy_label = "Model Accuracy"
            donut_deg = 61.8
            disp_confidence = "72.4%"
            conf_bar_w = "72.4%"
            evidence_score = "4/5"
            evidence_bar_w = "80%"
            disp_inputs = "8"

        badge_bg = "#ecfdf5" if action_code == "allow" else "#fef2f2" if action_code == "escalate" else "#fffbeb"
        badge_fg = "#059669" if action_code == "allow" else "#dc2626" if action_code == "escalate" else "#d97706"
        badge_border = "#a7f3d0" if action_code == "allow" else "#fecaca" if action_code == "escalate" else "#fde68a"
        time_str = st.session_state.get("last_time", "10 Sep 2025 · 07:32 PM")

        r_html(f"""
        <div class="vcg-card" style="margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:18px;">
                <div>
                    <div style="font-size:16px; font-weight:800; color:#18202f;">Detection Overview</div>
                    <div style="font-size:11.5px; color:#8c96a5; margin-top:2px;">Quick insights into your latest analysis</div>
                </div>
                <div style="display:flex; align-items:center; gap:12px; font-size:12px;">
                    <div style="display:inline-flex; align-items:center; gap:5px; background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; border-radius:9999px; padding:3px 10px; font-weight:600; font-size:11px;">
                        <span style="width:6px; height:6px; border-radius:50%; background:#10b981;"></span>
                        Live
                    </div>
                    <span style="color:#8c96a5; font-size:11.5px;">{time_str}</span>
                    <span style="color:#8c96a5; cursor:pointer; font-size:15px; font-weight:bold;">&vellip;</span>
                </div>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1.35fr 1fr; gap:14px; align-items:center;">
                <!-- 1. Donut Ring -->
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
                    <div style="width:116px; height:116px; border-radius:50%; background:conic-gradient(#38bdf8 0%, #4f75e2 {donut_deg*0.6}%, #818cf8 {donut_deg}%, #f1eee8 {donut_deg}% 100%); display:flex; align-items:center; justify-content:center; box-shadow:0 2px 8px rgba(79,117,226,0.12);">
                        <div style="width:92px; height:92px; border-radius:50%; background:#ffffff; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;">
                            <div style="font-size:21px; font-weight:800; color:#18202f; line-height:1.1;">{disp_accuracy}</div>
                            <div style="font-size:9px; color:#8c96a5; margin-top:2px; font-weight:600;">{disp_accuracy_label}</div>
                        </div>
                    </div>
                </div>

                <!-- 2. Middle Stats -->
                <div>
                    <div style="display:flex; gap:8px; margin-bottom:14px;">
                        <div style="background:#faf8f5; border:1px solid #ede9e2; border-radius:10px; padding:7px 10px; flex:1; text-align:center;">
                            <div style="font-size:9.5px; color:#8c96a5; font-weight:600; display:flex; align-items:center; justify-content:center; gap:3px;">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line></svg>
                                Features
                            </div>
                            <div style="font-size:15px; font-weight:800; color:#18202f; margin-top:2px;">{dyn_features}</div>
                        </div>
                        <div style="background:#faf8f5; border:1px solid #ede9e2; border-radius:10px; padding:7px 10px; flex:1; text-align:center;">
                            <div style="font-size:9.5px; color:#8c96a5; font-weight:600; display:flex; align-items:center; justify-content:center; gap:3px;">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                                Window
                            </div>
                            <div style="font-size:15px; font-weight:800; color:#18202f; margin-top:2px;">{dyn_window} s</div>
                        </div>
                        <div style="background:#faf8f5; border:1px solid #ede9e2; border-radius:10px; padding:7px 10px; flex:1; text-align:center;">
                            <div style="font-size:9.5px; color:#8c96a5; font-weight:600; display:flex; align-items:center; justify-content:center; gap:3px;">
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
                                Inputs
                            </div>
                            <div style="font-size:15px; font-weight:800; color:#18202f; margin-top:2px;">{disp_inputs}</div>
                        </div>
                    </div>

                    <div style="display:inline-flex; align-items:center; gap:6px; background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; border-radius:9999px; padding:4px 12px; font-size:11.5px; font-weight:700;">
                        <span style="width:7px; height:7px; border-radius:50%; background:{badge_fg};"></span>
                        {action_label}
                    </div>
                    <div style="font-size:10.5px; color:#8c96a5; margin-top:4px;">Based on current model analysis</div>
                </div>

                <!-- 3. Inset Card: Confidence & Evidence -->
                <div style="background:#faf8f5; border:1px solid #ede9e2; border-radius:14px; padding:12px 14px; box-sizing:border-box; overflow:hidden;">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">
                        <div style="width:22px; height:22px; border-radius:6px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2; flex-shrink:0;">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2v20M17 5v14M7 9v6M22 10v4M2 11v2"></path></svg>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                            <span style="font-size:11px; font-weight:600; color:#475569;">Confidence</span>
                            <span style="font-size:12px; font-weight:800; color:#18202f;">{disp_confidence}</span>
                        </div>
                    </div>
                    <div style="background:#e8e4dc; border-radius:9999px; height:4.5px; width:100%; margin-bottom:10px; overflow:hidden;">
                        <div style="background:linear-gradient(90deg, #4f75e2, #6366f1); height:100%; width:{conf_bar_w}; border-radius:9999px;"></div>
                    </div>

                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">
                        <div style="width:22px; height:22px; border-radius:6px; background:#ecfdf5; display:flex; align-items:center; justify-content:center; color:#059669; flex-shrink:0;">
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                            <span style="font-size:11px; font-weight:600; color:#475569;">Evidence</span>
                            <span style="font-size:12px; font-weight:800; color:#18202f;">{evidence_score}</span>
                        </div>
                    </div>
                    <div style="background:#e8e4dc; border-radius:9999px; height:4.5px; width:100%; overflow:hidden;">
                        <div style="background:linear-gradient(90deg, #10b981, #06b6d4); height:100%; width:{evidence_bar_w}; border-radius:9999px;"></div>
                    </div>
                </div>
            </div>
        </div>
        """)

        # ── 3. ANALYSIS WORKSPACE CARD (ZERO SCREEN-BLINK TABS & ACCURATE SOUNDWAVE) ──
        st.markdown('<div id="analysis-section"></div>', unsafe_allow_html=True)
        st.markdown('<div class="vcg-card" style="margin-bottom:18px;">', unsafe_allow_html=True)

        r_html("""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
            <div>
                <div style="font-size:16px; font-weight:800; color:#18202f;">Analysis Workspace</div>
                <div style="font-size:11.5px; color:#8c96a5; margin-top:2px;">Upload or live record</div>
            </div>
        </div>
        """)

        # Tab view switcher: Waveform, Spectrogram, Features (100% Client-side React - ZERO BLINK)
        ws_tabs = st.tabs(["Waveform", "Spectrogram", "Features"])

        with ws_tabs[0]:
            # Audio Waveform Player with Accurate Speech Bar Spectrum
            r_html(f"""
            <div style="margin:10px 0 16px 0; background:#ffffff; border:1px solid #ede9e2; border-radius:14px; padding:16px 20px;">
                <!-- Audio Waveform with Vertical Frequency Bars & Scrubber Pin -->
                <div style="position:relative; width:100%; height:68px; margin-bottom:12px; display:flex; align-items:center;">
                    <svg width="100%" height="68" viewBox="0 0 620 68" preserveAspectRatio="none" fill="none">
                        <rect x="0.0" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#4f75e2"/><rect x="8.2" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#4f75e2"/><rect x="16.5" y="31.9" width="2.8" height="4.2" rx="1.4" fill="#4f75e2"/><rect x="24.7" y="31.2" width="2.8" height="5.5" rx="1.4" fill="#4f75e2"/><rect x="32.9" y="31.2" width="2.8" height="5.6" rx="1.4" fill="#4f75e2"/><rect x="41.1" y="31.6" width="2.8" height="4.9" rx="1.4" fill="#4f75e2"/><rect x="49.4" y="31.7" width="2.8" height="4.6" rx="1.4" fill="#4f75e2"/><rect x="57.6" y="31.1" width="2.8" height="5.9" rx="1.4" fill="#4f75e2"/><rect x="65.8" y="29.4" width="2.8" height="9.1" rx="1.4" fill="#4f75e2"/><rect x="74.1" y="27.2" width="2.8" height="13.5" rx="1.4" fill="#4f75e2"/><rect x="82.3" y="25.3" width="2.8" height="17.4" rx="1.4" fill="#4f75e2"/><rect x="90.5" y="24.4" width="2.8" height="19.3" rx="1.4" fill="#4f75e2"/><rect x="98.8" y="24.6" width="2.8" height="18.9" rx="1.4" fill="#4f75e2"/><rect x="107.0" y="25.4" width="2.8" height="17.3" rx="1.4" fill="#4f75e2"/><rect x="115.2" y="25.7" width="2.8" height="16.6" rx="1.4" fill="#4f75e2"/><rect x="123.4" y="24.7" width="2.8" height="18.6" rx="1.4" fill="#4f75e2"/><rect x="131.7" y="22.0" width="2.8" height="24.0" rx="1.4" fill="#4f75e2"/><rect x="139.9" y="18.4" width="2.8" height="31.3" rx="1.4" fill="#4f75e2"/><rect x="148.1" y="15.0" width="2.8" height="38.0" rx="1.4" fill="#4f75e2"/><rect x="156.4" y="13.3" width="2.8" height="41.4" rx="1.4" fill="#4f75e2"/><rect x="164.6" y="13.6" width="2.8" height="40.7" rx="1.4" fill="#4f75e2"/><rect x="172.8" y="15.5" width="2.8" height="37.0" rx="1.4" fill="#4f75e2"/><rect x="181.0" y="17.4" width="2.8" height="33.1" rx="1.4" fill="#4f75e2"/><rect x="189.3" y="18.2" width="2.8" height="31.6" rx="1.4" fill="#4f75e2"/><rect x="197.5" y="17.0" width="2.8" height="34.0" rx="1.4" fill="#4f75e2"/><rect x="205.7" y="14.4" width="2.8" height="39.2" rx="1.4" fill="#4f75e2"/><rect x="214.0" y="11.9" width="2.8" height="44.2" rx="1.4" fill="#93c5fd"/><rect x="222.2" y="10.9" width="2.8" height="46.2" rx="1.4" fill="#93c5fd"/><rect x="230.4" y="12.2" width="2.8" height="43.6" rx="1.4" fill="#93c5fd"/><rect x="238.7" y="15.3" width="2.8" height="37.4" rx="1.4" fill="#93c5fd"/><rect x="246.9" y="18.7" width="2.8" height="30.6" rx="1.4" fill="#93c5fd"/><rect x="255.1" y="20.6" width="2.8" height="26.9" rx="1.4" fill="#93c5fd"/><rect x="263.3" y="19.9" width="2.8" height="28.2" rx="1.4" fill="#93c5fd"/><rect x="271.6" y="17.0" width="2.8" height="34.0" rx="1.4" fill="#93c5fd"/><rect x="279.8" y="13.2" width="2.8" height="41.5" rx="1.4" fill="#93c5fd"/><rect x="288.0" y="10.6" width="2.8" height="46.9" rx="1.4" fill="#93c5fd"/><rect x="296.3" y="10.1" width="2.8" height="47.9" rx="1.4" fill="#93c5fd"/><rect x="304.5" y="11.8" width="2.8" height="44.5" rx="1.4" fill="#93c5fd"/><rect x="312.7" y="14.4" width="2.8" height="39.3" rx="1.4" fill="#93c5fd"/><rect x="320.9" y="16.0" width="2.8" height="36.0" rx="1.4" fill="#93c5fd"/><rect x="329.2" y="15.4" width="2.8" height="37.1" rx="1.4" fill="#93c5fd"/><rect x="337.4" y="12.6" width="2.8" height="42.7" rx="1.4" fill="#93c5fd"/><rect x="345.6" y="8.8" width="2.8" height="50.5" rx="1.4" fill="#93c5fd"/><rect x="353.9" y="5.7" width="2.8" height="56.6" rx="1.4" fill="#93c5fd"/><rect x="362.1" y="4.9" width="2.8" height="58.3" rx="1.4" fill="#93c5fd"/><rect x="370.3" y="6.6" width="2.8" height="54.8" rx="1.4" fill="#93c5fd"/><rect x="378.5" y="9.9" width="2.8" height="48.3" rx="1.4" fill="#93c5fd"/><rect x="386.8" y="12.9" width="2.8" height="42.1" rx="1.4" fill="#93c5fd"/><rect x="395.0" y="14.4" width="2.8" height="39.2" rx="1.4" fill="#93c5fd"/><rect x="403.2" y="13.7" width="2.8" height="40.6" rx="1.4" fill="#93c5fd"/><rect x="411.5" y="11.6" width="2.8" height="44.7" rx="1.4" fill="#93c5fd"/><rect x="419.7" y="9.9" width="2.8" height="48.3" rx="1.4" fill="#93c5fd"/><rect x="427.9" y="9.7" width="2.8" height="48.6" rx="1.4" fill="#93c5fd"/><rect x="436.2" y="11.7" width="2.8" height="44.6" rx="1.4" fill="#93c5fd"/><rect x="444.4" y="15.2" width="2.8" height="37.6" rx="1.4" fill="#93c5fd"/><rect x="452.6" y="18.7" width="2.8" height="30.6" rx="1.4" fill="#93c5fd"/><rect x="460.8" y="20.8" width="2.8" height="26.4" rx="1.4" fill="#93c5fd"/><rect x="469.1" y="20.9" width="2.8" height="26.3" rx="1.4" fill="#93c5fd"/><rect x="477.3" y="19.3" width="2.8" height="29.4" rx="1.4" fill="#93c5fd"/><rect x="485.5" y="17.4" width="2.8" height="33.2" rx="1.4" fill="#93c5fd"/><rect x="493.8" y="16.4" width="2.8" height="35.2" rx="1.4" fill="#93c5fd"/><rect x="502.0" y="17.1" width="2.8" height="33.8" rx="1.4" fill="#93c5fd"/><rect x="510.2" y="19.2" width="2.8" height="29.5" rx="1.4" fill="#93c5fd"/><rect x="518.4" y="22.0" width="2.8" height="24.0" rx="1.4" fill="#93c5fd"/><rect x="526.7" y="24.3" width="2.8" height="19.4" rx="1.4" fill="#93c5fd"/><rect x="534.9" y="25.5" width="2.8" height="17.0" rx="1.4" fill="#93c5fd"/><rect x="543.1" y="25.8" width="2.8" height="16.5" rx="1.4" fill="#93c5fd"/><rect x="551.4" y="25.7" width="2.8" height="16.6" rx="1.4" fill="#93c5fd"/><rect x="559.6" y="26.1" width="2.8" height="15.8" rx="1.4" fill="#93c5fd"/><rect x="567.8" y="27.3" width="2.8" height="13.4" rx="1.4" fill="#93c5fd"/><rect x="576.1" y="29.1" width="2.8" height="9.8" rx="1.4" fill="#93c5fd"/><rect x="584.3" y="30.9" width="2.8" height="6.1" rx="1.4" fill="#93c5fd"/><rect x="592.5" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#93c5fd"/><rect x="600.7" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#93c5fd"/><rect x="609.0" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#93c5fd"/><rect x="617.2" y="32.0" width="2.8" height="4.0" rx="1.4" fill="#93c5fd"/>
                        <!-- Scrubber Pin at current playback position (34%) -->
                        <line x1="211" y1="2" x2="211" y2="66" stroke="#4f75e2" stroke-width="2"/>
                        <circle cx="211" cy="4" r="4.5" fill="#4f75e2"/>
                    </svg>
                </div>

                <!-- Player Controls Row -->
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <div style="display:flex; align-items:center; gap:14px;">
                        <button style="width:34px; height:34px; border-radius:50%; background:#4f75e2; border:none; color:#ffffff; display:flex; align-items:center; justify-content:center; cursor:pointer; box-shadow:0 2px 6px rgba(79,117,226,0.35);">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="#ffffff"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                        </button>
                        <span style="font-size:12px; font-weight:600; color:#64748b;">0:12 / 0:45</span>
                    </div>

                    <div style="flex:1; margin:0 20px; position:relative;">
                        <div style="background:#eae6df; height:4px; border-radius:9999px; width:100%;">
                            <div style="background:#4f75e2; height:100%; width:27%; border-radius:9999px; position:relative;">
                                <div style="position:absolute; right:-4px; top:-3px; width:10px; height:10px; border-radius:50%; background:#4f75e2; box-shadow:0 1px 3px rgba(0,0,0,0.2);"></div>
                            </div>
                        </div>
                    </div>

                    <div style="display:flex; align-items:center; gap:12px;">
                        <div style="color:#64748b; cursor:pointer; display:flex; align-items:center;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                        </div>
                        <div style="font-size:11px; font-weight:600; color:#64748b; background:#f4f2ee; border:1px solid #ded9d0; border-radius:6px; padding:3px 8px; cursor:pointer; display:flex; align-items:center; gap:3px;">
                            1x <span style="font-size:9px;">&#9662;</span>
                        </div>
                    </div>
                </div>
            </div>
            """)

        with ws_tabs[1]:
            r_html("""
            <div style="margin:10px 0 16px 0; background:#0f172a; border-radius:14px; padding:18px 20px; color:#ffffff;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; font-size:11.5px; color:#94a3b8;">
                    <span>MEL-FREQUENCY SPECTROGRAM HEATMAP (0 - 8000 Hz)</span>
                    <span style="color:#38bdf8;">Window: 4.0s · Hop: 1.0s · FFT: 1024</span>
                </div>
                <div style="height:85px; width:100%; border-radius:8px; overflow:hidden; background:linear-gradient(90deg, #1e1b4b 0%, #4338ca 15%, #06b6d4 30%, #10b981 45%, #eab308 60%, #ef4444 75%, #4338ca 90%, #06b6d4 100%); opacity:0.88; position:relative;">
                    <div style="position:absolute; inset:0; background:repeating-linear-gradient(0deg, transparent, transparent 12px, rgba(0,0,0,0.3) 12px, rgba(0,0,0,0.3) 13px);"></div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:10px; color:#64748b; margin-top:6px;">
                    <span>0.0s</span><span>1.0s</span><span>2.0s</span><span>3.0s</span><span>4.0s</span>
                </div>
            </div>
            """)

        with ws_tabs[2]:
            r_html(f"""
            <div style="margin:10px 0 16px 0; background:#ffffff; border:1px solid #ede9e2; border-radius:14px; padding:16px 20px;">
                <div style="font-size:12px; font-weight:700; color:#18202f; margin-bottom:12px;">EXTRACTED ACOUSTIC DESCRIPTOR MATRIX ({dyn_features} FEATURES)</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:11px;">
                    <div style="background:#faf8f5; padding:10px 12px; border-radius:8px; border:1px solid #ede9e2;">
                        <div style="font-weight:600; color:#475569; margin-bottom:4px;">MFCC Coefficients (13 bands + &Delta; + &Delta;&Delta;)</div>
                        <div style="height:6px; width:100%; background:#e2e8f0; border-radius:3px; overflow:hidden;"><div style="width:84%; height:100%; background:#4f75e2;"></div></div>
                    </div>
                    <div style="background:#faf8f5; padding:10px 12px; border-radius:8px; border:1px solid #ede9e2;">
                        <div style="font-weight:600; color:#475569; margin-bottom:4px;">Spectral Centroid &amp; Rolloff Energy</div>
                        <div style="height:6px; width:100%; background:#e2e8f0; border-radius:3px; overflow:hidden;"><div style="width:72%; height:100%; background:#10b981;"></div></div>
                    </div>
                </div>
            </div>
            """)

        # Input Mode Selector: Client-side tabs (ZERO BLINK / INSTANT SWITCHING)
        in_tabs = st.tabs(["📁  Upload Audio File", "🎙️  Live Voice Record"])

        with in_tabs[0]:
            r_html("""
            <div style="margin-bottom:6px;">
                <div style="font-size:12.5px; font-weight:700; color:#18202f;">Drag &amp; drop your audio file here</div>
                <div style="font-size:10.5px; color:#8c96a5;">Supports WAV, FLAC, MP3, OGG, M4A, AAC, MPG · 200MB max</div>
            </div>
            """)

            uploaded_file = st.file_uploader(
                "Drag & drop your audio file here",
                type=["wav", "mp3", "flac", "ogg", "m4a", "aac", "mpg", "mpeg"],
                label_visibility="collapsed",
                key="workspace_file_uploader"
            )

            col_btn1, col_btn2 = st.columns([3.5, 1.2])
            with col_btn2:
                run_btn = st.button("Analyze Audio File →", disabled=(uploaded_file is None), use_container_width=True)

            if run_btn and uploaded_file:
                with st.spinner("Processing audio through feature extraction engine…"):
                    try:
                        res = analyze_file(uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
                        st.session_state.last_result = res
                        st.session_state.last_time = datetime.now().strftime("%d %b %Y · %I:%M %p")
                        fin = res.get("final", {})
                        st.session_state.history.insert(0, {
                            "name": uploaded_file.name,
                            "type": uploaded_file.name.split(".")[-1].upper(),
                            "result": fin.get("action", "verify").upper(),
                            "confidence": pct(fin.get("confidence", 0.724)),
                            "date": st.session_state.last_time,
                        })
                        st.success("File analyzed successfully! Detection overview updated.")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

        with in_tabs[1]:
            r_html("""
            <div style="margin-bottom:8px;">
                <div style="font-size:12.5px; font-weight:700; color:#18202f;">Record live voice via microphone</div>
                <div style="font-size:10.5px; color:#8c96a5;">Speak clearly for at least 4 seconds for optimal sliding-window detection</div>
            </div>
            """)

            mic_audio = st.audio_input("Record Speech", key=f"mic_input_{st.session_state.live_rec_key}")

            col_rec1, col_rec2 = st.columns([3.5, 1.2])
            with col_rec2:
                run_rec_btn = st.button("Analyze Recording →", disabled=(mic_audio is None), use_container_width=True)

            if run_rec_btn and mic_audio:
                with st.spinner("Analyzing live microphone audio stream…"):
                    try:
                        rec_name = f"mic_capture_{datetime.now().strftime('%H%M%S')}.wav"
                        res = analyze_file(rec_name, mic_audio.getvalue(), "audio/wav")
                        st.session_state.last_result = res
                        st.session_state.last_time = datetime.now().strftime("%d %b %Y · %I:%M %p")
                        fin = res.get("final", {})
                        st.session_state.history.insert(0, {
                            "name": rec_name,
                            "type": "WAV",
                            "result": fin.get("action", "verify").upper(),
                            "confidence": pct(fin.get("confidence", 0.724)),
                            "date": st.session_state.last_time,
                        })
                        st.success("Microphone audio analyzed! Metrics updated.")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Live analysis failed: {e}")

        # Close Analysis Workspace Card
        st.markdown('</div>', unsafe_allow_html=True)

        # ── 4. RECENT ANALYSIS TABLE CARD ──
        history_rows = ""
        for item in st.session_state.history[:6]:
            res_val = item.get("result", "VERIFY").upper()
            badge_bg = "#ecfdf5" if res_val == "ALLOW" else "#fef2f2" if res_val == "ESCALATE" else "#fffbeb"
            badge_fg = "#059669" if res_val == "ALLOW" else "#dc2626" if res_val == "ESCALATE" else "#d97706"
            badge_border = "#d1fae5" if res_val == "ALLOW" else "#fee2e2" if res_val == "ESCALATE" else "#fef3c7"
            history_rows += f"""
            <div style="display:grid; grid-template-columns:2.2fr 1fr 1.3fr 1fr 1.4fr; padding:12px 14px; border-bottom:1px solid #f1eee8; font-size:12.5px; align-items:center;">
                <div style="font-weight:600; color:#18202f; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; padding-right:10px;">{item['name']}</div>
                <div style="color:#64748b;">{item['type']}</div>
                <div><span style="background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; padding:3px 9px; border-radius:12px; font-weight:600; font-size:11px;">{res_val}</span></div>
                <div style="font-weight:700; color:#18202f;">{item['confidence']}</div>
                <div style="color:#8c96a5; font-size:11.5px;">{item['date']}</div>
            </div>
            """

        r_html(f"""
        <div class="vcg-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="width:24px; height:24px; border-radius:6px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    </div>
                    <div>
                        <div style="font-size:15px; font-weight:700; color:#18202f;">Recent Analysis</div>
                        <div style="font-size:11px; color:#8c96a5;">Your uploaded files and results</div>
                    </div>
                </div>
                <div style="font-size:12px; font-weight:600; color:#4f75e2; cursor:pointer;">
                    View all &rarr;
                </div>
            </div>

            <div style="display:grid; grid-template-columns:2.2fr 1fr 1.3fr 1fr 1.4fr; padding:8px 14px; background:#faf8f5; border-radius:8px; font-size:11px; font-weight:600; color:#8c96a5;">
                <div>File Name</div>
                <div>Type</div>
                <div>Result</div>
                <div>Confidence</div>
                <div>Date</div>
            </div>

            {history_rows}
        </div>
        """)

    # ═════════════════════════════════════════════════════════════
    # RIGHT COLUMN (EXACT MOCKUP CARDS & CHEVRON SHORTCUTS)
    # ═════════════════════════════════════════════════════════════
    with col_right:
        # ── 1. MODEL CARD ──
        r_html(f"""
        <div class="vcg-card" style="padding:18px 20px; display:flex; gap:16px; align-items:stretch; margin-bottom:18px;">
            <div style="width:72px; min-height:120px; border-radius:12px; overflow:hidden; flex-shrink:0; background:linear-gradient(135deg, #e0e7ff 0%, #fae8ff 50%, #ffedd5 100%); position:relative;">
                <svg width="100%" height="100%" viewBox="0 0 80 120" preserveAspectRatio="none">
                    <path d="M-10,30 C30,10 50,70 90,40 L90,130 L-10,130 Z" fill="rgba(147, 197, 253, 0.45)"/>
                    <path d="M-10,60 C40,40 40,90 90,80 L90,130 L-10,130 Z" fill="rgba(249, 168, 130, 0.5)"/>
                    <path d="M-10,80 C30,70 60,110 90,100 L90,130 L-10,130 Z" fill="rgba(196, 181, 253, 0.55)"/>
                </svg>
            </div>

            <div style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:9.5px; font-weight:700; color:#8c96a5; text-transform:uppercase; letter-spacing:0.8px;">Model</div>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#18202f" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    </div>
                    <div style="font-size:16px; font-weight:800; color:#18202f; margin-top:3px; line-height:1.2;">{dyn_model_name}</div>
                    <div style="font-size:10.5px; color:#8c96a5; margin-top:2px;">MFCC, delta and spectral statistics</div>
                </div>

                <div style="margin-top:14px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-size:9.5px; font-weight:600; color:#8c96a5;">Security Response</div>
                            <div style="font-size:14px; font-weight:800; color:#18202f; margin-top:1px;">3 actions</div>
                        </div>
                        <span style="color:#8c96a5; font-size:16px;">&rsaquo;</span>
                    </div>
                    <div style="display:flex; gap:6px; margin-top:6px;">
                        <span style="font-size:10px; font-weight:500; background:#f4f2ee; color:#475569; padding:2px 8px; border-radius:10px;">Allow</span>
                        <span style="font-size:10px; font-weight:500; background:#f4f2ee; color:#475569; padding:2px 8px; border-radius:10px;">Verify</span>
                        <span style="font-size:10px; font-weight:500; background:#f4f2ee; color:#475569; padding:2px 8px; border-radius:10px;">Escalate</span>
                    </div>
                </div>
            </div>
        </div>
        """)

        # ── 2. SHORTCUT CARDS ──
        r_html("""
        <div class="vcg-card" style="margin-bottom:18px;">
            <div style="font-size:14.5px; font-weight:700; color:#18202f;">Analysis Workspace</div>
            <div style="font-size:11px; color:#8c96a5; margin-top:2px; margin-bottom:14px;">Upload or live record</div>

            <a href="#analysis-section" class="vcg-shortcut-card">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:34px; height:34px; border-radius:8px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2; flex-shrink:0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="2" x2="12" y2="22"></line><line x1="17" y1="6" x2="17" y2="18"></line><line x1="7" y1="9" x2="7" y2="15"></line><line x1="2" y1="12" x2="2" y2="12"></line><line x1="22" y1="12" x2="22" y2="12"></line></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Signal monitor</div>
                        <div style="font-size:10px; color:#8c96a5; line-height:1.2;">Waveform reference &middot; results</div>
                    </div>
                </div>
                <span style="color:#94a3b8; font-size:17px; font-weight:600;">&rsaquo;</span>
            </a>

            <a href="#analysis-section" class="vcg-shortcut-card">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:34px; height:34px; border-radius:8px; background:#f5f3ff; display:flex; align-items:center; justify-content:center; color:#7c3aed; flex-shrink:0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Upload audio</div>
                        <div style="font-size:10px; color:#8c96a5;">Choose a file or record</div>
                    </div>
                </div>
                <span style="color:#94a3b8; font-size:17px; font-weight:600;">&rsaquo;</span>
            </a>

            <a href="#analysis-section" class="vcg-shortcut-card">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:34px; height:34px; border-radius:8px; background:#fff1f2; display:flex; align-items:center; justify-content:center; color:#e11d48; flex-shrink:0;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Live record</div>
                        <div style="font-size:10px; color:#8c96a5;">Use your microphone</div>
                    </div>
                </div>
                <span style="color:#94a3b8; font-size:17px; font-weight:600;">&rsaquo;</span>
            </a>
        </div>
        """)

        # ── 3. MODEL SNAPSHOT CARD ──
        r_html(f"""
        <div class="vcg-card" style="padding:18px 20px; position:relative; overflow:hidden; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <span style="font-size:14px; font-weight:800; color:#18202f;">Model Snapshot</span>
                <div style="display:inline-flex; align-items:center; gap:5px; background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; border-radius:9999px; padding:2px 8px; font-size:10px; font-weight:600;">
                    <span style="width:5px; height:5px; border-radius:50%; background:#10b981;"></span>
                    Prototype validation
                    <span style="font-size:12px; margin-left:2px;">&rsaquo;</span>
                </div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:16px;">
                <div>
                    <div style="font-size:24px; font-weight:800; color:#18202f; line-height:1.1;">{dyn_accuracy}</div>
                    <div style="font-size:10px; color:#8c96a5; margin-top:2px;">Accuracy</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:24px; font-weight:800; color:#18202f; line-height:1.1;">{dyn_features}</div>
                    <div style="font-size:10px; color:#8c96a5; margin-top:2px;">Features</div>
                </div>
            </div>

            <!-- Pastel Gradient Wave art -->
            <div style="width:100%; height:32px; opacity:0.8;">
                <svg width="100%" height="32" viewBox="0 0 280 32" preserveAspectRatio="none" fill="none">
                    <path d="M0,22 C50,10 100,28 150,15 C200,2 240,24 280,12 L280,32 L0,32 Z" fill="url(#snapGrad)"/>
                    <defs>
                        <linearGradient id="snapGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#c4b5fd" stop-opacity="0.45"/>
                            <stop offset="50%" stop-color="#93c5fd" stop-opacity="0.5"/>
                            <stop offset="100%" stop-color="#fed7aa" stop-opacity="0.45"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
        </div>
        """)

        # ── 4. QUICK STATS CARD ──
        r_html(f"""
        <div class="vcg-card" style="padding:18px 20px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:14px;">
                <div style="width:20px; height:20px; border-radius:5px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2;">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                </div>
                <div style="font-size:12px; font-weight:700; color:#18202f;">Quick Stats</div>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f1eee8; font-size:12px;">
                <div style="display:flex; align-items:center; gap:8px; color:#64748b;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                    Window
                </div>
                <span style="font-weight:700; color:#18202f;">{dyn_window} s</span>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; border-bottom:1px solid #f1eee8; font-size:12px;">
                <div style="display:flex; align-items:center; gap:8px; color:#64748b;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5v14M7 9v6M22 10v4M2 11v2"></path></svg>
                    Inputs
                </div>
                <span style="font-weight:700; color:#18202f;">{disp_inputs}</span>
            </div>

            <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 0; font-size:12px;">
                <div style="display:flex; align-items:center; gap:8px; color:#64748b;">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M12 16v-4M12 8h.01"></path></svg>
                    Local prototype
                </div>
                <span style="font-size:11px; color:#8c96a5; background:#faf8f5; border:1px solid #ede9e2; padding:2px 8px; border-radius:6px; display:inline-flex; align-items:center; gap:3px;">
                    Not production ready <span style="font-size:10px;">&rsaquo;</span>
                </span>
            </div>
        </div>
        """)

# ═════════════════════════════════════════════════════════════
# ROUTING: ANALYZE PAGE
# ═════════════════════════════════════════════════════════════
elif st.session_state.nav_page == "Analyze":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Deep Audio Analysis Studio</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Detailed spectral, temporal, and model confidence examination</div>
    </div>
""")

    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        st.markdown('<div class="vcg-card">', unsafe_allow_html=True)
        r_html("""
        <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:6px;">Upload or Stream Audio for Deep Inspection</div>
        <div style="font-size:11.5px; color:#8c96a5; margin-bottom:16px;">Supports all SIH benchmark formats: WAV, FLAC, MP3, OGG, M4A, AAC, MPG</div>
        """)

        a_file = st.file_uploader("Analyze Audio File", type=["wav", "mp3", "flac", "ogg", "m4a", "aac", "mpg", "mpeg"], key="deep_analyze_uploader")
        if a_file:
            if st.button("Run Deep Analysis →", key="btn_deep_run"):
                with st.spinner("Extracting 102 acoustic feature descriptors…"):
                    try:
                        res = analyze_file(a_file.name, a_file.getvalue(), a_file.type)
                        st.session_state.last_result = res
                        st.session_state.last_time = datetime.now().strftime("%d %b %Y · %I:%M %p")
                        st.success("Deep Analysis Completed!")
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_a2:
        r_html(f"""
        <div class="vcg-card">
            <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:12px;">Active Pipeline Parameters</div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Classifier Model</span>
                <span style="font-weight:700; color:#18202f;">{dyn_model_name}</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Feature Dimension</span>
                <span style="font-weight:700; color:#18202f;">{dyn_features} Descriptors</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Analysis Window</span>
                <span style="font-weight:700; color:#18202f;">{dyn_window}.0 seconds</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12.5px;">
                <span style="color:#64748b;">Sampling Target</span>
                <span style="font-weight:700; color:#18202f;">16,000 Hz Mono</span>
            </div>
        </div>
        """)

# ═════════════════════════════════════════════════════════════
# ROUTING: HISTORY PAGE
# ═════════════════════════════════════════════════════════════
elif st.session_state.nav_page == "History":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Audit &amp; Detection History</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Complete chronological record of all evaluated audio files</div>
    </div>
""")

    full_rows = ""
    for item in st.session_state.history:
        res_val = item.get("result", "VERIFY").upper()
        badge_bg = "#ecfdf5" if res_val == "ALLOW" else "#fef2f2" if res_val == "ESCALATE" else "#fffbeb"
        badge_fg = "#059669" if res_val == "ALLOW" else "#dc2626" if res_val == "ESCALATE" else "#d97706"
        badge_border = "#d1fae5" if res_val == "ALLOW" else "#fee2e2" if res_val == "ESCALATE" else "#fef3c7"
        full_rows += f"""
        <div style="display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1.8fr; padding:12px 16px; border-bottom:1px solid #f1eee8; font-size:12.5px; align-items:center;">
            <div style="font-weight:600; color:#18202f;">{item['name']}</div>
            <div style="color:#64748b;">{item['type']}</div>
            <div><span style="background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; padding:3px 10px; border-radius:12px; font-weight:600; font-size:11px;">{res_val}</span></div>
            <div style="font-weight:700; color:#18202f;">{item['confidence']}</div>
            <div style="color:#8c96a5; font-size:11.5px;">{item['date']}</div>
        </div>
        """

    r_html(f"""
    <div class="vcg-card">
        <div style="display:grid; grid-template-columns:2.4fr 1fr 1.2fr 1.2fr 1.8fr; padding:10px 16px; background:#faf8f5; border-radius:10px; font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">
            <div>FILE NAME</div>
            <div>CODEC</div>
            <div>POLICY DECISION</div>
            <div>CONFIDENCE</div>
            <div>TIMESTAMP</div>
        </div>
        {full_rows}
    </div>
""")

# ═════════════════════════════════════════════════════════════
# ROUTING: MODEL PAGE
# ═════════════════════════════════════════════════════════════
elif st.session_state.nav_page == "Model":
    r_html(f"""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Model Architecture &amp; Specifications</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Technical parameters for the {dyn_model_name} classification engine</div>
    </div>
""")

    col_m1, col_m2 = st.columns([1, 1])
    with col_m1:
        r_html(f"""
        <div class="vcg-card">
            <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">Acoustic Feature Extraction</div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Vector Dimension</span>
                <span style="font-weight:700; color:#18202f;">{dyn_features} Features</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Primary Descriptor</span>
                <span style="font-weight:700; color:#18202f;">MFCC (13 coefficients + &Delta; + &Delta;&Delta;)</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Spectral Descriptors</span>
                <span style="font-weight:700; color:#18202f;">Spectral Centroid, Rolloff, Contrast, Flatness</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12.5px;">
                <span style="color:#64748b;">Zero Crossing Rate</span>
                <span style="font-weight:700; color:#18202f;">Mean &amp; Variance Statistics</span>
            </div>
        </div>
        """)

    with col_m2:
        r_html(f"""
        <div class="vcg-card">
            <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">Temporal Windowing &amp; Rolling Engine</div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Window Length</span>
                <span style="font-weight:700; color:#18202f;">{dyn_window}.0 seconds</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Hop Size</span>
                <span style="font-weight:700; color:#18202f;">1.0 second (75% overlap)</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Sampling Target</span>
                <span style="font-weight:700; color:#18202f;">16,000 Hz &middot; Mono Channel</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12.5px;">
                <span style="color:#64748b;">Validation Benchmark</span>
                <span style="font-weight:700; color:#18202f;">{dyn_accuracy} Accuracy ({dyn_samples} prototype vectors)</span>
            </div>
        </div>
        """)

# ═════════════════════════════════════════════════════════════
# ROUTING: SETTINGS PAGE
# ═════════════════════════════════════════════════════════════
elif st.session_state.nav_page == "Settings":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Settings</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Console preferences, risk policies, and API configuration</div>
    </div>
""")

    col_s1, col_s2 = st.columns([1, 1])
    with col_s1:
        r_html(f"""
        <div class="vcg-card">
            <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">API Endpoint Configuration</div>
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">SERVICE HOST</div>
                <div style="font-size:13px; color:#18202f; font-family:monospace; background:#faf8f5; padding:8px 12px; border-radius:8px; border:1px solid #ece7e0;">{API_URL}</div>
            </div>
            <div style="margin-bottom:12px;">
                <div style="font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">STATUS</div>
                <div style="display:flex; align-items:center; gap:6px; font-size:12.5px; font-weight:600; color:#059669;">
                    <div style="width:7px; height:7px; border-radius:50%; background:#10b981;"></div>
                    {status_label}
                </div>
            </div>
            <div>
                <div style="font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">SUPPORTED CODECS</div>
                <div style="font-size:12px; color:#64748b;">WAV, FLAC, MP3, OGG, M4A, AAC, MPEG, MPG</div>
            </div>
        </div>
        """)

    with col_s2:
        r_html("""
        <div class="vcg-card">
            <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">Security Policy Thresholds</div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Allow (Low Risk)</span>
                <span style="font-weight:700; color:#059669;">&le; 0.35 Spoof Probability</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
                <span style="color:#64748b;">Verify (Medium Risk)</span>
                <span style="font-weight:700; color:#d97706;">0.35 &ndash; 0.70 Spoof Probability</span>
            </div>
            <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12.5px;">
                <span style="color:#64748b;">Escalate (High Risk)</span>
                <span style="font-weight:700; color:#dc2626;">&gt; 0.70 Spoof Probability</span>
            </div>
        </div>
        """)
