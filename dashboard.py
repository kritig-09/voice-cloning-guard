import os
import requests
import streamlit as st


API_URL = os.getenv("VCG_API_URL", "http://127.0.0.1:8000").rstrip("/")


st.set_page_config(
    page_title="VoiceCloneGuard",
    page_icon="🎙️",
    layout="wide",
)


# ============================================================
# THEME
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background: #0d0f13;
        color: #e5e7eb;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .hero-title {
        font-size: 2.7rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 0.25rem;
        letter-spacing: -0.03em;
    }

    .hero-subtitle {
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .card {
        background: #12151b;
        border: 1px solid #282d37;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .label {
        color: #8992a1;
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 700;
    }

    .big-value {
        color: #f8fafc;
        font-size: 2.35rem;
        font-weight: 700;
        margin-top: 4px;
    }

    .decision-low {
        color: #86efac;
        font-size: 2rem;
        font-weight: 700;
    }

    .decision-medium {
        color: #fbbf24;
        font-size: 2rem;
        font-weight: 700;
    }

    .decision-high {
        color: #fca5a5;
        font-size: 2rem;
        font-weight: 700;
    }

    .evidence {
        background: #171a21;
        border: 1px solid #282d37;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 7px 0;
        color: #d6dbe3;
    }

    .helper {
        color: #8992a1;
        font-size: 0.86rem;
        line-height: 1.55;
    }

    .verification {
        background: #191614;
        border: 1px solid #5d4a1d;
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 10px;
    }

    .verification-title {
        color: #fbbf24;
        font-weight: 700;
        margin-bottom: 6px;
    }

    .section-title {
        font-size: 1.35rem;
        font-weight: 650;
        color: #f1f5f9;
        margin-top: 1.3rem;
        margin-bottom: 0.6rem;
    }

    .stButton > button {
        border-radius: 9px;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPERS
# ============================================================

def decision_class(action: str) -> str:
    action = action.lower()

    if action == "allow":
        return "decision-low"

    if action == "verify":
        return "decision-medium"

    return "decision-high"


def decision_label(action: str) -> str:
    return {
        "allow": "ALLOW",
        "verify": "VERIFY IDENTITY",
        "escalate": "ESCALATE",
    }.get(action.lower(), action.upper())


def window_time_label(window: dict) -> str:
    return (
        f'{window["start_seconds"]:.1f}'
        f'–'
        f'{window["end_seconds"]:.1f}s'
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="hero-title">VoiceCloneGuard</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero-subtitle">'
    'Privacy-first voice authenticity screening with rolling risk analysis.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# ENGINE STATUS
# ============================================================

health_col, info_col = st.columns([1, 3])

with health_col:
    try:
        health_response = requests.get(
            f"{API_URL}/health",
            timeout=5,
        )
        health_response.raise_for_status()
        health = health_response.json()

        if health.get("model_connected"):
            st.success("Detection engine online")
        else:
            st.error("Model not connected")

    except requests.RequestException:
        st.error("API offline")


with info_col:
    st.markdown(
        '<div class="helper">'
        'Audio upload → acoustic analysis → rolling evidence → '
        'security decision'
        '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# FILE INPUT
# ============================================================

uploaded = st.file_uploader(
    "Upload audio",
    type=[
        "wav",
        "flac",
        "mp3",
        "ogg",
        "m4a",
        "aac",
        "mpeg",
        "mpg",
    ],
)


# ============================================================
# ANALYSIS
# ============================================================

if uploaded is not None:

    if st.button(
        "Analyze Audio",
        type="primary",
        use_container_width=True,
    ):

        try:
            with st.spinner("Analyzing audio..."):

                response = requests.post(
                    f"{API_URL}/analyze",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            uploaded.type or "audio/wav",
                        )
                    },
                    timeout=120,
                )

            if response.status_code != 200:
                st.error(
                    f"Analysis failed ({response.status_code})"
                )
                st.code(response.text)
                st.stop()

            data = response.json()
            final = data["final"]

            spoof = float(final["spoof_probability"])
            risk_score = float(final["risk_score"])
            confidence = float(final["confidence"])
            action = str(final["action"]).lower()

            windows = data.get("windows", [])

            # =================================================
            # TOP METRICS
            # =================================================

            st.markdown("---")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(
                    '<div class="card">'
                    '<div class="label">AI likelihood</div>'
                    f'<div class="big-value">{spoof * 100:.1f}%</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown(
                    '<div class="card">'
                    '<div class="label">Risk score</div>'
                    f'<div class="big-value">{risk_score * 100:.1f}%</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with col3:
                st.markdown(
                    '<div class="card">'
                    '<div class="label">Model confidence</div>'
                    f'<div class="big-value">{confidence * 100:.1f}%</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            with col4:
                st.markdown(
                    '<div class="card">'
                    '<div class="label">Windows analyzed</div>'
                    f'<div class="big-value">{len(windows)}</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # =================================================
            # SECURITY DECISION
            # =================================================

            st.markdown(
                '<div class="section-title">Security decision</div>',
                unsafe_allow_html=True,
            )

            css_class = decision_class(action)
            label = decision_label(action)

            st.markdown(
                f'<div class="card">'
                f'<div class="{css_class}">{label}</div>'
                f'<div class="helper">'
                f'Policy action based on the current rolling-risk result.'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # =================================================
            # VERIFICATION WORKFLOW
            # =================================================

            if action == "verify":

                st.markdown(
                    '<div class="verification">'
                    '<div class="verification-title">'
                    'Verification required'
                    '</div>'
                    '<div class="helper">'
                    'Do not rely on the voice channel alone. '
                    'Confirm the request through an independent channel '
                    'before taking a sensitive action.'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            elif action == "escalate":

                st.markdown(
                    '<div class="verification">'
                    '<div class="verification-title">'
                    'Security escalation'
                    '</div>'
                    '<div class="helper">'
                    'The current risk state requires manual review '
                    'or an independent identity check.'
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # =================================================
            # AUDIO
            # =================================================

            st.markdown(
                '<div class="section-title">Analyzed audio</div>',
                unsafe_allow_html=True,
            )

            st.audio(uploaded.getvalue())

            audio_col1, audio_col2, audio_col3 = st.columns(3)

            with audio_col1:
                st.metric(
                    "Duration",
                    f'{data["duration_seconds"]:.2f} s',
                )

            with audio_col2:
                st.metric(
                    "Sample rate",
                    f'{int(data["sample_rate"]) / 1000:.0f} kHz',
                )

            with audio_col3:
                st.metric(
                    "Windows",
                    len(windows),
                )

            # =================================================
            # EVIDENCE
            # =================================================

            st.markdown(
                '<div class="section-title">Evidence</div>',
                unsafe_allow_html=True,
            )

            reasons = final.get("reasons", [])
            explanations = final.get("explanation", [])

            if reasons:
                for reason in reasons:
                    st.markdown(
                        f'<div class="evidence">{reason}</div>',
                        unsafe_allow_html=True,
                    )

            for explanation in explanations:
                st.markdown(
                    f'<div class="evidence">{explanation}</div>',
                    unsafe_allow_html=True,
                )

            if not reasons and not explanations:
                st.markdown(
                    '<div class="evidence">'
                    'No additional evidence was returned.'
                    '</div>',
                    unsafe_allow_html=True,
                )

            # =================================================
            # ROLLING-WINDOW TIMELINE
            # =================================================

            st.markdown(
                '<div class="section-title">Risk timeline</div>',
                unsafe_allow_html=True,
            )

            if windows:

                timeline_rows = []

                for index, window in enumerate(
                    windows,
                    start=1,
                ):
                    timeline_rows.append(
                        {
                            "Window": index,
                            "Time": window_time_label(window),
                            "AI likelihood (%)": round(
                                float(
                                    window["spoof_probability"]
                                ) * 100,
                                1,
                            ),
                            "Risk (%)": round(
                                float(window["risk_score"]) * 100,
                                1,
                            ),
                            "Action": str(
                                window["action"]
                            ).upper(),
                        }
                    )

                # Show compact visual trend.
                try:
                    chart_data = []

                    for row in timeline_rows:
                        chart_data.append(
                            {
                                "Window": row["Window"],
                                "AI likelihood": row[
                                    "AI likelihood (%)"
                                ],
                                "Risk": row["Risk (%)"],
                            }
                        )

                    st.line_chart(
                        chart_data,
                        x="Window",
                        y=["AI likelihood", "Risk"],
                    )

                except Exception:
                    pass

                st.dataframe(
                    timeline_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                # Highlight the strongest suspicious window.
                peak_window = max(
                    windows,
                    key=lambda item: float(
                        item["spoof_probability"]
                    ),
                )

                peak_spoof = float(
                    peak_window["spoof_probability"]
                )

                st.markdown(
                    '<div class="evidence">'
                    f'<b>Peak AI likelihood:</b> '
                    f'{peak_spoof * 100:.1f}% '
                    f'between '
                    f'{peak_window["start_seconds"]:.1f}s and '
                    f'{peak_window["end_seconds"]:.1f}s'
                    '</div>',
                    unsafe_allow_html=True,
                )

            else:
                st.info(
                    "No rolling-window data returned."
                )

            # =================================================
            # RAW RESPONSE
            # =================================================

            with st.expander("View technical response"):

                st.json(data)

        except requests.RequestException as exc:

            st.error(
                "Could not reach the VoiceCloneGuard API."
            )

            st.caption(str(exc))
