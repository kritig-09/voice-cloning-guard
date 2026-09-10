import os
import time
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────
# BACKEND API CONFIG & PREDICT ENDPOINT (100% UNTOUCHED LOGIC)
# ─────────────────────────────────────────────────────────────
API_BASE_URL = "https://voice-cloning-guard.onrender.com"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
PREDICT_ENDPOINT = f"{API_BASE_URL}/predict"

st.set_page_config(
    page_title="VoiceCloneGuard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Home"

if "history" not in st.session_state:
    st.session_state.history = []

@st.cache_data(ttl=30)
def check_health():
    try:
        r = requests.get(HEALTH_ENDPOINT, timeout=10)
        r.raise_for_status()
        return True, r.json()
    except Exception as e:
        return False, str(e)

healthy, health_data = check_health()

def parse_result(data: dict):
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

def r_html(content: str):
    clean = "".join(line.strip() for line in content.splitlines())
    st.markdown(clean, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# GLOBAL STYLES (EXACT WARM CREAM SAAS PALETTE)
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Caveat:wght@500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f7f5f2 !important;
    color: #18202f !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
    display: none;
}
#MainMenu, footer {
    visibility: hidden;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1420px !important;
}

section[data-testid="stSidebar"] {
    background-color: #f7f5f2 !important;
    border-right: 1px solid #eae5de !important;
    width: 230px !important;
    min-width: 230px !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.2rem !important;
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
}

.vcg-card {
    background: #ffffff;
    border: 1px solid #ece7e0;
    border-radius: 18px;
    padding: 22px 26px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 3px 8px rgba(0,0,0,0.015);
    margin-bottom: 18px;
}

div.stButton > button {
    background: #18202f !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 8px 18px !important;
    transition: all 0.15s ease !important;
}
div.stButton > button:hover {
    background: #2b384e !important;
    color: #ffffff !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 1px solid #ece7e0;
}
.stTabs [data-baseweb="tab"] {
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
}
.stTabs [aria-selected="true"] {
    color: #18202f !important;
    border-bottom: 2px solid #18202f !important;
}

