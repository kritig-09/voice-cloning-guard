from pathlib import Path

import librosa
import numpy as np

from app.feature_extractor import extract_features
from app.ood_detector import OODDetector


REAL_DIR = Path(
    r"D:\SIH26104_NextLevel_Files\Voice_Clone_Upgrade_Scaffold\evaluation_data\real"
)

V1_PATH = Path(
    r"D:\SIHHHH\models\ood_detector.pkl"
)

V2_PATH = Path(
    r"C:\Users\mohit\Downloads\ood_detector_v2.pkl"
)


v1 = OODDetector(V1_PATH)
v2 = OODDetector(V2_PATH)

files = sorted(
    p for p in REAL_DIR.iterdir()
    if p.is_file()
)

v1_scores = []
v2_scores = []

print("FILE | V1 | V2")
print("-" * 100)

for path in files:
    y, sr = librosa.load(
        str(path),
        sr=None,
        mono=True
    )

    features = extract_features(y, sr)

    r1 = v1.score(features)
    r2 = v2.score(features)

    s1 = r1["raw_score"]
    s2 = r2["raw_score"]

    v1_scores.append(s1)
    v2_scores.append(s2)

    print(
        f"{path.name}\n"
        f"  V1: {s1:.6f} ({r1['status']})\n"
        f"  V2: {s2:.6f} ({r2['status']})"
    )

print("\nSUMMARY")
print("-" * 50)

print(f"V1 mean: {np.mean(v1_scores):.6f}")
print(f"V2 mean: {np.mean(v2_scores):.6f}")

print(
    f"V1 high: "
    f"{sum(x >= v1.HIGH_THRESHOLD for x in v1_scores)}/{len(v1_scores)}"
)

print(
    f"V2 high: "
    f"{sum(x >= v2.HIGH_THRESHOLD for x in v2_scores)}/{len(v2_scores)}"
)

print(
    f"V1 watch/high: "
    f"{sum(x >= v1.WATCH_THRESHOLD for x in v1_scores)}/{len(v1_scores)}"
)

print(
    f"V2 watch/high: "
    f"{sum(x >= v2.WATCH_THRESHOLD for x in v2_scores)}/{len(v2_scores)}"
)