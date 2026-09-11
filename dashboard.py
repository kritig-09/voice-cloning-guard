import hashlib
import math
import os
import tempfile
from datetime import datetime
from html import escape

import librosa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st

try:
    from app.feature_extractor import extract_features as repo_extract_features
except Exception:
    repo_extract_features = None


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
    {"name": "ceo_q4_earnings_memo.wav", "type": "WAV", "result": "ALLOW", "confidence": "97.4%", "date": "10 Sep 2025 · 07:12 PM"},
    {"name": "wire_transfer_auth_09.mp3", "type": "MP3", "result": "ESCALATE", "confidence": "94.8%", "date": "10 Sep 2025 · 06:45 PM"},
    {"name": "support_verification_call.m4a", "type": "M4A", "result": "VERIFY", "confidence": "68.2%", "date": "10 Sep 2025 · 05:30 PM"},
    {"name": "exec_briefing_session.flac", "type": "FLAC", "result": "ALLOW", "confidence": "96.1%", "date": "10 Sep 2025 · 04:15 PM"},
]

for key, default in {
    "live_rec_key": 0,
    "current_audio_bytes": None,
    "current_audio_name": "",
    "current_audio_duration": 0.0,
    "current_audio_hash": None,
    "processed_file_hash": None,
    "processed_mic_hash": None,
    "last_result": None,
    "last_mode": None,
    "last_time": None,
    "nav_page": "Home",
}.items():
    st.session_state.setdefault(key, default)

if "history" not in st.session_state:
    st.session_state.history = list(DEFAULT_HISTORY)

qp_page = st.query_params.get("page", None)
if qp_page in ["Home", "Analyze", "History", "Model", "Settings"]:
    st.session_state.nav_page = qp_page


@st.cache_data(ttl=60)
def check_engine_health():
    try:
        r = requests.get(f"{API_URL}/health", timeout=8)
        r.raise_for_status()
        return True, r.json()
    except Exception:
        return False, {}


online, health = check_engine_health()
dyn_features = int(health.get("feature_count", 102) or 102)
dyn_window = float(health.get("window_seconds", 4) or 4)
dyn_hop = float(health.get("hop_seconds", 1) or 1)
dyn_model_name = str(health.get("model_type", "Rich-feature RF") or "Rich-feature RF")
dyn_samples = health.get("training_sample_count")


def pct(v):
    return "—" if v is None else f"{float(v) * 100:.1f}%"


def audio_mime_for_name(name):
    ext = os.path.splitext(str(name or ""))[1].lower()
    return {
        ".wav": "audio/wav",
        ".flac": "audio/flac",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".mpg": "audio/mpeg",
        ".mpeg": "audio/mpeg",
    }.get(ext, "audio/wav")


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
        timeout=180,
    )
    r.raise_for_status()
    return r.json()


def r_html(content: str):
    st.markdown("".join(line.strip() for line in content.splitlines()), unsafe_allow_html=True)


def audio_signature(data: bytes):
    return hashlib.sha256(data).hexdigest() if data else None


def set_current_audio(data: bytes, name: str, duration: float | None = None):
    sig = audio_signature(data)
    st.session_state.current_audio_bytes = data
    st.session_state.current_audio_name = name
    st.session_state.current_audio_hash = sig
    if duration is not None:
        st.session_state.current_audio_duration = float(duration)
    elif sig:
        try:
            y, sr = load_audio(data, name)
            st.session_state.current_audio_duration = float(len(y) / max(sr, 1))
        except Exception:
            pass


@st.cache_data(show_spinner=False)
def load_audio(audio_bytes: bytes, filename: str):
    suffix = os.path.splitext(filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(audio_bytes)
        path = tmp.name
    try:
        y, sr = librosa.load(path, sr=16000, mono=True)
        if y.size == 0:
            raise ValueError("Audio is empty.")
        return y.astype(np.float32), int(sr)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def compute_waveform_bars(audio_bytes, filename="audio.wav", num_bars=76, height=68, bar_w=2.8, width=620):
    if not audio_bytes:
        t = np.linspace(0, 1, num_bars)
        amps = 0.2 + 0.72 * (np.sin(np.pi * t) ** 0.85)
        duration = 0.0
    else:
        try:
            y, sr = load_audio(audio_bytes, filename)
            duration = len(y) / max(sr, 1)
            edges = np.linspace(0, len(y), num_bars + 1, dtype=int)
            amps = np.array([np.sqrt(np.mean(np.square(y[edges[i]:edges[i + 1]]))) if edges[i + 1] > edges[i] else 0.0 for i in range(num_bars)])
            if np.max(amps) > 0:
                amps = amps / np.max(amps)
        except Exception:
            t = np.linspace(0, 1, num_bars)
            amps = 0.2 + 0.72 * (np.sin(np.pi * t) ** 0.85)
            duration = 0.0

    gap = (width - num_bars * bar_w) / max(num_bars - 1, 1)
    bars = []
    for i, amp in enumerate(np.clip(amps, 0, 1)):
        h = max(4.0, min(height - 4, round(height * (0.12 + 0.84 * float(amp)), 1)))
        x = round(i * (bar_w + gap), 1)
        y = round((height - h) / 2, 1)
        color = "#4f75e2" if i <= int(num_bars * 0.38) else "#93c5fd"
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_w}" height="{h}" rx="1.4" fill="{color}"/>')
    return "".join(bars), round(duration, 2)


def feature_names():
    names = []
    for family in ("MFCC", "Delta MFCC", "Delta2 MFCC"):
        names += [f"{family} {i + 1:02d} mean" for i in range(13)]
        names += [f"{family} {i + 1:02d} std" for i in range(13)]
    for family in ("Spectral centroid", "Spectral bandwidth", "Spectral rolloff", "Zero-crossing rate", "RMS energy"):
        names += [f"{family} mean", f"{family} std"]
    names += [f"Spectral contrast band {i + 1} mean" for i in range(7)]
    names += [f"Spectral contrast band {i + 1} std" for i in range(7)]
    return names


FEATURE_NAMES = feature_names()


def extract_feature_vector(y, sr):
    if repo_extract_features is not None:
        return np.asarray(repo_extract_features(y, sr), dtype=np.float32)

    y = np.asarray(y, dtype=np.float32)
    if y.size == 0:
        raise ValueError("Empty audio")
    if sr != 16000:
        y = librosa.resample(y, orig_sr=sr, target_sr=16000)
        sr = 16000
    peak = float(np.max(np.abs(y)))
    if peak == 0:
        raise ValueError("Audio is silent")
    y = y / peak
    features = []
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2) if mfcc.shape[1] >= 9 else np.gradient(delta, axis=1)
    for matrix in (mfcc, delta, delta2):
        features.extend(np.mean(matrix, axis=1).tolist())
        features.extend(np.std(matrix, axis=1).tolist())
    spectral = (
        librosa.feature.spectral_centroid(y=y, sr=sr),
        librosa.feature.spectral_bandwidth(y=y, sr=sr),
        librosa.feature.spectral_rolloff(y=y, sr=sr),
        librosa.feature.zero_crossing_rate(y),
        librosa.feature.rms(y=y),
    )
    for arr in spectral:
        features.extend([float(np.mean(arr)), float(np.std(arr))])
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    features.extend(np.mean(contrast, axis=1).tolist())
    features.extend(np.std(contrast, axis=1).tolist())
    return np.asarray(features, dtype=np.float32)


def feature_groups(vec):
    v = np.asarray(vec, dtype=float)
    groups = {
        "MFCC": np.mean(np.abs(v[0:26])),
        "Delta": np.mean(np.abs(v[26:52])),
        "Delta-delta": np.mean(np.abs(v[52:78])),
        "Spectral": np.mean(np.abs(v[78:88])),
        "Contrast": np.mean(np.abs(v[88:102])),
    }
    return groups


