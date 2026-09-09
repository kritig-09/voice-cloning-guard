# VoiceCloneGuard

**AI voice deepfake detection and risk assessment for voice-based impersonation attacks.**

VoiceCloneGuard is a Smart India Hackathon (SIH) prototype designed to detect potentially AI-generated or cloned speech and translate model evidence into a practical security response. Unlike a simple binary classifier, the system combines acoustic analysis, rolling-window evidence, temporal smoothing, risk scoring, and a conservative decision policy to produce **Allow**, **Verify Identity**, or **Escalate** outcomes.

> **Prototype status:** VoiceCloneGuard is a research/demo system. A model score is evidence, not proof of a person's identity. High-risk results should trigger independent verification rather than automatic accusations or irreversible actions.

---

## 1. Project Information

| Field | Value |
|---|---|
| **Project** | VoiceCloneGuard |
| **SIH Problem ID** | SIH26104 |
| **Problem** | AI-powered real-time detection and prevention of voice-cloning impersonation attacks |
| **Category** | Software |
| **Primary UI** | Streamlit dashboard |
| **Backend API** | FastAPI |
| **Core classifier** | Random Forest |
| **Audio processing** | librosa + FFmpeg |
| **Language** | Python 3.11 |

---

## 2. Problem Statement

Generative AI has made voice cloning and synthetic speech generation increasingly accessible. A short reference recording can be enough to produce speech that sounds convincing to a human listener. In a security context, this creates risks such as:

- family-member impersonation and emergency-payment scams;
- executive or employee impersonation;
- voice-phishing and social engineering;
- fabricated recordings and misinformation;
- attempts to defeat voice-based verification workflows.

A defensive solution must therefore do more than output a single probability. It should normalize inconsistent audio, analyze evidence over time, expose uncertainty, and turn detection evidence into a proportionate security action.

---

## 3. Proposed Solution

VoiceCloneGuard wraps an acoustic voice-spoof detector inside a security-oriented decision pipeline:

```text
Audio Input
    ↓
Decode + Normalize
    ↓
Acoustic Feature Extraction
    ↓
Voice Spoof Probability
    ↓
Rolling 4 s Windows
    ↓
Temporal Risk Fusion
    ↓
Security Policy
    ↓
ALLOW / VERIFY / ESCALATE
```

The prototype supports both the original 13-MFCC detector and a richer-feature Random Forest model. The application prefers `models/improved_voice_model.pkl` when it is available and otherwise falls back to `models/voice_cloning_model.pkl`.

---

# 4. Model Features and Capabilities

## 4.1 Rich acoustic feature analysis

The improved prototype does not rely on a single acoustic measurement. It creates a fixed-length feature vector from multiple complementary views of the waveform.

### MFCC features

The system extracts **13 Mel-Frequency Cepstral Coefficients (MFCCs)**. MFCCs summarize the short-time spectral envelope of speech and are used to represent vocal and phonetic characteristics.

For each MFCC coefficient, the system calculates:

- mean value;
- standard deviation.

This produces **26 MFCC statistics**.

### Delta features

The system calculates the first temporal derivative of the MFCC sequence (**delta coefficients**), which captures how the acoustic representation changes over time.

For the 13 delta coefficients, the system again calculates mean and standard deviation, contributing **26 statistics**.

### Delta-delta features

The second temporal derivative (**delta-delta coefficients**) captures acceleration or curvature in the MFCC trajectory. Mean and standard deviation are retained for all 13 coefficients, contributing **26 statistics**.

### Spectral characteristics

The improved pipeline additionally measures:

| Feature | Purpose |
|---|---|
| **Spectral centroid** | Represents the spectral center of mass / perceived brightness |
| **Spectral bandwidth** | Measures spectral spread around the centroid |
| **Spectral rolloff** | Captures the frequency below which most spectral energy lies |
| **Zero-crossing rate** | Describes rapid waveform sign changes and signal texture |
| **RMS energy** | Represents signal energy / loudness |

For each descriptor, mean and standard deviation are retained, adding **10 statistics**.

### Spectral contrast

Spectral contrast measures differences between prominent spectral peaks and valleys across frequency bands. The current implementation retains the mean and standard deviation of the contrast bands.

### Feature-vector size

With the current implementation and librosa defaults, the improved extractor produces a **102-dimensional acoustic feature vector**:

```text
13 MFCC × 2                  = 26
13 Delta × 2                 = 26
13 Delta-Delta × 2           = 26
5 spectral descriptors × 2   = 10
7 spectral-contrast bands × 2 = 14
----------------------------------
Total                         = 102 features
```

This representation captures both static spectral characteristics and short-term temporal behavior.

---

## 4.2 Improved Random Forest classifier

The extracted acoustic feature vector is passed to a **Random Forest classifier**.

The improved model uses:

