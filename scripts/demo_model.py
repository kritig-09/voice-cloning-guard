from pathlib import Path

import librosa

from app.model_adapter import VoiceCloningModelAdapter

MODEL_PATH = Path("models/voice_cloning_model.pkl")
if not MODEL_PATH.exists():
    raise SystemExit(f"Model not found: {MODEL_PATH}")

adapter = VoiceCloningModelAdapter(MODEL_PATH)
for filename in ("sample_real.flac", "sample_fake.flac"):
    path = Path(filename)
    if not path.exists():
        print(f"NOT FOUND: {filename}")
        continue
    waveform, sample_rate = librosa.load(path, sr=None, mono=True)
    result = adapter.predict(waveform, sample_rate)
    print(f"\n{filename}")
    print(f"Spoof probability: {result.spoof_probability:.4f}")
    print(f"OOD score: {result.ood_score:.4f}")
    for item in result.explanation:
        print(f"  - {item}")