def get_active_analysis():
    data = st.session_state.get("current_audio_bytes")
    name = st.session_state.get("current_audio_name") or "audio.wav"
    if not data:
        return None
    try:
        y, sr = load_audio(data, name)
        vec = extract_feature_vector(y, sr)
        return {
            "y": y,
            "sr": sr,
            "features": vec,
            "duration": len(y) / max(sr, 1),
            "peak": float(np.max(np.abs(y))) if y.size else 0.0,
            "rms": float(np.sqrt(np.mean(np.square(y)))) if y.size else 0.0,
            "zcr": float(np.mean(librosa.feature.zero_crossing_rate(y))),
            "spectral_centroid": float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))),
        }
    except Exception as e:
        return {"error": str(e)}



def forensic_analysis(y, sr):
    """Compute additional explainable acoustic diagnostics for the active audio."""
    y = np.asarray(y, dtype=np.float32)
    if y.size < 512:
        raise ValueError("Audio is too short for forensic analysis.")

    hop = 256
    n_fft = 1024
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    S_norm = S / (np.sum(S, axis=0, keepdims=True) + 1e-9)

    # Spectral flux: frame-to-frame normalized spectral change.
    flux = np.sqrt(np.sum(np.diff(S_norm, axis=1) ** 2, axis=0))
    flux = np.concatenate([[0.0], flux])

    # Fundamental frequency and voiced fraction.
    f0 = librosa.yin(y, fmin=65.0, fmax=min(500.0, sr / 2 - 1), sr=sr, frame_length=1024, hop_length=hop)
    voiced = np.isfinite(f0)
    voiced_f0 = f0[voiced]

    # Harmonic/noise ratio proxy from harmonic-percussive separation.
    harmonic = librosa.effects.harmonic(y)
    residual = y - harmonic
    hrms = float(np.sqrt(np.mean(harmonic**2)) + 1e-9)
    nrms = float(np.sqrt(np.mean(residual**2)) + 1e-9)
    hnr_db = 10.0 * np.log10((hrms**2 + 1e-12) / (nrms**2 + 1e-12))

    # Formant approximation via LPC roots. Display only plausible resonances.
    formants = {"F1": np.nan, "F2": np.nan, "F3": np.nan}
    try:
        frame = y[:min(len(y), sr * 2)]
        frame = frame - np.mean(frame)
        order = min(18, max(8, int(sr / 1000)))
        a = librosa.lpc(frame, order=order)
        roots = np.roots(a)
        roots = roots[np.imag(roots) >= 0.01]
        freqs = np.angle(roots) * (sr / (2 * np.pi))
        bandwidths = -0.5 * (sr / (2 * np.pi)) * np.log(np.abs(roots))
        pairs = sorted([(float(f), float(b)) for f, b in zip(freqs, bandwidths)
                        if 90 <= f <= 5000 and 0 < b < 1000])
        vals = []
        for f, _ in pairs:
            if not vals or abs(f - vals[-1]) > 120:
                vals.append(f)
        for key, value in zip(("F1", "F2", "F3"), vals[:3]):
            formants[key] = value
    except Exception:
        pass

    frame_rms = librosa.feature.rms(y=y, frame_length=n_fft, hop_length=hop)[0]
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=n_fft, hop_length=hop)[0]
    rms_db = 20 * np.log10(np.maximum(frame_rms, 1e-8))

    # Lightweight jitter/shimmer proxies using consecutive voiced F0 periods.
    jitter_pct = np.nan
    shimmer_pct = np.nan
    if voiced_f0.size >= 4:
        periods = 1.0 / np.maximum(voiced_f0, 1e-6)
        jitter_pct = float(100 * np.mean(np.abs(np.diff(periods))) / max(np.mean(periods), 1e-9))
        voiced_idx = np.flatnonzero(voiced)
        sample_pos = np.clip((voiced_idx * hop).astype(int), 0, len(y) - 1)
        amps = np.abs(y[sample_pos])
        if amps.size >= 4 and np.mean(amps) > 1e-8:
            shimmer_pct = float(100 * np.mean(np.abs(np.diff(amps))) / np.mean(amps))

    # Segment-level consistency proxy: compare rich feature vectors across three temporal regions.
    thirds = np.array_split(y, 3)
    seg_vecs = []
    for seg in thirds:
        if len(seg) >= 512:
            try:
                seg_vecs.append(extract_feature_vector(seg, sr))
            except Exception:
                pass
    consistency = np.nan
    if len(seg_vecs) >= 2:
        sims=[]
        for i in range(len(seg_vecs)):
            for j in range(i+1,len(seg_vecs)):
                a,b=seg_vecs[i],seg_vecs[j]
                den=(np.linalg.norm(a)*np.linalg.norm(b))+1e-9
                sims.append(float(np.dot(a,b)/den))
        consistency=float(np.mean(sims))

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=n_fft, hop_length=hop, n_mels=64, fmax=min(8000, sr//2))
    mel_db = librosa.power_to_db(mel, ref=np.max)
    mfcc_mat = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, n_fft=n_fft, hop_length=hop)

    return {
        "spectrogram_db": mel_db,
        "mfcc": mfcc_mat,
        "f0": f0,
        "f0_voiced": voiced,
        "flux": flux,
        "hnr_db": float(hnr_db),
        "formants": formants,
        "jitter_pct": jitter_pct,
        "shimmer_pct": shimmer_pct,
        "rms_db": rms_db,
        "zcr": zcr,
        "voiced_ratio": float(np.mean(voiced)),
        "consistency": consistency,
        "duration": len(y)/max(sr,1),
        "sr": sr,
    }

def reset_recording():
    for k in ("last_result", "last_mode", "last_time", "current_audio_bytes", "current_audio_name", "current_audio_duration", "current_audio_hash"):
        st.session_state.pop(k, None)
    st.session_state.live_rec_key += 1
    st.session_state.processed_mic_hash = None
    st.rerun()


# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# EXACT-STYLE UI REBUILD — original product composition + live features
# ─────────────────────────────────────────────────────────────
st.markdown(r"""
<style>
:root{--bg:#f7f5f2;--white:#fff;--ink:#18202f;--muted:#8c96a5;--line:#e8e3dc;--panel:#faf8f5;--blue:#4f75e2;--lav:#c4b5fd;--peach:#fed7aa;--green:#059669}
html,body,.stApp{background:var(--bg)!important;color:var(--ink)!important;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif!important}
header,footer,#MainMenu,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
.block-container{max-width:1410px!important;padding:14px 25px 34px 28px!important}
section[data-testid="stSidebar"],section[data-testid="stSidebar"]>div,[data-testid="stSidebarContent"]{width:250px!important;min-width:250px!important;max-width:250px!important;background:#f7f5f2!important;border-right:1px solid #ebe6df!important;overflow:hidden!important;height:100vh!important;position:relative!important}
section[data-testid="stSidebar"]>div:first-child{padding:18px 11px!important;overflow:hidden!important}[data-testid="stSidebarCollapseButton"],[data-testid="collapsedControl"]{display:none!important}
.vcg-sidebar{height:calc(100vh - 36px);display:flex;flex-direction:column;justify-content:space-between;overflow:hidden}.brand-row{display:flex;align-items:center;gap:10px;padding:1px 3px 8px}.brand-title{font-size:15px;font-weight:800;line-height:1.15;color:#18202f}.brand-sub{font-size:9.5px;line-height:1.3;color:#8c96a5;margin-top:2px}.sidebar-wave{margin:36px 4px 16px}
.nav-link{display:flex;align-items:center;gap:11px;padding:9px 12px;border-radius:11px;color:#64748b!important;font-size:13px;font-weight:600;text-decoration:none!important;margin:2px 0}.nav-link:hover,.nav-link.active{background:#e9e5de!important;color:#18202f!important}
.topline{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}.search-shell{display:flex;align-items:center;gap:10px;width:440px;height:40px;background:#fff;border:1px solid #e7e1d9;border-radius:999px;padding:0 14px;box-shadow:0 1px 2px rgba(0,0,0,.025)}.search-icon{font-size:16px;color:#8c96a5}.search-copy{font-size:11px;color:#94a3b8;flex:1}.search-shortcut{font-size:10px;color:#94a3b8;border:1px solid #e2ddd5;background:#faf8f5;border-radius:7px;padding:3px 7px}.top-meta{display:flex;align-items:center;gap:12px;font-size:11px;color:#8c96a5}.engine-pill{display:inline-flex;align-items:center;gap:6px;border:1px solid #b7efd5;background:#effcf6;color:#059669;border-radius:999px;padding:7px 11px;font-weight:700}.engine-dot{width:6px;height:6px;border-radius:50%;background:#10b981}.avatar{width:32px;height:32px;border-radius:50%;background:#64748b;color:#fff;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800}
.hero-grid{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:16px}.hero{position:relative;height:250px;background:#fff;border:1px solid #e8e3dc;border-radius:20px;overflow:hidden;padding:30px 35px;box-shadow:0 2px 10px rgba(0,0,0,.025)}.hero-eyebrow{font-size:9px;letter-spacing:.18em;font-weight:800;color:#7990b7;text-transform:uppercase}.hero h1{font-family:"Playfair Display",Georgia,serif;font-size:49px;line-height:.98;letter-spacing:-.035em;margin:10px 0 11px;color:#18202f}.hero-copy{font-size:12px;line-height:1.55;color:#718095;max-width:560px}.hero-script{position:absolute;right:31px;top:25px;font-family:"Caveat",cursive;color:#26324a;font-size:25px;line-height:.9;text-align:right;transform:rotate(-2deg)}.underline{display:block;width:78px;height:1px;background:#7d8795;margin:7px 0 0 auto}.hero-art{position:absolute;left:34%;right:-7%;bottom:-3px;height:137px}.hero-art svg{position:absolute;inset:0;width:100%;height:100%}.hero-fill{position:absolute;left:9%;right:6%;bottom:0;height:104px;background:linear-gradient(90deg,rgba(100,120,243,.23),rgba(183,187,244,.19),rgba(254,215,170,.30));clip-path:polygon(0 72%,8% 48%,19% 68%,30% 53%,44% 45%,57% 52%,68% 77%,82% 84%,91% 64%,100% 28%,100% 100%,0 100%)}
.side-card{background:#fff;border:1px solid #e8e3dc;border-radius:18px;padding:17px 18px;box-shadow:0 2px 10px rgba(0,0,0,.025)}.model-wrap{display:grid;grid-template-columns:76px 1fr;gap:13px;align-items:center}.model-thumb{height:116px;border-radius:13px;background:linear-gradient(180deg,#ede8ff 0%,#ede8ff 41%,#d4c6e6 41%,#efc7b8 70%,#dbc8e8 70%,#dbc8e8 100%);position:relative;overflow:hidden}.model-thumb:before{content:"";position:absolute;left:-24px;right:-18px;top:24px;height:51px;background:#bed0f4;opacity:.78;clip-path:polygon(0 10%,23% 35%,42% 10%,63% 33%,86% 20%,100% 44%,100% 66%,83% 48%,63% 64%,44% 40%,21% 68%,0 52%)}.model-label{font-size:8.5px;letter-spacing:.1em;text-transform:uppercase;color:#8c96a5;font-weight:800}.model-name{font-size:17px;font-weight:800;margin-top:4px;line-height:1.08}.model-note{font-size:9.5px;line-height:1.35;color:#8c96a5;margin-top:3px}.action-row{display:flex;gap:6px;margin-top:11px}.chip{background:#f7f5f2;color:#64748b;border-radius:999px;padding:4px 7px;font-size:8.5px;font-weight:700}
.card{background:#fff;border:1px solid #e8e3dc;border-radius:18px;box-shadow:0 2px 10px rgba(0,0,0,.025);padding:19px 24px}.section-title{font-size:15px;font-weight:800;color:#18202f}.section-sub{font-size:10px;color:#8c96a5;margin-top:4px}.overview-grid{display:grid;grid-template-columns:190px 1fr 220px;gap:20px;align-items:center;margin-top:17px}.donut{width:118px;height:118px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:conic-gradient(#3da1ef 0deg 222deg,#ebe8e2 222deg 360deg);position:relative;margin:auto}.donut:after{content:"";width:88px;height:88px;border-radius:50%;background:#fff;position:absolute}.donut-inner{position:relative;z-index:2;text-align:center}.donut-num{font-size:23px;font-weight:800}.donut-label{font-size:8px;color:#8c96a5;margin-top:2px}.mini-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.mini{background:#faf8f5;border:1px solid #ece6de;border-radius:11px;padding:11px 8px;text-align:center}.mini-label{font-size:8.5px;color:#8c96a5}.mini-value{font-size:15px;font-weight:800;margin-top:3px}.result-pill{display:inline-flex;align-items:center;gap:6px;background:#effcf6;color:#059669;border:1px solid #b7efd5;border-radius:999px;padding:7px 11px;font-size:9.5px;font-weight:800}.result-dot{width:6px;height:6px;border-radius:50%;background:#10b981}.bars-box{background:#faf8f5;border:1px solid #ece6de;border-radius:12px;padding:10px 12px}.bar-line{display:flex;justify-content:space-between;font-size:9px;color:#64748b;margin-bottom:6px}.track{height:5px;background:#e7e3dd;border-radius:999px;overflow:hidden}.fill-blue{height:100%;background:#6d6df6}.fill-teal{height:100%;background:#13b4ab}
.workspace-grid{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:16px;margin-top:16px}.right-stack{display:flex;flex-direction:column;gap:16px}.quick-card,.snapshot{background:#fff;border:1px solid #e8e3dc;border-radius:18px;padding:17px 18px;box-shadow:0 2px 10px rgba(0,0,0,.025)}.quick-item{display:flex;justify-content:space-between;align-items:center;border:1px solid #ece6de;background:#fff;border-radius:12px;padding:10px 11px;margin-top:8px}.qi-left{display:flex;gap:9px;align-items:center}.qi-icon{width:30px;height:30px;border-radius:9px;background:#eff4ff;color:#4f75e2;display:flex;align-items:center;justify-content:center;font-weight:800}.qi-name{font-size:11px;font-weight:800}.qi-note{font-size:9px;color:#8c96a5;margin-top:2px}.arrow{font-size:15px;color:#94a3b8}.snapshot-head{display:flex;justify-content:space-between;align-items:center}.snapshot-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:17px}.snapshot-big{font-size:22px;font-weight:800}.snapshot-label{font-size:8.5px;color:#8c96a5;margin-top:2px}.snapshot-wave{height:37px;margin-top:15px;background:linear-gradient(90deg,#eeeaff,#dfe9fb,#faf0e6);clip-path:polygon(0 76%,13% 57%,28% 68%,41% 56%,56% 64%,72% 38%,88% 57%,100% 46%,100% 100%,0 100%);border-radius:6px}
/* Workbench / Streamlit tabs — force readable contrast for every state */
div[data-testid="stTabs"] [data-baseweb="tab-list"]{background:transparent!important;gap:21px!important;padding:0!important;border-bottom:1px solid #e5dfd7!important}
div[data-testid="stTabs"] [data-baseweb="tab"]{padding:9px 4px 11px!important;background:transparent!important;border:none!important;color:#475569!important;font-size:11px!important;font-weight:650!important;opacity:1!important;text-shadow:none!important;-webkit-text-fill-color:#475569!important}
div[data-testid="stTabs"] [data-baseweb="tab"] *{color:#475569!important;opacity:1!important;text-shadow:none!important;-webkit-text-fill-color:#475569!important}
div[data-testid="stTabs"] [data-baseweb="tab"]:hover{color:#18202f!important;background:#f1eee8!important;border-radius:8px 8px 0 0!important}
div[data-testid="stTabs"] [data-baseweb="tab"]:hover *{color:#18202f!important;-webkit-text-fill-color:#18202f!important}
div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"]{color:#4f75e2!important;font-weight:800!important;border-bottom:2px solid #4f75e2!important}
div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] *{color:#4f75e2!important;-webkit-text-fill-color:#4f75e2!important}
div[data-testid="stTabs"] [data-baseweb="tab"]:focus-visible{outline:2px solid #9fb4ff!important;outline-offset:2px!important}
div[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none!important}

/* Native controls: high-contrast, always-readable interactive elements */
.control-divider{height:1px;background:#e6e1d9;margin:2px 0 10px}
div[data-testid="stButton"]{opacity:1!important}
div[data-testid="stButton"] > button,
div[data-testid="stButton"] button,
button[kind="primary"],button[kind="secondary"]{
    min-height:38px!important;
    opacity:1!important;
    visibility:visible!important;
    color:#18202f!important;
    -webkit-text-fill-color:#18202f!important;
    background:#ffffff!important;
    border:1px solid #d8d2c9!important;
    border-radius:10px!important;
    font-weight:800!important;
    font-size:12px!important;
    line-height:1.15!important;
    padding:9px 14px!important;
    box-shadow:0 1px 3px rgba(24,32,47,.06)!important;
}
div[data-testid="stButton"] > button:hover,
div[data-testid="stButton"] button:hover{
    color:#18202f!important;
    -webkit-text-fill-color:#18202f!important;
    background:#f1eee8!important;
    border-color:#bdb5aa!important;
}
div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[aria-pressed="true"]{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    background:#4f75e2!important;
    border-color:#4f75e2!important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover,
div[data-testid="stButton"] > button[aria-pressed="true"]:hover{
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    background:#3f63c7!important;
    border-color:#3f63c7!important;
}
div[data-testid="stButton"] p,
div[data-testid="stButton"] span,
div[data-testid="stButton"] div{color:inherit!important;-webkit-text-fill-color:inherit!important;opacity:1!important;visibility:visible!important}

/* Buttons: primary actions, uploader controls, microphone controls, expanders */
div[data-testid="stButton"] > button, div.stButton > button{min-height:38px!important;background:#18202f!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;border:1px solid #18202f!important;border-radius:999px!important;font-weight:800!important;font-size:11px!important;padding:9px 18px!important;opacity:1!important;box-shadow:0 2px 7px rgba(24,32,47,.12)!important}
div[data-testid="stButton"] > button:hover, div.stButton > button:hover{background:#2a3447!important;color:#ffffff!important;-webkit-text-fill-color:#ffffff!important;border-color:#2a3447!important}
div[data-testid="stButton"] > button:focus-visible, div.stButton > button:focus-visible{outline:2px solid #9fb4ff!important;outline-offset:2px!important}
[data-testid="stFileUploaderDropzone"]{background:#faf8f5!important;border:1px dashed #c9c1b6!important;border-radius:13px!important;padding:14px!important;opacity:1!important}
[data-testid="stFileUploaderDropzone"] *{color:#475569!important;-webkit-text-fill-color:#475569!important;opacity:1!important}
[data-testid="stFileUploaderDropzone"] button,[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"]{background:#ffffff!important;color:#18202f!important;-webkit-text-fill-color:#18202f!important;border:1px solid #d8d2c9!important;opacity:1!important;box-shadow:none!important}
[data-testid="stAudioInput"]{background:#faf8f5!important;border:1px dashed #c9c1b6!important;border-radius:13px!important;padding:12px!important;opacity:1!important}
[data-testid="stAudioInput"] *{color:#475569!important;-webkit-text-fill-color:#475569!important;opacity:1!important}
[data-testid="stAudioInput"] button{background:#ffffff!important;color:#18202f!important;-webkit-text-fill-color:#18202f!important;border:1px solid #d8d2c9!important;opacity:1!important}
div[data-testid="stExpander"] summary{color:#334155!important;opacity:1!important;font-weight:700!important}
div[data-testid="stExpander"] summary *{color:#334155!important;-webkit-text-fill-color:#334155!important;opacity:1!important}

/* Sidebar navigation: keep labels separated and readable */
.vcg-sidebar .nav-link{display:flex!important;align-items:center!important;gap:10px!important;width:100%!important;box-sizing:border-box!important;padding:9px 12px!important;margin:3px 0!important;border-radius:11px!important;color:#475569!important;-webkit-text-fill-color:#475569!important;font-size:13px!important;font-weight:650!important;text-decoration:none!important;opacity:1!important}
.vcg-sidebar .nav-link span{color:inherit!important;-webkit-text-fill-color:inherit!important;opacity:1!important}
.vcg-sidebar .nav-link:hover{background:#ece8e1!important;color:#18202f!important;-webkit-text-fill-color:#18202f!important}
.vcg-sidebar .nav-link.active{background:#e9e5de!important;color:#18202f!important;-webkit-text-fill-color:#18202f!important}

.visual-card{background:#fff;border:1px solid #e9e4dc;border-radius:15px;padding:14px 17px}.visual-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.visual-name{font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.04em}.visual-tag{font-size:8.5px;color:#4f75e2;background:#eff4ff;border-radius:6px;padding:4px 7px;font-weight:700}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.feature-card{background:#faf8f5;border:1px solid #ece6de;border-radius:11px;padding:10px}.feature-title{font-size:8.5px;color:#8c96a5}.feature-value{font-size:15px;font-weight:800;margin-top:4px}.feature-unit{font-size:8.5px;color:#94a3b8;margin-left:3px}
[data-testid="stFileUploader"] section,[data-testid="stFileUploaderDropzone"]{background:#faf8f5!important;border:1px dashed #d8d2c9!important;border-radius:13px!important;padding:14px!important}[data-testid="stFileUploaderDropzone"] *{color:#64748b!important;opacity:1!important}[data-testid="stAudioInput"]{background:#faf8f5!important;border:1px dashed #d8d2c9!important;border-radius:13px!important;padding:12px!important}[data-testid="stAudioInput"] *{color:#64748b!important;opacity:1!important}div.stButton>button{background:#18202f!important;color:#fff!important;border:none!important;border-radius:999px!important;font-weight:700!important;font-size:11px!important;padding:9px 18px!important;box-shadow:0 2px 7px rgba(24,32,47,.12)!important}
.vcg-footer{border-top:1px solid #e7e1da;margin-top:21px;padding-top:11px;color:#9aa3ad;font-size:9px;line-height:1.5}.explain-card{background:#f6f8fc;border:1px solid #dfe7f5;border-left:3px solid #4f75e2;border-radius:12px;padding:11px 13px;margin:10px 0 12px}.explain-title{font-size:10px;font-weight:800;color:#25324a;margin-bottom:4px}.explain-copy{font-size:10px;line-height:1.55;color:#526174}.explain-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:9px 0 12px}.explain-mini{background:#fbfaf8;border:1px solid #ebe5dc;border-radius:10px;padding:9px 10px}.explain-mini b{display:block;font-size:9px;color:#25324a;margin-bottom:3px}.explain-mini span{font-size:9px;line-height:1.45;color:#667487}.section-hint{font-size:9px;color:#7b8794;line-height:1.5;margin-top:-2px;margin-bottom:9px}@media(max-width:850px){.explain-grid{grid-template-columns:1fr}}
@media(max-width:1050px){.hero-grid,.workspace-grid{grid-template-columns:1fr}.overview-grid{grid-template-columns:150px 1fr}.overview-grid>div:last-child{grid-column:1/-1}.topline{flex-wrap:wrap;gap:12px}.search-shell{width:min(440px,100vw - 300px)}}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    curr=st.session_state.nav_page
    acts={p:(" active" if curr==p else "") for p in ["Home","Analyze","History","Model","Settings"]}
    r_html("""
    <div class="vcg-sidebar">
      <div>
        <div class="brand-row"><svg width="25" height="25" viewBox="0 0 28 28" fill="none"><rect x="2" y="10" width="3" height="8" rx="1.5" fill="#4f75e2"/><rect x="7.5" y="6" width="3" height="16" rx="1.5" fill="#4f75e2"/><rect x="13" y="2" width="3" height="24" rx="1.5" fill="#4f75e2"/><rect x="18.5" y="7" width="3" height="14" rx="1.5" fill="#4f75e2"/><rect x="24" y="11" width="3" height="6" rx="1.5" fill="#4f75e2"/></svg><div><div class="brand-title">VoiceCloneGuard</div><div class="brand-sub">Voice authenticity &amp;<br>impersonation risk console</div></div></div>
        <div class="sidebar-wave"><svg width="100%" height="48" viewBox="0 0 220 48" fill="none"><defs><linearGradient id="sw" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#93c5fd" stop-opacity=".35"/><stop offset=".55" stop-color="#c4b5fd" stop-opacity=".45"/><stop offset="1" stop-color="#fed7aa" stop-opacity=".35"/></linearGradient></defs><path d="M0 31 C42 16 72 38 116 27 C160 16 190 31 220 20 L220 48 L0 48Z" fill="url(#sw)"/><path d="M0 34 C48 20 76 35 122 24 C168 14 196 28 220 21" stroke="#7a87e8" stroke-opacity=".65" stroke-width="1.4" fill="none"/></svg></div>
        <a href="?page=Home" target="_self" class="nav-link{acts['Home']}">⌂<span>Home</span></a><a href="?page=Analyze" target="_self" class="nav-link{acts['Analyze']}">◌<span>Analyze</span></a><a href="?page=History" target="_self" class="nav-link{acts['History']}">◷<span>History</span></a><a href="?page=Model" target="_self" class="nav-link{acts['Model']}">◫<span>Model</span></a><a href="?page=Settings" target="_self" class="nav-link{acts['Settings']}">⚙<span>Settings</span></a>
      </div>
      <div style="position:relative;overflow:hidden;background:rgba(255,255,255,.72);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.92);border-radius:14px;padding:12px;box-shadow:0 2px 10px rgba(0,0,0,.03);"><div style="font-size:11.5px;font-weight:700;color:#18202f;line-height:1.35;margin-bottom:7px;">A safer digital world<br>starts with authentic<br>voices.</div><div style="font-size:10px;font-weight:600;color:#475569;">Learn more →</div></div>
    </div>
    """)

# Top search/status row
health_text="Engine Online" if online else "Engine Offline"
r_html(f"""<div class="topline"><div class="search-shell"><div class="search-icon">⌕</div><div class="search-copy">Search for analysis, files or model…</div><div class="search-shortcut">⌘ K</div></div><div class="top-meta"><div class="engine-pill"><span class="engine-dot"></span>{health_text}</div><div>SIH 26104</div><div style="color:#d7d0c8">|</div><div>Build 0.3</div><div class="avatar">SK</div><div style="font-size:10px;color:#94a3b8">⌄</div></div></div>""")

# hero
r_html(f"""<div class="hero-grid"><div class="hero"><div class="hero-eyebrow">AI voice security &amp; imposter detection</div><h1>VoiceCloneGuard</h1><div class="hero-copy">Advanced voice authenticity check for impersonation risk scenarios.<br>Make safer decisions with AI-powered analysis.</div><div class="hero-script">Real voices.<br>Real people.<span class="underline"></span></div><div class="hero-art"><div class="hero-fill"></div><svg viewBox="0 0 760 150" preserveAspectRatio="none" fill="none"><path d="M0 107 C82 62 145 124 245 88 C354 48 416 41 500 81 C592 127 670 116 760 58" stroke="#86a6f7" stroke-width="2" stroke-opacity=".72"/><path d="M0 115 C90 68 152 132 252 96 C370 55 428 48 508 88 C592 132 674 122 760 68" stroke="#a58cf3" stroke-width="1.5" stroke-opacity=".52"/><path d="M34 96 C100 70 170 92 252 80 C338 66 420 54 500 72 C596 92 670 110 760 70" stroke="#f0a48b" stroke-width="1.4" stroke-opacity=".5"/><path d="M18 82 C94 58 165 80 238 72 C330 62 420 34 508 58 C602 84 670 98 748 52" stroke="#b9cafa" stroke-width="1" stroke-opacity=".8"/></svg></div></div><div class="side-card"><div class="model-wrap"><div class="model-thumb"></div><div><div class="model-label">Model</div><div class="model-name">{escape(dyn_model_name)}</div><div class="model-note">MFCC, delta and spectral statistics</div><div class="model-label" style="margin-top:13px;">Security Response</div><div class="action-row"><span class="chip">Allow</span><span class="chip">Verify</span><span class="chip">Escalate</span></div></div></div></div></div>""")

last=st.session_state.get("last_result")
analysis=get_active_analysis()
if last and "final" in last:
    final=last.get("final",{}); dc,dl,dd=decision(final.get("action")); risk=float(final.get("risk_score",0) or 0); spoof=float(final.get("spoof_probability",0) or 0); conf=float(final.get("confidence",0) or 0); result_label=dl; overview_value=conf*100; evidence=int(round(risk*5)); last_time=st.session_state.get("last_time") or "Latest analysis"
else:
    dc="allow";dd="Analyze an audio sample to generate a result.";risk=0;spoof=0;conf=0;result_label="Awaiting analysis";overview_value=0;evidence=0;last_time="No analysis yet"

# detection overview
r_html(f"""<div style="height:16px"></div><div class="card"><div style="display:flex;justify-content:space-between;align-items:center;"><div><div class="section-title">Detection Overview</div><div class="section-sub">Quick insights into your latest analysis</div></div><div style="display:flex;align-items:center;gap:9px;font-size:9px;color:#8c96a5;"><span class="result-pill"><span class="result-dot"></span>Live</span><span>{escape(last_time)}</span><span style="font-size:15px">⋮</span></div></div><div class="overview-grid"><div><div class="donut" style="background:conic-gradient(#3da1ef 0deg {min(360,max(8,overview_value/100*360)):.1f}deg,#ebe8e2 {min(360,max(8,overview_value/100*360)):.1f}deg 360deg)"><div class="donut-inner"><div class="donut-num">{overview_value:.1f}%</div><div class="donut-label">Confidence</div></div></div></div><div><div class="mini-grid"><div class="mini"><div class="mini-label">Features</div><div class="mini-value">{dyn_features}</div></div><div class="mini"><div class="mini-label">Window</div><div class="mini-value">{dyn_window:.0f}s</div></div><div class="mini"><div class="mini-label">Inputs</div><div class="mini-value">8</div></div></div><div style="margin-top:13px"><span class="result-pill"><span class="result-dot"></span>{escape(result_label)}</span></div><div style="font-size:9px;color:#8c96a5;margin-top:7px">{escape(dd)}</div></div><div class="bars-box"><div class="bar-line"><span>Confidence</span><b>{conf*100:.1f}%</b></div><div class="track"><div class="fill-blue" style="width:{max(5,conf*100):.1f}%"></div></div><div style="height:11px"></div><div class="bar-line"><span>Evidence</span><b>{evidence}/5</b></div><div class="track"><div class="fill-teal" style="width:{max(5,(risk*100 if last else 80)):.1f}%"></div></div></div></div></div>""")

# workspace title + robust two-column composition
current_bytes=st.session_state.get("current_audio_bytes"); current_name=st.session_state.get("current_audio_name") or "No active audio"
if analysis and "error" not in analysis: bars_svg,_=compute_waveform_bars(current_bytes,current_name); duration=float(analysis["duration"])
else: bars_svg,_=compute_waveform_bars(None); duration=float(st.session_state.get("current_audio_duration",45.0) or 45.0)

st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
left_col, right_col = st.columns([1.0, 0.34], gap="medium")

with left_col:
    r_html("<div class='card' style='padding-bottom:13px'><div class='section-title'>Analysis Workspace</div><div class='section-sub'>Upload or live record</div></div>")
    st.session_state.setdefault("ws_panel", "Waveform")
    ws_names=["Waveform","Spectrogram","Forensics","Features"]
    ws_cols=st.columns(4, gap="small")
    for idx, (col, name) in enumerate(zip(ws_cols, ws_names)):
        with col:
            if st.button(name, key=f"ws_{name.lower()}", use_container_width=True, type="primary" if st.session_state.ws_panel==name else "secondary"):
                st.session_state.ws_panel=name
                st.rerun()
    st.markdown("<div class='control-divider'></div>", unsafe_allow_html=True)
    ws_tab=st.session_state.ws_panel
    if ws_tab == "Waveform":
        r_html("""<div class='explain-card'><div class='explain-title'>What does this tell us?</div><div class='explain-copy'>The waveform shows the audio signal's amplitude over time. Taller regions mean stronger signal energy; quieter regions indicate softer speech or silence.</div><div class='explain-grid'><div class='explain-mini'><b>What to look for</b><span>Speech rhythm, pauses, clipping, and abrupt amplitude changes.</span></div><div class='explain-mini'><b>Why it matters</b><span>It gives a quick view of signal quality before deeper acoustic analysis.</span></div></div></div>""")
        r_html(f"""<div class='visual-card' style='margin-top:12px'><div class='visual-head'><div class='visual-name'>Spectrum Monitor: {escape(current_name)}</div><div class='visual-tag'>76 Dynamic Bins · Actual Audio</div></div><svg width='100%' height='82' viewBox='0 0 620 82' preserveAspectRatio='none' fill='none'><line x1='0' y1='41' x2='620' y2='41' stroke='#ece8e1'/>{bars_svg}</svg><div style='display:flex;justify-content:space-between;font-size:9px;color:#94a3b8'><span>0:00</span><span>{int(duration)//60}:{int(duration)%60:02d}</span></div></div>""")
        if current_bytes: st.audio(current_bytes,format=audio_mime_for_name(current_name))

    elif ws_tab == "Spectrogram":
        if analysis and "error" not in analysis:
            fa=forensic_analysis(analysis["y"],analysis["sr"])
            r_html("""<div class='explain-card'><div class='explain-title'>What does this tell us?</div><div class='explain-copy'>The spectrogram shows where sound energy sits across frequency and time. The MFCC map compresses that spectral shape into numbers used by the detector.</div><div class='explain-grid'><div class='explain-mini'><b>Mel spectrogram</b><span>Brighter regions represent stronger acoustic energy.</span></div><div class='explain-mini'><b>MFCC map</b><span>Summarizes the speech spectrum as a compact feature representation.</span></div></div></div>""")
            fig,ax=plt.subplots(figsize=(10,3.15))
            img=librosa.display.specshow(fa["spectrogram_db"],sr=fa["sr"],hop_length=256,x_axis='time',y_axis='mel',ax=ax,cmap='magma',fmax=min(8000,fa["sr"]//2))
            ax.set_title('Real-time Mel-frequency spectrogram',fontsize=10,color='#18202f',loc='left',pad=8)
            ax.set_xlabel('Time'); ax.set_ylabel('Frequency')
            fig.colorbar(img,ax=ax,format='%+2.0f dB',pad=.01)
            fig.patch.set_facecolor('white'); ax.set_facecolor('#faf8f5'); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)
            r_html(f"<div style='font-size:9px;color:#8c96a5'>FFT 1024 · hop 256 · {fa['sr']:,} Hz · actual active audio</div>")
            r_html("<div class='section-hint'><b>How to read it:</b> left to right = time; bottom to top = frequency; brighter = stronger energy.</div>")
            st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
            fig,ax=plt.subplots(figsize=(10,2.5))
            librosa.display.specshow(fa["mfcc"],x_axis='time',ax=ax,cmap='viridis');ax.set_title('MFCC coefficient map',fontsize=10,color='#18202f',loc='left',pad=8);ax.set_ylabel('MFCC');fig.patch.set_facecolor('white');ax.set_facecolor('#faf8f5');fig.tight_layout();st.pyplot(fig,use_container_width=True);plt.close(fig)
        else:
            r_html("<div class='visual-card' style='margin-top:12px;color:#8c96a5;font-size:10px'>Analyze audio to generate the spectrogram and MFCC heatmap.</div>")

    elif ws_tab == "Forensics":
        if analysis and "error" not in analysis:
            fa=forensic_analysis(analysis["y"],analysis["sr"])
            r_html("<div class='explain-card'><div class='explain-title'>What do these measurements tell us?</div><div class='explain-copy'>These are supporting acoustic diagnostics. They describe pitch, harmonic structure, spectral change, resonance, and voice-cycle variability. They are interpreted together with the detector score, not as standalone proof of genuine or synthetic audio.</div></div>")
            c1,c2,c3=st.columns(3)
            metrics=[(c1,'Voiced ratio',fa['voiced_ratio']*100,'%', '#4f75e2'),(c2,'HNR',fa['hnr_db'],' dB','#8b5cf6'),(c3,'Spectral flux',float(np.mean(fa['flux'])),'','#e11d48')]
            for col,label,val,unit,_ in metrics:
                with col: st.markdown(f"<div class='feature-card' style='text-align:center'><div class='feature-title'>{label}</div><div class='feature-value'>{val:.2f}<span class='feature-unit'>{unit}</span></div></div>",unsafe_allow_html=True)
            r_html("<div class='explain-grid'><div class='explain-mini'><b>Voiced ratio</b><span>How much of the recording is detected as voiced speech.</span></div><div class='explain-mini'><b>HNR</b><span>Compares harmonic voice energy with noise-like energy.</span></div><div class='explain-mini'><b>Spectral flux</b><span>Measures how quickly the spectrum changes from frame to frame.</span></div><div class='explain-mini'><b>Why they matter</b><span>They provide additional acoustic context alongside the main model score.</span></div></div>")
            st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
            fig,ax=plt.subplots(figsize=(10,2.55));
            t=np.arange(len(fa['f0']))*256/fa['sr']; ax.plot(t,np.where(np.isfinite(fa['f0']),fa['f0'],np.nan),linewidth=1.1); ax.set_title('Fundamental frequency (F0)',fontsize=10,color='#18202f',loc='left'); ax.set_xlabel('Time (s)'); ax.set_ylabel('Hz'); ax.grid(alpha=.15); fig.patch.set_facecolor('white'); ax.set_facecolor('#faf8f5'); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)
            r_html("<div class='section-hint'><b>F0 / pitch:</b> shows how the speaker's fundamental pitch changes over time. It describes prosody and voice behavior; it is not a speaker-identity test.</div>")
            f1,f2,f3=st.columns(3)
            for col,key in [(f1,'F1'),(f2,'F2'),(f3,'F3')]:
                with col:
                    val=fa['formants'][key]
                    st.markdown(f"<div class='feature-card' style='text-align:center'><div class='feature-title'>{key} formant</div><div class='feature-value'>{'—' if np.isnan(val) else f'{val:.0f}'}<span class='feature-unit'> Hz</span></div></div>",unsafe_allow_html=True)
            st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True)
            j1,j2,j3=st.columns(3)
            vals=[('Jitter proxy',fa['jitter_pct'],'%'),('Shimmer proxy',fa['shimmer_pct'],'%'),('Segment consistency',fa['consistency']*100 if np.isfinite(fa['consistency']) else np.nan,'%')]
            for col,(lab,val,unit) in zip((j1,j2,j3),vals):
                with col:
                    txt='—' if val is None or not np.isfinite(val) else f'{val:.2f}'
                    st.markdown(f"<div class='feature-card' style='text-align:center'><div class='feature-title'>{lab}</div><div class='feature-value'>{txt}<span class='feature-unit'>{unit}</span></div></div>",unsafe_allow_html=True)
            r_html("<div class='explain-grid'><div class='explain-mini'><b>Formants F1/F2/F3</b><span>Approximate vocal-tract resonances that describe speech sound structure.</span></div><div class='explain-mini'><b>Jitter / shimmer</b><span>Cycle-to-cycle timing and amplitude variability; these dashboard values are proxies.</span></div><div class='explain-mini'><b>Segment consistency</b><span>Checks whether acoustic features remain similar across parts of this recording.</span></div><div class='explain-mini'><b>Important</b><span>Segment consistency is within-audio consistency, not speaker verification.</span></div></div>")
            fig,ax=plt.subplots(figsize=(10,2.45)); t=np.arange(len(fa['flux']))*256/fa['sr']; ax.plot(t,fa['flux'],linewidth=1.0); ax.set_title('Spectral flux timeline',fontsize=10,color='#18202f',loc='left'); ax.set_xlabel('Time (s)'); ax.set_ylabel('Flux'); ax.grid(alpha=.15); fig.patch.set_facecolor('white'); ax.set_facecolor('#faf8f5'); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)
            voiced=np.where(fa['f0_voiced'],1.0,0.0); fig,ax=plt.subplots(figsize=(10,1.7)); ax.step(np.arange(len(voiced))*256/fa['sr'],voiced,where='mid',linewidth=1.2); ax.set_yticks([0,1],['Silence','Voiced']); ax.set_title('Voicing / silence structure',fontsize=10,color='#18202f',loc='left'); ax.set_xlabel('Time (s)'); ax.set_ylim(-.15,1.15); fig.patch.set_facecolor('white'); ax.set_facecolor('#faf8f5'); fig.tight_layout(); st.pyplot(fig,use_container_width=True); plt.close(fig)
        else:
            r_html("<div class='visual-card' style='margin-top:12px;color:#8c96a5;font-size:10px'>Analyze audio to populate the forensic signal panel.</div>")

    elif ws_tab == "Features":
        if analysis and "error" not in analysis:
            vec=np.asarray(analysis['features'],dtype=float)
            r_html("<div class='explain-card'><div class='explain-title'>What does the 102-feature vector tell us?</div><div class='explain-copy'>It converts the recording into numerical acoustic measurements that the machine-learning model can compare with patterns learned during training. The table is shown for transparency and technical inspection; users do not need to interpret every number individually.</div><div class='explain-grid'><div class='explain-mini'><b>MFCC / Delta</b><span>Describe speech-spectrum shape and how that shape changes over time.</span></div><div class='explain-mini'><b>Spectral statistics</b><span>Describe energy distribution, bandwidth, rolloff, waveform crossings, and signal strength.</span></div></div></div>")
            groups=feature_groups(vec)
            group_names=['MFCC mean/std','Delta mean/std','Delta² mean/std','Spectral statistics','Contrast statistics']
            group_vals=[groups['MFCC'],groups['Delta'],groups['Delta-delta'],groups['Spectral'],groups['Contrast']]
            cols=st.columns(5)
            for col,name,val in zip(cols,group_names,group_vals):
                with col: st.markdown(f"<div class='feature-card' style='text-align:center'><div class='feature-title'>{name}</div><div class='feature-value'>{val:.3f}</div></div>",unsafe_allow_html=True)
            st.markdown('<div style="height:12px"></div>',unsafe_allow_html=True)
            r_html("<div class='section-title' style='font-size:12px'>102-dimensional acoustic vector</div><div class='section-sub' style='margin-bottom:8px'>Live measurements from the repository feature extractor</div>")
            rows=[]
            for i,v in enumerate(vec[:78]): rows.append({'Index':i+1,'Feature':FEATURE_NAMES[i],'Value':float(v)})
            st.dataframe(pd.DataFrame(rows).style.format({'Value':'{:.6f}'}),use_container_width=True,hide_index=True,height=420)
            r_html("<div style='height:10px'></div><div class='section-title' style='font-size:12px'>Spectral descriptors</div><div class='section-sub' style='margin-bottom:8px'>Centroid, bandwidth, rolloff, ZCR and RMS · mean/std</div><div class='section-hint'><b>In plain English:</b> these describe where sound energy is concentrated, how spread out it is, how bright it is, how often the waveform crosses zero, and how strong the signal is.</div>")
            spectral_rows=[]; labels=['Spectral centroid','Spectral bandwidth','Spectral rolloff','Zero-crossing rate','RMS energy']
            for i,label in enumerate(labels):
                idx=78+i*2; spectral_rows.append({'Feature':label,'Mean':float(vec[idx]),'Std':float(vec[idx+1])})
            st.dataframe(pd.DataFrame(spectral_rows).style.format({'Mean':'{:.6f}','Std':'{:.6f}'}),use_container_width=True,hide_index=True)
            r_html("<div style='height:10px'></div><div class='section-title' style='font-size:12px'>Spectral contrast bands</div><div class='section-sub' style='margin-bottom:8px'>Seven contrast bands × mean/std</div><div class='section-hint'><b>What it tells us:</b> the difference between stronger peaks and weaker valleys across frequency bands, giving another view of spectral texture.</div>")
            contrast_rows=[]
            for i in range(7): contrast_rows.append({'Band':i+1,'Mean':float(vec[88+i]),'Std':float(vec[95+i])})
            st.dataframe(pd.DataFrame(contrast_rows).style.format({'Mean':'{:.6f}','Std':'{:.6f}'}),use_container_width=True,hide_index=True)
            top_idx=np.argsort(np.abs(vec))[-10:][::-1]
            r_html("<div style='height:10px'></div><div class='section-title' style='font-size:12px'>Largest observed feature magnitudes</div><div class='section-sub' style='margin-bottom:8px'>Measurements only — not model attribution</div><div class='section-hint'>These are the largest absolute measurements in this recording. They <b>do not</b> tell us which features the Random Forest used most strongly.</div>")
            st.dataframe(pd.DataFrame([{'Feature':FEATURE_NAMES[i],'Value':float(vec[i]),'Abs. magnitude':abs(float(vec[i]))} for i in top_idx]).style.format({'Value':'{:.6f}','Abs. magnitude':'{:.6f}'}),use_container_width=True,hide_index=True)
        else:
            r_html("<div class='visual-card' style='margin-top:12px;color:#8c96a5;font-size:10px'>Analyze an audio sample to populate the 102-feature acoustic matrix.</div>")