```text
Class 0 → Real voice
Class 1 → AI-cloned / spoofed voice
```

The classifier returns class probabilities. The adapter converts the spoof-class probability into a normalized value called `spoof_probability`, which is then consumed by the rolling risk engine.

The original model is retained for compatibility:

```text
Original model:
13 mean MFCC features
Class 0 → AI-cloned
Class 1 → Real
```

The adapter layer handles these different conventions and exposes a consistent downstream detection interface.

---

## 4.3 Rolling-window detection

Instead of relying only on one score for an entire recording, VoiceCloneGuard analyzes the audio in overlapping windows.

Default configuration:

```text
Window length = 4 seconds
Hop length    = 1 second
```

For every window, the system records:

- start and end time;
- spoof probability;
- OOD score field;
- risk score;
- confidence;
- action;
- model explanation;
- policy reasons.

The remaining tail of the recording is also analyzed so the response covers the complete upload.

This creates a temporal evidence trail that the dashboard can visualize.

---

## 4.4 Temporal risk smoothing

The rolling risk engine stores recent spoof probabilities and applies increasing weights to newer observations. Recent evidence therefore influences the security state more strongly than older evidence.

Conceptually:

```text
Older evidence  → lower weight
Recent evidence → higher weight
                 ↓
          Smoothed spoof signal
```

The engine then combines the smoothed signal with optional contextual risk.

---

## 4.5 Context-aware security policy

The model probability is kept separate from contextual security factors.

The API can accept:

- transaction risk;
- verified-contact context;
- an optional speaker-consistency field for future extension;
- an optional OOD score.

Context affects the **response policy**, not the underlying ML probability.

The current policy maps risk into three operational actions:

| Condition | Action |
|---|---|
| Low risk | **ALLOW** |
| Elevated risk or uncertainty | **VERIFY IDENTITY** |
| High risk with sufficient confidence | **ESCALATE** |

The goal is to use detection as a warning and verification trigger, not as proof of identity.

---

## 4.6 Uncertainty-aware confidence

The risk engine treats uncertainty explicitly. When an OOD score indicates that audio may be outside the model's known distribution, confidence is reduced rather than artificially increased.

The repository contains the integration hook for OOD scoring, but a dedicated OOD detector is **not yet trained in the current prototype**. This is documented as future work rather than presented as an implemented production capability.

---

## 4.7 Multi-format audio support

The API accepts:

```text
WAV  FLAC  MP3  OGG  M4A  AAC  MPEG  MPG
```

WAV and FLAC can be analyzed directly. Other formats are converted to 16 kHz mono WAV using **FFmpeg** before feature extraction.

---

## 4.8 Audio validation and normalization

Before inference, the pipeline:

- decodes the audio;
- converts multi-channel input to mono;
- resamples to 16 kHz;
- normalizes waveform amplitude;
- rejects empty input;
- rejects silent input.

These checks reduce avoidable failures and prevent meaningless inputs from being treated as valid detections.

---

## 4.9 Explainability and evidence

VoiceCloneGuard returns structured evidence rather than only a binary label.

For each analyzed window, the API can expose:

```text
Spoof probability
Risk score
Confidence
Action
Reasons
Feature-pipeline information
```

The dashboard presents this through risk cards, a rolling timeline, window-level analysis, peak-risk information, and technical response data.

The improved model also stores the feature-pipeline version and number of features used by the saved model bundle.

---

## 4.10 Privacy-first processing

The application follows a temporary-processing pattern:

1. receive uploaded audio;
2. write it to a temporary server-side file;
3. decode and analyze it;
4. generate metadata/evidence;
5. delete the temporary files.

Raw audio is not intentionally written into the application event record. Deployment operators should still configure logging, storage, backups, and access controls appropriately for production use.

---

## 4.11 FastAPI backend

The backend exposes the detector as an API that can be integrated with other applications.

### Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Service metadata |
| `GET /health` | Health and model-status check |
| `POST /score` | Risk-policy calculation from supplied probabilities |
| `POST /analyze` | Full audio analysis and rolling-window inference |
| `WS /stream` | Streaming inference contract for float32 16 kHz audio |

FastAPI/Swagger documentation is available at `/docs` when the service is running.

---

## 4.12 Streamlit security dashboard

The Streamlit interface is designed for demonstrations and analyst review. It exposes the model results as a security workflow instead of only showing a raw classifier output.

The dashboard includes:

- detection-engine status;
- audio upload;
- AI-cloned likelihood;
- risk score;
- confidence;
- security decision;
- verification/escalation guidance;
- audio playback;
- evidence summary;
- rolling risk timeline;
- window-level analysis;
- peak-risk window;
- technical response information.

---

# 5. End-to-End Technical Workflow

