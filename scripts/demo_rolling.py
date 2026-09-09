from pathlib import Path

import librosa

from app.model_adapter import VoiceCloningModelAdapter
from app.models import Context
from app.risk_engine import RollingRiskEngine

MODEL_PATH = Path("models/voice_cloning_model.pkl")
if not MODEL_PATH.exists():
    raise SystemExit(f"Model not found: {MODEL_PATH}")

adapter = VoiceCloningModelAdapter(MODEL_PATH)

for filename in ("sample_real.flac", "sample_fake.flac"):
    path = Path(filename)
    if not path.exists():
        print(f"NOT FOUND: {filename}")
        continue

    audio, sr = librosa.load(path, sr=None, mono=True)
    window_size = max(1, int(4 * sr))
    hop_size = max(1, int(1 * sr))
    engine = RollingRiskEngine()

    print("\n" + "=" * 60)
    print(f"FILE: {filename}")
    print(f"Duration: {len(audio) / sr:.2f} sec")
    print("=" * 60)

    starts = [0] if len(audio) <= window_size else list(range(0, len(audio) - window_size + 1, hop_size))
    for idx, start in enumerate(starts, 1):
        end = min(len(audio), start + window_size)
        detection = adapter.predict(audio[start:end], sr)
        risk = engine.update(detection, Context())
        print(
            f"Window {idx:02d} | {start/sr:5.1f}-{end/sr:5.1f}s | "
            f"Spoof={detection.spoof_probability:.3f} | Risk={risk.risk_score:.3f} | "
            f"Confidence={risk.confidence:.3f} | Action={risk.action}"
        )