with right_col:
    r_html(f"""<div class='quick-card'><div class='section-title'>Analysis Workspace</div><div class='section-sub'>Upload or live record</div><div class='quick-item'><div class='qi-left'><div class='qi-icon'>⌁</div><div><div class='qi-name'>Signal monitor</div><div class='qi-note'>Waveform reference · results</div></div></div><div class='arrow'>›</div></div><div class='quick-item'><div class='qi-left'><div class='qi-icon' style='background:#f2ecff;color:#8b5cf6'>↥</div><div><div class='qi-name'>Upload audio</div><div class='qi-note'>Choose a file or record</div></div></div><div class='arrow'>›</div></div><div class='quick-item'><div class='qi-left'><div class='qi-icon' style='background:#fff0f2;color:#e11d48'>◉</div><div><div class='qi-name'>Live record</div><div class='qi-note'>Use your microphone</div></div></div><div class='arrow'>›</div></div></div><div class='snapshot' style='margin-top:16px'><div class='snapshot-head'><div style='font-size:13px;font-weight:800'>Model Snapshot</div><span class='chip' style='background:#effcf6;color:#059669;border:1px solid #b7efd5'>Prototype validation</span></div><div class='snapshot-grid'><div><div class='snapshot-big'>91.37%</div><div class='snapshot-label'>Test Accuracy</div></div><div style='text-align:right'><div class='snapshot-big'>97.84%</div><div class='snapshot-label'>ROC-AUC</div></div></div><div style='display:flex;gap:7px;margin-top:12px;flex-wrap:wrap'><span class='chip' style='background:#eff4ff;color:#4f75e2'>15,290 MLAAD samples</span><span class='chip' style='background:#f7f5f2;color:#64748b'>102 features</span></div><div class='snapshot-wave'></div></div>""")

