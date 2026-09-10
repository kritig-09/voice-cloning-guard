import io
import os
from datetime import datetime

import librosa
import librosa.display
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("VCG_API_URL", "http://127.0.0.1:8000").rstrip("/")

st.set_page_config(page_title="VoiceCloneGuard", page_icon="◈", layout="wide")

if "live_rec_key" not in st.session_state:
    st.session_state.live_rec_key = 0

st.markdown(r"""
<style>
.stApp{background:#071018;color:#dce6ed;font-family:Inter,system-ui,sans-serif}
.block-container{max-width:1280px;padding:1.1rem 2rem 3rem}
header,footer{visibility:hidden}
.topbar{border:1px solid #20313e;background:#0a141d;padding:12px 15px;display:flex;justify-content:space-between;align-items:center}
.brand{display:flex;align-items:center;gap:10px}.mark{width:34px;height:34px;border:1px solid #3b6d8b;background:#0d1b25;color:#76c9f2;display:flex;align-items:center;justify-content:center;border-radius:4px;font-weight:900}.name{font-size:1.08rem;font-weight:800;color:#f1f5f7}.sub{font-size:.66rem;color:#687a89;margin-top:2px}.meta{display:flex;gap:16px;align-items:center;color:#687a89;font-size:.62rem;letter-spacing:.08em}.live{color:#76d9a3}.warn{color:#dfbd70}.dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:#667888;margin-right:5px}.live .dot{background:#61d79a}.warn .dot{background:#d9aa4b}
.hero{margin-top:18px;border:1px solid #20313e;background:#0a141d;padding:28px 29px;display:grid;grid-template-columns:1.45fr .8fr;gap:30px}.eyebrow{color:#70b9e6;font-size:.62rem;letter-spacing:.18em;font-weight:800;text-transform:uppercase}.hero h1{font-size:3.1rem;line-height:.98;margin:7px 0 0;color:#f4f7f9;letter-spacing:-.055em}.copy{color:#8293a2;max-width:760px;line-height:1.62;font-size:.9rem;margin-top:12px}.hero-side{border-left:1px solid #20303a;padding-left:20px;display:flex;justify-content:space-between;flex-direction:column}.sl{font-size:.61rem;letter-spacing:.12em;text-transform:uppercase;color:#617483;font-weight:800}.sv{font-size:1.8rem;color:#eef4f7;font-weight:820;letter-spacing:-.035em;margin-top:4px}.sn{font-size:.64rem;color:#627585;line-height:1.45;margin-top:2px}
.section{margin-top:20px}.head{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid #1b2934;padding-bottom:7px;margin-bottom:9px}.title{font-size:.88rem;font-weight:780;color:#eaf1f5}.note{font-size:.62rem;color:#5d7080;text-transform:uppercase;letter-spacing:.08em}.pipeline{border:1px solid #20303e;background:#0a141d}.pgrid{display:grid;grid-template-columns:repeat(5,1fr)}.p{padding:11px 13px;min-height:70px;border-left:1px solid #22323e}.p:first-child{border-left:0}.num{font-size:.58rem;color:#4d87ac;font-weight:800}.pt{font-size:.74rem;color:#dde7ee;font-weight:750;margin-top:7px}.ps{font-size:.61rem;color:#627583;margin-top:3px}
.metrics{display:grid;grid-template-columns:repeat(4,1fr);border:1px solid #20303e;background:#0a141d}.m{padding:13px 15px;border-left:1px solid #20303e}.m:first-child{border-left:0}.ml{font-size:.57rem;letter-spacing:.11em;text-transform:uppercase;color:#607383;font-weight:800}.mv{font-size:1.52rem;color:#eef4f7;font-weight:820;margin-top:7px}.mn{font-size:.61rem;color:#5d7180;margin-top:2px}
.workspace{display:grid;grid-template-columns:1.5fr .82fr;gap:10px}.panel{border:1px solid #20313e;background:#0a141d;padding:15px}.ptitle{font-size:.8rem;font-weight:780;color:#e4edf2}.psub2{font-size:.63rem;color:#657887;margin-top:3px;margin-bottom:10px}.signal{height:250px;border:1px solid #182833;background:#071018;display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden}.signal:before,.signal:after{content:"";position:absolute;left:0;right:0;height:1px;background:#13232d}.signal:before{top:36%}.signal:after{top:64%}.bars{height:135px;display:flex;align-items:center;gap:4px}.bars span{width:2px;background:#337796;display:block}
div[data-testid="stFileUploader"]{background:#071018;border:1px dashed #355265;border-radius:4px}.stButton>button{background:#66b9e4;color:#061018;border:1px solid #66b9e4;border-radius:4px;font-weight:850}.stButton>button:hover{background:#8bd0ee;border-color:#8bd0ee;color:#061018}.stTabs [data-baseweb="tab-list"]{gap:2px;border-bottom:1px solid #20303e}.stTabs [data-baseweb="tab"]{font-size:.68rem;font-weight:800;color:#718391}
.result{border:1px solid #273740;background:#0b151d;padding:15px;border-left:3px solid #788894}.result.allow{border-left-color:#59be8d}.result.verify{border-left-color:#d4ad50}.result.escalate{border-left-color:#d15a68}.rl{font-size:.59rem;letter-spacing:.12em;text-transform:uppercase;color:#627686;font-weight:800}.rv{font-size:1.72rem;font-weight:830;color:#f0f5f7;margin-top:4px}.rc{font-size:.68rem;color:#8998a5;margin-top:3px}.twocol{display:grid;grid-template-columns:1.15fr .85fr;gap:10px}.row{padding:8px 0;border-bottom:1px solid #17242d;color:#acbac5;font-size:.68rem;line-height:1.45}.row:last-child{border-bottom:0}.interpret{border-left:2px solid #315a72;background:#0c171f;padding:10px 12px;color:#9aabb9;font-size:.69rem;line-height:1.55}.footer{border-top:1px solid #1b2832;padding-top:12px;margin-top:24px;color:#526675;font-size:.60rem;line-height:1.55}
@media(max-width:900px){.hero,.workspace,.twocol{grid-template-columns:1fr}.pgrid,.metrics{grid-template-columns:1fr}.p,.m{border-left:0;border-top:1px solid #22323e}.p:first-child,.m:first-child{border-top:0}}
</style>
""", unsafe_allow_html=True)