```text
┌───────────────────┐
│   Audio Input     │
│ WAV/FLAC/MP3/...  │
└─────────┬─────────┘
          ↓
┌───────────────────┐
│ Decode + Validate │
│ 16 kHz / Mono     │
└─────────┬─────────┘
          ↓
┌───────────────────────┐
│ Rich Acoustic Features│
│ MFCC + Delta + Spect. │
└─────────┬─────────────┘
          ↓
┌──────────────────────┐
│ Random Forest Model  │
│ Spoof Probability    │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ Rolling Risk Engine  │
│ Temporal Evidence    │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ Security Policy      │
│ Allow / Verify / Esc │
└─────────┬────────────┘
          ↓
┌──────────────────────┐
│ Dashboard / REST API │
│ Evidence + Timeline  │
└──────────────────────┘
```

---

# 6. Technology Stack

- **Python 3.11** — runtime
- **FastAPI** — inference and risk API
- **Streamlit** — interactive dashboard
- **scikit-learn** — Random Forest classifier
- **librosa** — audio loading and acoustic features
- **FFmpeg** — additional audio-format conversion
- **NumPy** — numerical processing
- **pytest** — automated testing
- **Docker** — reproducible backend deployment

---

# 7. Repository Structure

```text
VoiceCloneGuard/
├── README.md
├── LICENSE
├── SUBMISSION_GUIDE.md
├── requirements.txt
├── packages.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── dashboard.py
├── evaluate_model.py
├── train_improved_model.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── feature_extractor.py
│   ├── improved_model_adapter.py
│   ├── main.py
│   ├── model_adapter.py
│   ├── models.py
│   ├── privacy.py
│   └── risk_engine.py
├── docs/
│   ├── api.md
│   └── architecture.md
├── models/
│   ├── README.md
│   └── improved_voice_model.pkl
├── scripts/
│   ├── demo_model.py
│   └── demo_rolling.py
├── tests/
│   ├── test_api.py
│   └── test_risk_engine.py
├── submission/
│   ├── DEMO.md
│   └── PRESENTATION.md
└── assets/
    └── screenshots/
```

---

# 8. Installation

```bash
git clone https://github.com/kritig-09/voice-cloning-guard.git
cd voice-cloning-guard
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Ensure FFmpeg is installed and available on PATH, or set `FFMPEG_BIN` to the executable path.

---

# 9. Run the Backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` for the API and `http://127.0.0.1:8000/docs` for Swagger.

---

# 10. Run the Dashboard

In a second terminal:

```powershell
.\.venv\Scripts\python.exe -m streamlit run dashboard.py
```

Open:

```text
http://localhost:8501
```

For a separately hosted API, set:

```powershell
$env:VCG_API_URL = "https://your-api-host.example"
```

---

# 11. Training the Improved Prototype

Training data should be organized as:

```text
evaluation_data/
├── real/
│   ├── real_01.wav
│   └── ...
└── fake/
    ├── fake_01.wav
    └── ...
```

Run:

```bash
python train_improved_model.py --data evaluation_data --output models/improved_voice_model.pkl
```

For a defensible benchmark, use independent train/validation/test splits, avoid speaker leakage, document sample provenance, and use genuine synthetic speech from multiple generators rather than arbitrary AI-generated sound effects.

---

# 12. Evaluation

Run:

```bash
python evaluate_model.py --model models/improved_voice_model.pkl --data evaluation_data
```

Metrics should only be reported together with dataset composition, class definitions, split protocol, speaker separation, and provenance. The current prototype evaluation data is not sufficient to claim production-level accuracy.

---

# 13. Testing

```bash
python -m pytest -q
```

The repository contains policy and API-level tests for core service behavior.

---

# 14. Current Limitations

VoiceCloneGuard is intentionally documented as a prototype. Current limitations include:

- the improved model is a classical-ML research prototype rather than a production-grade deepfake detector;
- the present benchmark dataset is limited and may not represent deployment conditions;
- dedicated OOD detection is not yet trained;
- dedicated speaker-embedding verification is not yet integrated into the final decision;
- performance can vary across languages, microphones, codecs, compression, noise conditions, and unseen synthesis systems;
- direct telephony/VoIP integration is not yet implemented.

---

# 15. Future Enhancements

1. Train and evaluate on larger, diverse anti-spoofing benchmarks.
2. Add pretrained speech embeddings for stronger generalization.
3. Train a dedicated OOD detector.
4. Add speaker-consistency and speaker-verification fusion.
5. Calibrate probabilities on a held-out validation set.
6. Add real-time VoIP and call-center integration.
7. Add model/version monitoring and audit trails.
8. Evaluate robustness across languages, codecs, microphones, noise, and unseen generators.

---

# 16. SIH Submission

See:

- [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md)
- [submission/PRESENTATION.md](submission/PRESENTATION.md)
- [submission/DEMO.md](submission/DEMO.md)

---

# 17. License

MIT — see [LICENSE](LICENSE).