# Actual input controls, with stable visibility
r_html("<div style='height:16px'></div><div class='card'><div class='section-title'>Upload or Stream Audio for Deep Inspection</div><div class='section-sub'>Supports WAV, FLAC, MP3, OGG, M4A, AAC, MPG</div>")
st.session_state.setdefault("input_panel", "Upload Audio File")
in_names=["Upload Audio File","Live Voice Record"]
in_cols=st.columns(2, gap="small")
for idx, (col, name) in enumerate(zip(in_cols, in_names)):
    with col:
        label=("📁  " if name=="Upload Audio File" else "🎙️  ")+name
        if st.button(label, key=f"input_{idx}", use_container_width=True, type="primary" if st.session_state.input_panel==name else "secondary"):
            st.session_state.input_panel=name
            st.rerun()
st.markdown("<div class='control-divider'></div>", unsafe_allow_html=True)
if st.session_state.input_panel == "Upload Audio File":
    uploaded_file=st.file_uploader("Drag & drop your audio file here",type=["wav","flac","mp3","ogg","m4a","aac","mpeg","mpg"],label_visibility="collapsed",key="main_upload")
    if uploaded_file:
        data=uploaded_file.getvalue();
        if st.session_state.get('current_audio_hash')!=audio_signature(data): set_current_audio(data,uploaded_file.name)
        r_html(f"<div style='font-size:10px;color:#64748b;margin:5px 0 8px'>Ready: <b>{escape(uploaded_file.name)}</b> · {uploaded_file.size/1024:.1f} KB</div>")
        if st.button("Analyze Audio File →",key="analyze_upload",use_container_width=True):
            with st.spinner("Processing audio through the feature extraction and risk engine…"):
                try:
                    res=analyze_file(uploaded_file.name,data,uploaded_file.type);st.session_state.last_result=res;st.session_state.last_mode='upload';st.session_state.last_time=datetime.now().strftime('%d %b %Y · %I:%M %p');st.session_state.current_audio_duration=float(res.get('duration_seconds',0) or st.session_state.current_audio_duration or 0);fin=res.get('final',{});st.session_state.history.insert(0,{"name":uploaded_file.name,"type":uploaded_file.name.split('.')[-1].upper(),"result":str(fin.get('action','verify')).upper(),"confidence":pct(fin.get('confidence')),"date":st.session_state.last_time});st.rerun()
                except requests.HTTPError as e:
                    try: detail=e.response.json().get('detail','The API rejected this audio.')
                    except Exception: detail='The API rejected this audio.'
                    st.error(str(detail))
                except requests.RequestException: st.error('The analysis API could not be reached.')
                except Exception as e: st.error(f'Analysis failed: {e}')