def pct(v):
    return "—" if v is None else f"{float(v)*100:.1f}%"

def decision(action):
    action = str(action or "verify").lower()
    if action == "allow":
        return "allow", "ALLOW", "Current evidence is below the verification threshold."
    if action == "escalate":
        return "escalate", "ESCALATE", "Treat as high risk and follow established review procedures."
    return "verify", "VERIFY IDENTITY", "Confirm independently before a sensitive action."

def analyze_file(name, data, mime):
    r = requests.post(f"{API_URL}/analyze", files={"file": (name, data, mime or "application/octet-stream")}, timeout=180)
    r.raise_for_status()
    return r.json()

health = {}
online = False
try:
    r = requests.get(f"{API_URL}/health", timeout=4)
    r.raise_for_status()
    health = r.json()
    online = bool(health.get("model_connected"))
except Exception:
    pass

status_cls = "live" if online else "warn"
status = "ENGINE ONLINE" if online else "API OFFLINE"

st.markdown(f"""
<div class="topbar">
<div class="brand"><div class="mark">◈</div><div><div class="name">VoiceCloneGuard</div><div class="sub">Voice authenticity & impersonation risk console</div></div></div>
<div class="meta"><div class="{status_cls}"><span class="dot"></span>{status}</div><div>SIH 26104</div><div>BUILD 0.3</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
<div><div class="eyebrow">AI voice security · prototype</div><h1>VoiceCloneGuard</h1><div class="copy">A practical voice-authenticity check for impersonation-risk scenarios. The system combines acoustic evidence, rolling analysis and risk policy to support safer decisions.</div></div>
<div class="hero-side"><div><div class="sl">Model</div><div class="sv">Rich-feature RF</div><div class="sn">MFCC, delta and spectral statistics</div></div><div><div class="sl">Security response</div><div class="sv">3 actions</div><div class="sn">Allow · Verify · Escalate</div></div></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section"><div class="head"><div class="title">Detection path</div><div class="note">signal → evidence → action</div></div><div class="pipeline"><div class="pgrid">', unsafe_allow_html=True)
for n,t,s in [("01","AUDIO INPUT","upload or record"),("02","NORMALIZE","16 kHz · mono"),("03","ACOUSTIC ANALYSIS","MFCC + spectral"),("04","ROLLING EVIDENCE","4 s window · 1 s hop"),("05","SECURITY RESPONSE","allow · verify · escalate")]:
    st.markdown(f'<div class="p"><div class="num">{n}</div><div class="pt">{t}</div><div class="ps">{s}</div></div>', unsafe_allow_html=True)
st.markdown('</div></div></div>', unsafe_allow_html=True)

st.markdown('<div class="section"><div class="head"><div class="title">Model snapshot</div><div class="note">live from /health</div></div><div class="metrics">', unsafe_allow_html=True)
_feat_count = health.get("feature_count")
_feat_version = health.get("feature_version") or "—"
_train_n = health.get("training_sample_count")
_window_s = health.get("window_seconds", 4)
_hop_s = health.get("hop_seconds", 1)
_n_formats = len(health.get("supported_formats") or []) or 8
_train_value = f"{_train_n} clips" if _train_n else "not reported"
_train_note = "prototype-scale — not a production benchmark" if _train_n and _train_n < 500 else "labeled training set"
for a, b, c in [
    ("FEATURES", str(_feat_count if _feat_count is not None else "—"), _feat_version),
    ("TRAINING DATA", _train_value, _train_note),
    ("WINDOW", f"{_window_s:g}s", f"{_hop_s:g}s hop"),
    ("INPUTS", str(_n_formats), "audio formats"),
]:
    st.markdown(f'<div class="m"><div class="ml">{a}</div><div class="mv">{b}</div><div class="mn">{c}</div></div>', unsafe_allow_html=True)
st.markdown('</div><div style="font-size:.62rem;color:#647687;margin-top:5px">These figures are read live from the running model, not hardcoded — no accuracy number is shown here because it has not been measured on a documented, independent evaluation set yet. Run evaluate_model.py for a real metric.</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section"><div class="head"><div class="title">Analysis workspace</div><div class="note">upload or live record</div></div><div class="workspace">', unsafe_allow_html=True)


def render_signal_panel():
    audio_bytes = st.session_state.get("last_audio_bytes")
    if not audio_bytes:
        st.markdown(
            '<div class="panel"><div class="ptitle">Signal monitor</div>'
            '<div class="psub2">The waveform of the analyzed audio appears here after you run an analysis</div>'
            '<div class="signal" style="display:flex;align-items:center;justify-content:center;color:#4d5f6c;font-size:.68rem">No audio analyzed yet</div></div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown('<div class="panel"><div class="ptitle">Signal monitor</div><div class="psub2">Waveform of the analyzed audio</div>', unsafe_allow_html=True)
    try:
        waveform, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)
        fig, ax = plt.subplots(figsize=(9, 2.3))
        fig.patch.set_alpha(0)
        ax.set_facecolor("#071018")
        librosa.display.waveshow(waveform, sr=sr, ax=ax, color="#66b9e4")
        ax.set_xlabel("Time (s)", color="#8998a5", fontsize=8)
        ax.set_ylabel("")
        ax.tick_params(colors="#647687", labelsize=7)
        for spine in ax.spines.values():
            spine.set_color("#20313e")
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    except Exception as exc:
        st.markdown(f'<div style="color:#647687;font-size:.68rem">Waveform unavailable for this file ({exc}).</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


render_signal_panel()
st.markdown('<div class="panel"><div class="ptitle">Input</div><div class="psub2">Choose a saved sample or use the microphone</div>', unsafe_allow_html=True)
t1,t2=st.tabs(["UPLOAD","LIVE RECORD"])
with t1:
    up=st.file_uploader("Audio",type=["wav","flac","mp3","ogg","m4a","aac","mpeg","mpg"],label_visibility="collapsed")
    go=st.button("Analyze uploaded audio",disabled=up is None,use_container_width=True)
    if go and up:
        with st.spinner("Analyzing audio…"):
            try:
                st.session_state.last_result=analyze_file(up.name,up.getvalue(),up.type)
                st.session_state.last_audio_bytes=up.getvalue()
                st.session_state.last_mode="upload"
                st.session_state.last_time=datetime.now().strftime("%d %b %Y, %H:%M:%S")
                st.rerun()
            except requests.HTTPError as e:
                try: detail=e.response.json().get("detail","The API rejected this audio.")
                except Exception: detail="The API rejected this audio."
                st.error(str(detail))
            except requests.RequestException: st.error("The analysis API could not be reached.")
            except Exception as e: st.error(f"Analysis failed: {e}")
with t2:
    rec=st.audio_input("Record voice", key=f"live_record_{st.session_state.live_rec_key}")
    st.markdown('<div style="font-size:.61rem;color:#627583;margin:6px 0 10px">Record a short speech sample. It uses the same analysis API as file uploads.</div>',unsafe_allow_html=True)
    go2=st.button("Analyze recording",disabled=rec is None,use_container_width=True)
    if go2 and rec:
        with st.spinner("Analyzing recording…"):
            try:
                st.session_state.last_result=analyze_file("live_recording.wav",rec.getvalue(),"audio/wav")
                st.session_state.last_audio_bytes=rec.getvalue()
                st.session_state.last_mode="live"
                st.session_state.last_time=datetime.now().strftime("%d %b %Y, %H:%M:%S")
                st.rerun()
            except requests.HTTPError as e:
                try: detail=e.response.json().get("detail","The API rejected this recording.")
                except Exception: detail="The API rejected this recording."
                st.error(str(detail))
            except requests.RequestException: st.error("The analysis API could not be reached.")
            except Exception as e: st.error(f"Recording analysis failed: {e}")
st.markdown('</div></div></div>',unsafe_allow_html=True)

last=st.session_state.get("last_result")
if last:
    final=last.get("final",{})
    dc,dl,dd=decision(final.get("action"))
    st.markdown('<div class="section"><div class="head"><div class="title">Security assessment</div><div class="note">latest result</div></div>',unsafe_allow_html=True)
    if st.session_state.get("last_mode") == "live":
        c1,c2=st.columns([1,1])
        with c1:
            st.markdown(f'<div class="result {dc}"><div class="rl">Recommended action</div><div class="rv">{dl}</div><div class="rc">{dd}</div></div>',unsafe_allow_html=True)
        with c2:
            st.markdown('<div style="height:100%">', unsafe_allow_html=True)
            if st.button("Record another", use_container_width=True):
                for k in ("last_result","last_mode","last_time","last_audio_bytes"):
                    st.session_state.pop(k, None)
                st.session_state.live_rec_key += 1
                st.rerun()
            st.markdown('<div style="font-size:.61rem;color:#627583;margin-top:6px">Start a fresh microphone capture without refreshing the page.</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="result {dc}"><div class="rl">Recommended action</div><div class="rv">{dl}</div><div class="rc">{dd}</div></div>',unsafe_allow_html=True)
    windows=last.get("windows",[])
    st.markdown('<div class="twocol">',unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="panel" style="margin-top:10px"><div class="ptitle">Evidence over time</div><div class="psub2">One point per analysis window</div>',unsafe_allow_html=True)
        if windows:
            df=pd.DataFrame({"AI likelihood":[float(w.get("spoof_probability",0)) for w in windows],"Risk":[float(w.get("risk_score",0)) for w in windows]})
            st.line_chart(df,height=250)
        st.markdown('</div>',unsafe_allow_html=True)
    st.markdown(f'<div class="panel" style="margin-top:10px"><div class="ptitle">Signal summary</div><div class="row"><b>AI likelihood</b><br>{pct(final.get("spoof_probability"))}</div><div class="row"><b>Risk score</b><br>{pct(final.get("risk_score"))}</div><div class="row"><b>Confidence</b><br>{pct(final.get("confidence"))}</div><div class="row"><b>Windows</b><br>{last.get("windows_analyzed","—")}</div><div class="row"><b>Input</b><br>{last.get("filename","—")}</div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown('<div class="twocol">',unsafe_allow_html=True)
    st.markdown('<div class="panel" style="margin-top:10px"><div class="ptitle">Evidence</div>',unsafe_allow_html=True)
    for x in final.get("reasons") or final.get("explanation") or ["No additional evidence returned."]:
        st.markdown(f'<div class="row">{x}</div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    guidance=("Current evidence is below the verification threshold; normal controls still apply." if dc=="allow" else "The synthetic-voice signal is elevated. Independently confirm the caller before a sensitive action." if dc=="verify" else "The combined signal is high. Follow established review procedures.")
    st.markdown(f'<div class="panel" style="margin-top:10px"><div class="ptitle">Operator guidance</div><div class="interpret">{guidance}<br><br><span style="color:#617482">A model score is evidence, not proof of identity.</span></div></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    with st.expander("Open window-level evidence"):
        if windows:
            t=pd.DataFrame(windows)
            keep=[x for x in ["start_seconds","end_seconds","spoof_probability","risk_score","confidence","action"] if x in t.columns]
            t=t[keep].copy()
            csv_bytes = t.to_csv(index=False).encode("utf-8")
            for x in ["spoof_probability","risk_score","confidence"]:
                if x in t.columns: t[x]=(t[x]*100).round(1).astype(str)+"%"
            t.columns=[x.replace("_"," ").title() for x in t.columns]
            st.dataframe(t,use_container_width=True,hide_index=True)
            st.download_button(
                "Download evidence as CSV",
                data=csv_bytes,
                file_name=f"voicecloneguard_evidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
    st.caption(f"Analyzed {st.session_state.get('last_time','—')} · mode: {st.session_state.get('last_mode','—')}")
    st.markdown('</div>',unsafe_allow_html=True)

st.markdown(
    '<div class="footer">VoiceCloneGuard is a Smart India Hackathon prototype. It provides acoustic evidence and a risk-oriented response; it does not prove speaker identity. '
    'Metrics on this page are read live from the running model\'s metadata; run evaluate_model.py against a documented dataset for an accuracy/EER figure before quoting one.</div>',
    unsafe_allow_html=True,
)
