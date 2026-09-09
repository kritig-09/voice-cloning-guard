import argparse
from pathlib import Path

import joblib
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from app.feature_extractor import extract_features

AUDIO_EXTENSIONS = {".flac", ".wav", ".mp3", ".m4a", ".aac", ".ogg", ".mpeg", ".mpg"}


def collect_samples(dataset_dir: Path):
    samples = []
    for label_name, label in (("real", 0), ("fake", 1)):
        folder = dataset_dir / label_name
        if not folder.exists():
            continue
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                samples.append((path, label))
    return samples


def load_dataset(dataset_dir: Path):
    X, y, names = [], [], []
    for path, label in collect_samples(dataset_dir):
        try:
            waveform, sample_rate = librosa.load(path, sr=None, mono=True)
            features = extract_features(waveform, sample_rate)
            X.append(features)
            y.append(label)
            names.append(path.name)
            print(f"[OK] {path.name} -> {features.shape[0]} features")
        except Exception as exc:
            print(f"[FAIL] {path.name} -> {type(exc).__name__}: {exc}")
    if not X:
        raise SystemExit("No usable audio files found.")
    return np.asarray(X), np.asarray(y), names


def main():
    parser = argparse.ArgumentParser(description="Train VoiceCloneGuard's rich-feature prototype model.")
    parser.add_argument("--data", default="evaluation_data")
    parser.add_argument("--output", default="models/improved_voice_model.pkl")
    args = parser.parse_args()

    X, y, _ = load_dataset(Path(args.data))
    print(f"\nSamples: {len(y)}")
    print(f"Features: {X.shape[1]}")
    print(f"Real: {(y == 0).sum()} | AI-cloned: {(y == 1).sum()}")

    model = RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    min_class_count = int(min(np.sum(y == 0), np.sum(y == 1)))
    if min_class_count >= 2:
        n_splits = min(5, min_class_count)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        probabilities = cross_val_predict(model, X, y, cv=cv, method="predict_proba", n_jobs=-1)
        predictions = np.argmax(probabilities, axis=1)
        print("\nCross-validation estimates")
        print(f"Accuracy : {accuracy_score(y, predictions) * 100:.2f}%")
        print(f"Precision: {precision_score(y, predictions, zero_division=0) * 100:.2f}%")
        print(f"Recall   : {recall_score(y, predictions, zero_division=0) * 100:.2f}%")
        print(f"F1-score : {f1_score(y, predictions, zero_division=0) * 100:.2f}%")
        if len(set(y)) == 2:
            print(f"ROC-AUC  : {roc_auc_score(y, probabilities[:, 1]):.4f}")
    else:
        print("\nSkipping cross-validation: each class needs at least two samples.")

    model.fit(X, y)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_count": int(X.shape[1]),
            "feature_version": "rich_v1",
            "sample_count": int(len(y)),
        },
        output,
    )
    print(f"\nSaved prototype model to {output}")


if __name__ == "__main__":
    main()