else:
    r_html("<div style='font-size:11px;font-weight:700;color:#18202f'>Record live voice via microphone</div><div style='font-size:9.5px;color:#8c96a5;margin:3px 0 8px'>Speak clearly for at least 4 seconds for the sliding-window detector.</div>")
    mic_audio=st.audio_input("Record Speech",key=f"mic_input_{st.session_state.live_rec_key}")
    if mic_audio:
        rec_bytes=mic_audio.getvalue();rec_name=f"mic_capture_{datetime.now().strftime('%H%M%S')}.wav"
        if st.session_state.get('current_audio_hash')!=audio_signature(rec_bytes): set_current_audio(rec_bytes,rec_name)
        if st.button("Analyze Recording →",key="analyze_recording",use_container_width=True):
            with st.spinner("Analyzing live microphone audio through the same backend engine…"):
                try:
                    res=analyze_file(rec_name,rec_bytes,'audio/wav');st.session_state.last_result=res;st.session_state.last_mode='live';st.session_state.last_time=datetime.now().strftime('%d %b %Y · %I:%M %p');st.session_state.current_audio_duration=float(res.get('duration_seconds',0) or st.session_state.current_audio_duration or 0);fin=res.get('final',{});st.session_state.history.insert(0,{"name":rec_name,"type":"WAV","result":str(fin.get('action','verify')).upper(),"confidence":pct(fin.get('confidence')),"date":st.session_state.last_time});st.rerun()
                except Exception as e: st.error(f'Live analysis failed: {e}')