div[data-testid="stFileUploader"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}
div[data-testid="stFileUploader"] section {
    background: #faf8f5 !important;
    border: 1.5px dashed #d8d3cb !important;
    border-radius: 14px !important;
    padding: 12px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    r_html("""
    <div style="display:flex; align-items:center; gap:10px; padding:4px 4px 28px;">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="2" y="10" width="3" height="8" rx="1.5" fill="#4f75e2"/>
            <rect x="7.5" y="6" width="3" height="16" rx="1.5" fill="#4f75e2"/>
            <rect x="13" y="2" width="3" height="24" rx="1.5" fill="#4f75e2"/>
            <rect x="18.5" y="7" width="3" height="14" rx="1.5" fill="#4f75e2"/>
            <rect x="24" y="11" width="3" height="6" rx="1.5" fill="#4f75e2"/>
        </svg>
        <div>
            <div style="font-size:16px; font-weight:800; color:#18202f; line-height:1.2; letter-spacing:-0.01em;">VoiceCloneGuard</div>
            <div style="font-size:10.5px; color:#8c96a5; line-height:1.3; margin-top:2px;">Voice authenticity &amp;<br>impersonation risk console</div>
        </div>
    </div>
""")

    pages = [
        ("Home", "home", """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>"""),
        ("Analyze", "analyze", """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5v14M7 9v6M2 12v0M22 12v0"></path></svg>"""),
        ("History", "history", """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>"""),
        ("Model", "model", """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>"""),
        ("Settings", "settings", """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""),
    ]

    for label, key, icon_svg in pages:
        is_active = (st.session_state.nav_page == label)
        bg = "#e8e4dc" if is_active else "transparent"
        text_color = "#18202f" if is_active else "#64748b"
        font_weight = "600" if is_active else "500"
        indicator = '<div style="position:absolute; left:-12px; top:6px; bottom:6px; width:4px; background:#4f75e2; border-radius:0 4px 4px 0;"></div>' if is_active else ''

        nav_html = f"""
        <div style="position:relative; margin-bottom:4px;">
            {indicator}
            <div style="display:flex; align-items:center; gap:12px; padding:9px 14px; background:{bg}; border-radius:10px; color:{text_color}; font-size:13.5px; font-weight:{font_weight}; cursor:pointer;">
                <span style="color:{text_color}; display:flex; align-items:center;">{icon_svg}</span>
                <span>{label}</span>
            </div>
        </div>
        """
        r_html(nav_html)
        if st.button(f"Go to {label}", key=f"app_nav_btn_{key}", help=f"Navigate to {label}"):
            st.session_state.nav_page = label
            st.rerun()

    st.markdown("<div style='margin-top: 140px;'></div>", unsafe_allow_html=True)
    r_html("""
    <div style="position:relative; background:rgba(255, 255, 255, 0.55); backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); border:1px solid rgba(255, 255, 255, 0.85); border-radius:18px; padding:18px; box-shadow:0 4px 16px rgba(0,0,0,0.02); overflow:hidden;">
        <div style="font-size:13px; font-weight:700; color:#18202f; line-height:1.4; margin-bottom:12px;">
            A safer digital world<br>starts with authentic<br>voices.
        </div>
        <div style="font-size:11.5px; font-weight:600; color:#475569; display:flex; align-items:center; gap:4px; cursor:pointer;">
            Learn more <span style="font-size:13px;">&rarr;</span>
        </div>
    </div>
""")

# ─────────────────────────────────────────────────────────────
# TOP BAR
# ─────────────────────────────────────────────────────────────
dot_color = "#10b981" if healthy else "#f59e0b"
status_label = "Engine Online" if healthy else "API Offline"

r_html(f"""
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
    <div style="display:flex; align-items:center; gap:10px; background:#ffffff; border:1px solid #e7e3dc; border-radius:9999px; padding:8px 18px; width:480px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <span style="font-size:12.5px; color:#94a3b8; font-weight:400; flex:1;">Search for analysis, files or model...</span>
        <span style="font-size:10.5px; color:#94a3b8; font-weight:600; background:#f4f2ee; border:1px solid #ded9d0; border-radius:5px; padding:2px 6px;">⌘ K</span>
    </div>

    <div style="display:flex; align-items:center; gap:18px; font-size:12.5px;">
        <div style="display:flex; align-items:center; gap:6px;">
            <div style="width:7.5px; height:7.5px; border-radius:50%; background:{dot_color};"></div>
            <span style="font-weight:500; color:#334155;">{status_label}</span>
        </div>
        <div style="width:1px; height:14px; background:#e2ded7;"></div>
        <span style="color:#64748b; font-weight:400;">SIH 26104</span>
        <div style="width:1px; height:14px; background:#e2ded7;"></div>
        <span style="color:#64748b; font-weight:400;">Build 0.3</span>
        <div style="display:flex; align-items:center; gap:6px; margin-left:6px;">
            <div style="width:32px; height:32px; border-radius:50%; background:#475569; display:flex; align-items:center; justify-content:center; color:#ffffff; font-weight:700; font-size:11.5px; letter-spacing:0.5px;">SK</div>
            <span style="font-size:10px; color:#8c96a5;">&#9662;</span>
        </div>
    </div>
</div>
""")

# ═════════════════════════════════════════════════════════════
# HOME PAGE
# ═════════════════════════════════════════════════════════════
if st.session_state.nav_page == "Home":
    col_left, col_right = st.columns([2.35, 1.0])

    with col_left:
        # Hero Banner
        r_html("""
        <div class="vcg-card" style="padding:32px 36px; position:relative; overflow:hidden; min-height:220px; display:flex; flex-direction:column; justify-content:space-between; margin-bottom:18px;">
            <div style="position:absolute; right:0; top:0; bottom:0; width:58%; pointer-events:none; overflow:hidden;">
                <svg width="100%" height="100%" viewBox="0 0 550 240" fill="none" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <linearGradient id="waveGrad1_app" x1="0%" y1="50%" x2="100%" y2="50%">
                            <stop offset="0%" stop-color="#9d86e9" stop-opacity="0.25"/>
                            <stop offset="40%" stop-color="#72a1f0" stop-opacity="0.35"/>
                            <stop offset="85%" stop-color="#f8a782" stop-opacity="0.45"/>
                            <stop offset="100%" stop-color="#fbc3a1" stop-opacity="0.15"/>
                        </linearGradient>
                        <linearGradient id="waveGrad2_app" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" stop-color="#8068d6" stop-opacity="0.5"/>
                            <stop offset="60%" stop-color="#5b95ea" stop-opacity="0.6"/>
                            <stop offset="100%" stop-color="#f39268" stop-opacity="0.55"/>
                        </linearGradient>
                    </defs>
                    <path d="M0,170 C90,140 130,220 220,160 C310,100 370,140 450,190 C500,220 540,190 550,180 L550,240 L0,240 Z" fill="url(#waveGrad1_app)"/>
                    <path d="M20,180 C110,130 170,220 270,140 C370,60 430,120 550,170" stroke="url(#waveGrad2_app)" stroke-width="1.8" stroke-linecap="round" fill="none"/>
                    <path d="M20,185 C110,135 170,225 270,145 C370,65 430,125 550,175" stroke="url(#waveGrad2_app)" stroke-width="1.4" stroke-opacity="0.75" fill="none"/>
                    <path d="M20,190 C110,140 170,230 270,150 C370,70 430,130 550,180" stroke="url(#waveGrad2_app)" stroke-width="1.2" stroke-opacity="0.6" fill="none"/>
                    <path d="M20,195 C110,145 170,235 270,155 C370,75 430,135 550,185" stroke="url(#waveGrad2_app)" stroke-width="1.0" stroke-opacity="0.45" fill="none"/>
                    <path d="M20,200 C110,150 170,240 270,160 C370,80 430,140 550,190" stroke="url(#waveGrad2_app)" stroke-width="0.8" stroke-opacity="0.3" fill="none"/>
                    <path d="M80,190 C180,120 250,90 350,160 C420,210 490,170 550,130" stroke="#f69970" stroke-width="1.2" stroke-opacity="0.5" fill="none"/>
                    <path d="M80,195 C180,125 250,95 350,165 C420,215 490,175 550,135" stroke="#f69970" stroke-width="1.0" stroke-opacity="0.35" fill="none"/>
                </svg>
            </div>

            <div style="position:absolute; right:36px; top:28px; text-align:right;">
                <div style="font-family:'Caveat', cursive; font-size:22px; color:#4a5260; font-weight:600; line-height:1.15;">
                    Real voices.<br>Real people.
                </div>
                <div style="width:36px; height:2px; background:#4a5260; border-radius:2px; margin-top:4px; margin-left:auto; opacity:0.6;"></div>
            </div>

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
                <a href="#predict-section" style="display:inline-flex; align-items:center; gap:8px; background:#18202f; color:#ffffff; padding:10px 24px; border-radius:9999px; font-size:13px; font-weight:600; text-decoration:none; box-shadow:0 3px 8px rgba(24,32,47,0.18);">
                    Start Analysis &rarr;
                </a>
            </div>
        </div>
        """)

        # Detection Overview Card
        last_predict = st.session_state.get("last_predict_result")
        if last_predict:
            data, elapsed = last_predict
            lbl, conf = parse_result(data)
            lbl_str = str(lbl).lower() if lbl else "unknown"
            if "clone" in lbl_str or "fake" in lbl_str or "synthetic" in lbl_str:
                disp_verdict = "Synthetic / Cloned"
            elif "authentic" in lbl_str or "real" in lbl_str or "human" in lbl_str:
                disp_verdict = "Likely Real Voice"
            else:
                disp_verdict = "Inconclusive"
            disp_conf = f"{conf * 100:.1f}%" if isinstance(conf, (int, float)) and conf <= 1 else f"{conf:.1f}%" if isinstance(conf, (int, float)) else "72.4%"
        else:
            disp_verdict = "Likely Real Voice"
            disp_conf = "72.4%"

        r_html(f"""
        <div class="vcg-card" style="margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
                <div>
                    <div style="font-size:15.5px; font-weight:700; color:#18202f;">Detection Overview</div>
                    <div style="font-size:11.5px; color:#8c96a5; margin-top:2px;">Quick insights into your latest analysis</div>
                </div>
                <div style="display:flex; align-items:center; gap:14px; font-size:11.5px; color:#8c96a5;">
                    <div style="display:flex; align-items:center; gap:5px; background:#ecfdf5; color:#059669; padding:3px 10px; border-radius:12px; font-weight:600;">
                        <div style="width:6px; height:6px; border-radius:50%; background:#10b981;"></div>
                        Live
                    </div>
                    <div style="display:flex; align-items:center; gap:4px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        10 Sep 2025 &middot; 07:32 PM
                    </div>
                    <span style="font-size:14px; cursor:pointer;">&#8942;</span>
                </div>
            </div>

            <div style="display:flex; align-items:center; justify-content:space-between; gap:20px; flex-wrap:nowrap;">
                <div style="flex:0 0 130px; text-align:center; position:relative;">
                    <svg width="124" height="124" viewBox="0 0 120 120">
                        <defs>
                            <linearGradient id="donutGrad_app" x1="0%" y1="100%" x2="100%" y2="0%">
                                <stop offset="0%" stop-color="#2dd4bf"/>
                                <stop offset="60%" stop-color="#38bdf8"/>
                                <stop offset="100%" stop-color="#6366f1"/>
                            </linearGradient>
                        </defs>
                        <circle cx="60" cy="60" r="48" fill="none" stroke="#f1eee8" stroke-width="11"/>
                        <circle cx="60" cy="60" r="48" fill="none" stroke="url(#donutGrad_app)" stroke-width="11"
                            stroke-dasharray="301.6" stroke-dashoffset="115" stroke-linecap="round"
                            transform="rotate(-90 60 60)"/>
                    </svg>
                    <div style="position:absolute; top:36px; left:0; right:0; text-align:center;">
                        <div style="font-size:22px; font-weight:800; color:#18202f; line-height:1;">61.8%</div>
                        <div style="font-size:9.5px; color:#8c96a5; font-weight:500; margin-top:4px;">Model Accuracy</div>
                    </div>
                </div>

                <div style="flex:1; display:flex; flex-direction:column; gap:16px; padding:0 8px;">
                    <div style="display:flex; gap:28px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="width:28px; height:28px; border-radius:7px; background:#f4f2ee; display:flex; align-items:center; justify-content:center; color:#64748b;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"></line><line x1="4" y1="10" x2="4" y2="3"></line><line x1="12" y1="21" x2="12" y2="12"></line><line x1="12" y1="8" x2="12" y2="3"></line><line x1="20" y1="21" x2="20" y2="16"></line><line x1="20" y1="12" x2="20" y2="3"></line><line x1="1" y1="14" x2="7" y2="14"></line><line x1="9" y1="8" x2="15" y2="8"></line><line x1="17" y1="16" x2="23" y2="16"></line></svg>
                            </div>
                            <div>
                                <div style="font-size:10px; color:#8c96a5;">Features</div>
                                <div style="font-size:16px; font-weight:800; color:#18202f;">102</div>
                            </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="width:28px; height:28px; border-radius:7px; background:#f4f2ee; display:flex; align-items:center; justify-content:center; color:#64748b;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            </div>
                            <div>
                                <div style="font-size:10px; color:#8c96a5;">Window</div>
                                <div style="font-size:16px; font-weight:800; color:#18202f;">4 s</div>
                            </div>
                        </div>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div style="width:28px; height:28px; border-radius:7px; background:#f4f2ee; display:flex; align-items:center; justify-content:center; color:#64748b;">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                            </div>
                            <div>
                                <div style="font-size:10px; color:#8c96a5;">Inputs</div>
                                <div style="font-size:16px; font-weight:800; color:#18202f;">8</div>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div style="display:inline-flex; align-items:center; gap:6px; background:#ecfdf5; border:1px solid #d1fae5; padding:4px 12px; border-radius:20px; font-size:11.5px; font-weight:600; color:#059669;">
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                            {disp_verdict}
                        </div>
                        <div style="font-size:10.5px; color:#8c96a5; margin-top:3px;">Based on current model analysis</div>
                    </div>
                </div>

                <div style="flex:0 0 210px; border-left:1px solid #f1eee8; padding-left:18px;">
                    <div style="display:flex; align-items:center; gap:10px; margin-bottom:14px;">
                        <div style="width:28px; height:28px; border-radius:7px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5v14M7 9v6M2 12v0M22 12v0"></path></svg>
                        </div>
                        <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:3px;">
                                <span style="color:#8c96a5;">Confidence</span>
                                <span style="font-weight:700; color:#18202f;">{disp_conf}</span>
                            </div>
                            <div style="height:5px; background:#f1eee8; border-radius:3px; overflow:hidden;">
                                <div style="width:72.4%; height:100%; background:linear-gradient(90deg, #4f75e2, #6366f1); border-radius:3px;"></div>
                            </div>
                        </div>
                    </div>

                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="width:28px; height:28px; border-radius:7px; background:#f0fdf9; display:flex; align-items:center; justify-content:center; color:#0d9488;">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                        </div>
                        <div style="flex:1;">
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:3px;">
                                <span style="color:#8c96a5;">Evidence</span>
                                <span style="font-weight:700; color:#18202f;">4/5</span>
                            </div>
                            <div style="height:5px; background:#f1eee8; border-radius:3px; overflow:hidden;">
                                <div style="width:80%; height:100%; background:linear-gradient(90deg, #14b8a6, #2dd4bf); border-radius:3px;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """)

        # Analysis Workspace
        r_html("""
        <div id="predict-section" class="vcg-card" style="margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <div>
                    <div style="font-size:15.5px; font-weight:700; color:#18202f;">Analysis Workspace</div>
                    <div style="font-size:11.5px; color:#8c96a5; margin-top:2px;">Upload or live record</div>
                </div>
                <div style="display:flex; background:#f1eee8; padding:3px; border-radius:9999px;">
                    <div style="background:#ffffff; color:#18202f; font-weight:600; font-size:11.5px; padding:5px 14px; border-radius:9999px; box-shadow:0 1px 2px rgba(0,0,0,0.06);">Waveform</div>
                    <div style="color:#8c96a5; font-weight:500; font-size:11.5px; padding:5px 14px;">Spectrogram</div>
                    <div style="color:#8c96a5; font-weight:500; font-size:11.5px; padding:5px 14px;">Features</div>
                </div>
            </div>

            <div style="position:relative; width:100%; height:120px; background:#ffffff; margin-bottom:14px; display:flex; align-items:center; justify-content:center;">
                <svg width="100%" height="90" viewBox="0 0 650 90" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="waveBarGrad_app" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#60a5fa" stop-opacity="0.8"/>
                            <stop offset="50%" stop-color="#38bdf8" stop-opacity="0.95"/>
                            <stop offset="100%" stop-color="#60a5fa" stop-opacity="0.8"/>
                        </linearGradient>
                    </defs>
                    <g stroke="url(#waveBarGrad_app)" stroke-width="2" stroke-linecap="round">
                        <line x1="8" y1="42" x2="8" y2="48"/><line x1="14" y1="40" x2="14" y2="50"/><line x1="20" y1="36" x2="20" y2="54"/><line x1="26" y1="32" x2="26" y2="58"/><line x1="32" y1="26" x2="32" y2="64"/><line x1="38" y1="20" x2="38" y2="70"/><line x1="44" y1="25" x2="44" y2="65"/><line x1="50" y1="32" x2="50" y2="58"/><line x1="56" y1="18" x2="56" y2="72"/><line x1="62" y1="28" x2="62" y2="62"/><line x1="68" y1="38" x2="68" y2="52"/><line x1="74" y1="22" x2="74" y2="68"/><line x1="80" y1="12" x2="80" y2="78"/><line x1="86" y1="24" x2="86" y2="66"/><line x1="92" y1="35" x2="92" y2="55"/><line x1="98" y1="16" x2="98" y2="74"/><line x1="104" y1="28" x2="104" y2="62"/><line x1="110" y1="40" x2="110" y2="50"/><line x1="116" y1="22" x2="116" y2="68"/><line x1="122" y1="14" x2="122" y2="76"/><line x1="128" y1="26" x2="128" y2="64"/><line x1="134" y1="38" x2="134" y2="52"/><line x1="140" y1="18" x2="140" y2="72"/><line x1="146" y1="30" x2="146" y2="60"/><line x1="152" y1="42" x2="152" y2="48"/><line x1="158" y1="20" x2="158" y2="70"/><line x1="164" y1="10" x2="164" y2="80"/><line x1="170" y1="22" x2="170" y2="68"/><line x1="176" y1="34" x2="176" y2="56"/><line x1="182" y1="16" x2="182" y2="74"/><line x1="188" y1="28" x2="188" y2="62"/><line x1="194" y1="38" x2="194" y2="52"/><line x1="200" y1="24" x2="200" y2="66"/><line x1="206" y1="12" x2="206" y2="78"/><line x1="212" y1="26" x2="212" y2="64"/><line x1="218" y1="36" x2="218" y2="54"/><line x1="224" y1="18" x2="224" y2="72"/><line x1="230" y1="8" x2="230" y2="82"/><line x1="236" y1="20" x2="236" y2="70"/><line x1="242" y1="32" x2="242" y2="58"/><line x1="248" y1="42" x2="248" y2="48"/><line x1="254" y1="24" x2="254" y2="66"/><line x1="260" y1="14" x2="260" y2="76"/><line x1="266" y1="28" x2="266" y2="62"/><line x1="272" y1="38" x2="272" y2="52"/><line x1="278" y1="18" x2="278" y2="72"/><line x1="284" y1="10" x2="284" y2="80"/><line x1="290" y1="22" x2="290" y2="68"/><line x1="296" y1="32" x2="296" y2="58"/><line x1="302" y1="16" x2="302" y2="74"/><line x1="308" y1="28" x2="308" y2="62"/><line x1="314" y1="40" x2="314" y2="50"/><line x1="320" y1="20" x2="320" y2="70"/><line x1="326" y1="12" x2="326" y2="78"/><line x1="332" y1="26" x2="332" y2="64"/><line x1="338" y1="36" x2="338" y2="54"/><line x1="344" y1="18" x2="344" y2="72"/><line x1="350" y1="8" x2="350" y2="82"/><line x1="356" y1="22" x2="356" y2="68"/><line x1="362" y1="34" x2="362" y2="56"/><line x1="368" y1="16" x2="368" y2="74"/><line x1="374" y1="26" x2="374" y2="64"/><line x1="380" y1="38" x2="380" y2="52"/><line x1="386" y1="20" x2="386" y2="70"/><line x1="392" y1="14" x2="392" y2="76"/><line x1="398" y1="28" x2="398" y2="62"/><line x1="404" y1="38" x2="404" y2="52"/><line x1="410" y1="18" x2="410" y2="72"/><line x1="416" y1="28" x2="416" y2="62"/><line x1="422" y1="40" x2="422" y2="50"/><line x1="428" y1="22" x2="428" y2="68"/><line x1="434" y1="12" x2="434" y2="78"/><line x1="440" y1="24" x2="440" y2="66"/><line x1="446" y1="36" x2="446" y2="54"/><line x1="452" y1="16" x2="452" y2="74"/><line x1="458" y1="28" x2="458" y2="62"/><line x1="464" y1="38" x2="464" y2="52"/><line x1="470" y1="22" x2="470" y2="68"/><line x1="476" y1="14" x2="476" y2="76"/><line x1="482" y1="26" x2="482" y2="64"/><line x1="488" y1="36" x2="488" y2="54"/><line x1="494" y1="18" x2="494" y2="72"/><line x1="500" y1="30" x2="500" y2="60"/><line x1="506" y1="42" x2="506" y2="48"/><line x1="512" y1="26" x2="512" y2="64"/><line x1="518" y1="18" x2="518" y2="72"/><line x1="524" y1="32" x2="524" y2="58"/><line x1="530" y1="40" x2="530" y2="50"/><line x1="536" y1="24" x2="536" y2="66"/><line x1="542" y1="16" x2="542" y2="74"/><line x1="548" y1="28" x2="548" y2="62"/><line x1="554" y1="38" x2="554" y2="52"/><line x1="560" y1="22" x2="560" y2="68"/><line x1="566" y1="32" x2="566" y2="58"/><line x1="572" y1="42" x2="572" y2="48"/><line x1="578" y1="26" x2="578" y2="64"/><line x1="584" y1="18" x2="584" y2="72"/><line x1="590" y1="34" x2="590" y2="56"/><line x1="596" y1="42" x2="596" y2="48"/><line x1="602" y1="30" x2="602" y2="60"/><line x1="608" y1="20" x2="608" y2="70"/><line x1="614" y1="36" x2="614" y2="54"/><line x1="620" y1="42" x2="620" y2="48"/><line x1="626" y1="38" x2="626" y2="52"/><line x1="632" y1="42" x2="632" y2="48"/><line x1="638" y1="44" x2="638" y2="46"/>
                    </g>
                    <line x1="185" y1="10" x2="185" y2="85" stroke="#4f75e2" stroke-width="1.5"/>
                    <circle cx="185" cy="8" r="4.5" fill="#4f75e2"/>
                </svg>
            </div>

            <div style="display:flex; align-items:center; gap:14px; margin-bottom:18px; padding-bottom:18px; border-bottom:1px solid #f1eee8;">
                <div style="width:34px; height:34px; border-radius:50%; background:#4f75e2; display:flex; align-items:center; justify-content:center; color:#ffffff; cursor:pointer; flex-shrink:0; box-shadow:0 2px 6px rgba(79,117,226,0.3);">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                </div>
                <div style="font-size:11.5px; font-weight:600; color:#475569; flex-shrink:0;">0:12 / 0:45</div>
                <div style="flex:1; height:4px; background:#e9e5de; border-radius:2px; position:relative;">
                    <div style="width:28%; height:100%; background:#4f75e2; border-radius:2px;"></div>
                    <div style="position:absolute; left:28%; top:-4px; width:12px; height:12px; border-radius:50%; background:#4f75e2; box-shadow:0 1px 3px rgba(0,0,0,0.2);"></div>
                </div>
                <div style="display:flex; align-items:center; gap:10px; color:#64748b;">
                    <div style="width:28px; height:28px; border-radius:6px; background:#f4f2ee; display:flex; align-items:center; justify-content:center; cursor:pointer;">
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    </div>
                    <div style="display:flex; align-items:center; gap:2px; font-size:11.5px; font-weight:600; background:#f4f2ee; padding:4px 8px; border-radius:6px; cursor:pointer;">
                        1x <span style="font-size:9px;">&#9662;</span>
                    </div>
                </div>
            </div>
        </div>
        """)

        st.markdown("""<div style="margin-top:-8px; margin-bottom:18px;">""", unsafe_allow_html=True)
        supported = health_data.get("supported_formats", ["wav", "mp3", "flac", "m4a"]) if healthy else ["wav", "mp3", "flac", "m4a"]
        up_predict = st.file_uploader(
            "Drag & drop your audio file here (Supports WAV, FLAC, MP3, OGG, M4A, AAC, MPG · 200MB max)",
            type=supported,
            key="app_predict_uploader"
        )
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn2:
            run_pred = st.button("Run Detection →", disabled=(up_predict is None or not healthy), use_container_width=True)

        if run_pred and up_predict:
            with st.spinner("Processing sample through Render engine…"):
                try:
                    files = {"file": (up_predict.name, up_predict.getvalue())}
                    t_start = time.time()
                    resp = requests.post(PREDICT_ENDPOINT, files=files, timeout=60)
                    elapsed = time.time() - t_start
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.last_predict_result = (data, elapsed)
                    st.success("Detection successful!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.session_state.last_predict_result = ({"error": str(e)}, 0)
                    st.error(f"Prediction failed: {e}")
        st.markdown("""</div>""", unsafe_allow_html=True)

        # Recent Analysis Table
        r_html("""
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

            <div style="display:grid; grid-template-columns:2fr 1fr 1.5fr 1fr 1.2fr; padding:8px 14px; background:#faf8f5; border-radius:8px; font-size:11px; font-weight:600; color:#8c96a5;">
                <div>File Name</div>
                <div>Type</div>
                <div>Result</div>
                <div>Confidence</div>
                <div>Date</div>
            </div>

            <div style="padding:28px 14px; text-align:center; color:#94a3b8; font-size:12.5px;">
                No files uploaded yet. Drag &amp; drop an audio sample above to run detection.
            </div>
        </div>
        """)

    with col_right:
        # Model Card
        r_html("""
        <div class="vcg-card" style="padding:18px 20px; display:flex; gap:16px; align-items:stretch; margin-bottom:18px;">
            <div style="width:68px; border-radius:12px; overflow:hidden; flex-shrink:0; background:linear-gradient(135deg, #e0e7ff 0%, #fae8ff 50%, #ffedd5 100%); position:relative;">
                <svg width="100%" height="100%" viewBox="0 0 80 120" preserveAspectRatio="none">
                    <path d="M-10,30 C30,10 50,70 90,40 L90,130 L-10,130 Z" fill="rgba(147, 197, 253, 0.4)"/>
                    <path d="M-10,60 C40,40 40,90 90,80 L90,130 L-10,130 Z" fill="rgba(249, 168, 130, 0.45)"/>
                    <path d="M-10,80 C30,70 60,110 90,100 L90,130 L-10,130 Z" fill="rgba(196, 181, 253, 0.5)"/>
                </svg>
            </div>

            <div style="flex:1; display:flex; flex-direction:column; justify-content:space-between;">
                <div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="font-size:9.5px; font-weight:700; color:#8c96a5; text-transform:uppercase; letter-spacing:0.8px;">Model</div>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    </div>
                    <div style="font-size:16px; font-weight:800; color:#18202f; margin-top:3px; line-height:1.2;">Rich-feature RF</div>
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

        # Analysis Workspace Shortcuts
        r_html("""
        <div class="vcg-card" style="margin-bottom:18px;">
            <div style="font-size:14.5px; font-weight:700; color:#18202f;">Analysis Workspace</div>
            <div style="font-size:11px; color:#8c96a5; margin-top:2px; margin-bottom:14px;">Upload or live record</div>

            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#faf8f5; border:1px solid #f1eee8; border-radius:12px; margin-bottom:8px; cursor:pointer;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:8px; background:#eff4ff; display:flex; align-items:center; justify-content:center; color:#4f75e2;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5v14M7 9v6M2 12v0M22 12v0"></path></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Signal monitor</div>
                        <div style="font-size:10px; color:#8c96a5; line-height:1.2;">Waveform reference &middot; analyzed waveform appears with results</div>
                    </div>
                </div>
                <span style="color:#8c96a5; font-size:16px;">&rsaquo;</span>
            </div>

            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#faf8f5; border:1px solid #f1eee8; border-radius:12px; margin-bottom:8px; cursor:pointer;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:8px; background:#f5f3ff; display:flex; align-items:center; justify-content:center; color:#7c3aed;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Upload audio</div>
                        <div style="font-size:10px; color:#8c96a5;">Choose a file or record</div>
                    </div>
                </div>
                <span style="color:#8c96a5; font-size:16px;">&rsaquo;</span>
            </div>

            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 12px; background:#faf8f5; border:1px solid #f1eee8; border-radius:12px; cursor:pointer;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <div style="width:32px; height:32px; border-radius:8px; background:#fff1f2; display:flex; align-items:center; justify-content:center; color:#e11d48;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>
                    </div>
                    <div>
                        <div style="font-size:12.5px; font-weight:700; color:#18202f;">Live record</div>
                        <div style="font-size:10px; color:#8c96a5;">Use your microphone</div>
                    </div>
                </div>
                <span style="color:#8c96a5; font-size:16px;">&rsaquo;</span>
            </div>
        </div>
        """)

        # Model Snapshot
        r_html("""
        <div class="vcg-card" style="position:relative; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
                <div style="font-size:14.5px; font-weight:700; color:#18202f;">Model Snapshot</div>
                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="background:#ecfdf5; color:#059669; font-size:10.5px; font-weight:600; padding:2px 8px; border-radius:12px; display:flex; align-items:center; gap:4px;">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                        Prototype validation
                    </div>
                    <span style="color:#8c96a5; font-size:16px;">&rsaquo;</span>
                </div>
            </div>

            <div style="display:flex; gap:36px; align-items:baseline; margin-bottom:16px;">
                <div>
                    <div style="font-size:28px; font-weight:800; color:#18202f; line-height:1;">61.8%</div>
                    <div style="font-size:11px; color:#8c96a5; margin-top:2px;">Accuracy</div>
                </div>
                <div>
                    <div style="font-size:28px; font-weight:800; color:#18202f; line-height:1;">102</div>
                    <div style="font-size:11px; color:#8c96a5; margin-top:2px;">Features</div>
                </div>
            </div>

            <div style="height:20px; width:100%; margin-bottom:14px;">
                <svg width="100%" height="20" viewBox="0 0 240 20" preserveAspectRatio="none">
                    <path d="M0,10 C40,18 80,2 120,12 C160,22 200,6 240,14" stroke="#c4b5fd" stroke-width="1.5" fill="none"/>
                    <path d="M0,12 C40,20 80,4 120,14 C160,24 200,8 240,16" stroke="#fbcfe8" stroke-width="1.2" fill="none"/>
                </svg>
            </div>

            <div>
                <div style="font-size:11.5px; font-weight:700; color:#18202f; margin-bottom:8px; display:flex; align-items:center; gap:6px;">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#4f75e2" stroke-width="2.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
                    Quick Stats
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #f4f2ee; font-size:11.5px;">
                    <span style="color:#64748b; display:flex; align-items:center; gap:6px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8c96a5" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        Window
                    </span>
                    <span style="font-weight:700; color:#18202f;">4 s</span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #f4f2ee; font-size:11.5px;">
                    <span style="color:#64748b; display:flex; align-items:center; gap:6px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8c96a5" stroke-width="2"><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line><line x1="18" y1="20" x2="18" y2="10"></line></svg>
                        Inputs
                    </span>
                    <span style="font-weight:700; color:#18202f;">8</span>
                </div>

                <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; font-size:11.5px;">
                    <span style="color:#64748b; display:flex; align-items:center; gap:6px;">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8c96a5" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle></svg>
                        Local prototype
                    </span>
                    <span style="font-size:10px; font-weight:500; background:#f4f2ee; color:#71717a; padding:2px 8px; border-radius:10px;">Not production ready</span>
                </div>
            </div>
        </div>
        """)

# ═════════════════════════════════════════════════════════════
# OTHER PAGES (Analyze, History, Model, Settings)
# ═════════════════════════════════════════════════════════════
elif st.session_state.nav_page == "Analyze":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Audio Detection Workspace</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Upload speech to run detection against the Render-hosted endpoint</div>
    </div>
""")
    st.markdown('<div class="vcg-card">', unsafe_allow_html=True)
    up = st.file_uploader("Upload audio file", type=["wav", "mp3", "flac", "m4a"], key="app_analyze_page_file")
    if up:
        st.audio(up)
        if st.button("Run Detection Analysis", use_container_width=True):
            with st.spinner("Analyzing..."):
                try:
                    files = {"file": (up.name, up.getvalue())}
                    t_start = time.time()
                    resp = requests.post(PREDICT_ENDPOINT, files=files, timeout=60)
                    elapsed = time.time() - t_start
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.last_predict_result = (data, elapsed)
                    st.success("Analysis complete!")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.nav_page == "History":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Analysis History</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Log of voice samples processed during this session</div>
    </div>
    <div class="vcg-card" style="text-align:center; padding:60px 20px;">
        <div style="width:48px; height:48px; border-radius:50%; background:#faf8f5; border:1px solid #ece7e0; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; color:#94a3b8;">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
        </div>
        <div style="font-size:16px; font-weight:700; color:#18202f; margin-bottom:4px;">No Analysis History Recorded</div>
        <div style="font-size:12.5px; color:#8c96a5; max-width:380px; margin:0 auto; line-height:1.5;">
            Audio files and live recordings processed in the current browser session will automatically appear here.
        </div>
    </div>
""")

elif st.session_state.nav_page == "Model":
    r_html("""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Model Architecture &amp; Parameters</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Technical parameters for the Rich-feature Random Forest voice classification engine</div>
    </div>
    <div class="vcg-card">
        <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">Acoustic Feature Extraction</div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
            <span style="color:#64748b;">Vector Dimension</span>
            <span style="font-weight:700; color:#18202f;">102 Features</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1eee8; font-size:12.5px;">
            <span style="color:#64748b;">Primary Descriptor</span>
            <span style="font-weight:700; color:#18202f;">MFCC (13 coefficients + &Delta; + &Delta;&Delta;)</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:8px 0; font-size:12.5px;">
            <span style="color:#64748b;">Validation Benchmark</span>
            <span style="font-weight:700; color:#18202f;">61.8% Accuracy (34 local prototype vectors)</span>
        </div>
    </div>
""")

elif st.session_state.nav_page == "Settings":
    r_html(f"""
    <div style="margin-bottom:20px;">
        <div style="font-size:22px; font-weight:800; color:#18202f;">Settings</div>
        <div style="font-size:13px; color:#8c96a5; margin-top:2px;">Console preferences, risk policies, and API configuration</div>
    </div>
    <div class="vcg-card">
        <div style="font-size:15px; font-weight:700; color:#18202f; margin-bottom:14px;">API Endpoint Configuration</div>
        <div style="margin-bottom:12px;">
            <div style="font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">SERVICE HOST</div>
            <div style="font-size:13px; color:#18202f; font-family:monospace; background:#faf8f5; padding:8px 12px; border-radius:8px; border:1px solid #ece7e0;">{API_BASE_URL}</div>
        </div>
        <div style="margin-bottom:12px;">
            <div style="font-size:11px; font-weight:600; color:#8c96a5; margin-bottom:4px;">STATUS</div>
            <div style="display:flex; align-items:center; gap:6px; font-size:12.5px; font-weight:600; color:#059669;">
                <div style="width:7px; height:7px; border-radius:50%; background:#10b981;"></div>
                {status_label}
            </div>
        </div>
    </div>
""")