r_html('</div>')

# security result
if last:
    final=last.get('final',{});dc,dl,dd=decision(final.get('action'));risk=float(final.get('risk_score',0) or 0);spoof=float(final.get('spoof_probability',0) or 0);confidence=float(final.get('confidence',0) or 0);windows=last.get('windows',[]) or []
    st.markdown('<div class="card" style="margin-top:16px">',unsafe_allow_html=True);r_html(f"<div style='display:flex;justify-content:space-between;align-items:center'><div><div class='section-title'>Latest Inspection Breakdown</div><div class='section-sub'>{escape(last.get('filename') or current_name)}</div></div><div class='result-pill'><span class='result-dot'></span>{escape(dl)}</div></div><div style='height:11px'></div>")
    a,b,c,d=st.columns(4)
    for col,label,val in [(a,'Real Voice',(1-spoof)*100),(b,'AI Likelihood',spoof*100),(c,'Risk Score',risk*100),(d,'Confidence',confidence*100)]:
        with col: st.markdown(f"<div class='feature-card' style='text-align:center'><div class='feature-title'>{label}</div><div class='feature-value'>{val:.1f}%</div></div>",unsafe_allow_html=True)
    if windows:
        st.markdown('<div style="height:10px"></div>',unsafe_allow_html=True);r_html('<div class="section-title" style="font-size:12px">Evidence over time</div>');st.line_chart(pd.DataFrame({'AI likelihood':[float(w.get('spoof_probability',0)) for w in windows],'Risk':[float(w.get('risk_score',0)) for w in windows]}),height=210)
    if st.session_state.get('last_mode')=='live':
        if st.button('Record another',key='record_another',use_container_width=True): reset_recording()
    with st.expander('Open window-level evidence'):
        if windows:
            t=pd.DataFrame(windows);keep=[x for x in ['start_seconds','end_seconds','spoof_probability','risk_score','confidence','action'] if x in t.columns];t=t[keep].copy()
            for x in ['spoof_probability','risk_score','confidence']:
                if x in t.columns:t[x]=(t[x].astype(float)*100).round(1).astype(str)+'%'
            t.columns=[x.replace('_',' ').title() for x in t.columns];st.dataframe(t,use_container_width=True,hide_index=True)
    guidance='Current evidence is below the verification threshold; normal controls still apply.' if dc=='allow' else 'The synthetic-voice signal is elevated. Independently confirm the caller before a sensitive action.' if dc=='verify' else 'The combined signal is high. Follow established review procedures.'
    r_html(f"<div style='margin-top:10px;padding:10px 12px;background:#faf8f5;border:1px solid #ece6de;border-radius:10px;font-size:10px;color:#475569'><b>Operator guidance:</b> {guidance}<br><br><span style='color:#8c96a5'>A model score is evidence, not proof of identity.</span></div></div>")

# utility pages
if st.session_state.nav_page=="History":
    st.markdown('<div class="card" style="margin-top:16px">',unsafe_allow_html=True);r_html('<div class="section-title">Analysis History</div>');st.dataframe(pd.DataFrame(st.session_state.history),use_container_width=True,hide_index=True);r_html('</div>')
elif st.session_state.nav_page=="Model":
    st.markdown('<div class="card" style="margin-top:16px">',unsafe_allow_html=True);r_html(f'<div class="section-title">Model & Pipeline</div><div class="section-sub">{escape(dyn_model_name)} · {dyn_features} acoustic descriptors · {dyn_window:.0f}s/{dyn_hop:.0f}s rolling windows</div>');
    if analysis and 'error' not in analysis: st.dataframe(pd.DataFrame({'Feature':FEATURE_NAMES,'Value':analysis['features']}),use_container_width=True,hide_index=True)
    r_html('</div>')
elif st.session_state.nav_page=="Settings":
    st.markdown('<div class="card" style="margin-top:16px">',unsafe_allow_html=True);r_html(f'<div class="section-title">Settings</div><div class="section-sub">API: {escape(API_URL)}</div><div style="margin-top:10px;font-size:10px;color:#8c96a5">Dedicated OOD detection and speaker-verification fusion remain future backend components.</div>');r_html('</div>')

r_html("<div class='vcg-footer'>VoiceCloneGuard is a Smart India Hackathon prototype. It provides acoustic evidence and a risk-oriented response; it does not prove speaker identity. Model results shown in the dashboard come from the MLAAD evaluation pipeline and should be interpreted as benchmark results, not proof of real-world performance across every recording condition.</div>")
