import argparse
from pathlib import Path

import joblib
import librosa
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from app.improved_model_adapter import ImprovedVoiceModelAdapter
from app.model_adapter import VoiceCloningModelAdapter

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


def load_adapter(model_path: str):
    """Pick the right adapter based on what's actually in the pickle file.

    The original model is a bare sklearn estimator; the improved model is a
    dict bundle (``{"model": ..., "feature_count": ...}``). Auto-detecting
    this means the script works for either model without the caller needing
    to know which one they pointed at.
    """
    raw = joblib.load(model_path)
    if isinstance(raw, dict) and "model" in raw:
        return ImprovedVoiceModelAdapter(model_path)
    return VoiceCloningModelAdapter(model_path)


def predict_file(adapter, path: Path):
    waveform, sample_rate = librosa.load(path, sr=None, mono=True)
    result = adapter.predict(waveform, sample_rate)
    return int(result.spoof_probability >= 0.5), result.spoof_probability


def compute_eer(y_true, y_score):
    fpr, tpr, thresholds = roc_curve(y_true, y_score)
    fnr = 1 - tpr
    eer_index = int(abs(fnr - fpr).argmin())
    eer = (fpr[eer_index] + fnr[eer_index]) / 2
    return float(eer), float(thresholds[eer_index])


def main():
    parser = argparse.ArgumentParser(description="Evaluate VoiceCloneGuard on a labeled audio folder.")
    parser.add_argument("--model", default="models/improved_voice_model.pkl")
    parser.add_argument("--data", default="evaluation_data")
    args = parser.parse_args()

    adapter = load_adapter(args.model)
    samples = collect_samples(Path(args.data))
    if not samples:
        raise SystemExit("No supported audio files found.")

    y_true, y_pred, y_score = [], [], []
    failed = 0

    for path, true_label in samples:
        try:
            predicted, score = predict_file(adapter, path)
            y_true.append(true_label)
            y_pred.append(predicted)
            y_score.append(score)
            print(f"[OK] {path.name}: expected={true_label} predicted={predicted} AI={score:.3f}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {path.name}: {type(exc).__name__}: {exc}")

    if not y_true:
        raise SystemExit("No audio files could be evaluated successfully.")

    print("\nMetrics")
    print(f"Samples   : {len(y_true)}")
    print(f"Failed    : {failed}")
    print(f"Accuracy  : {accuracy_score(y_true, y_pred) * 100:.2f}%")
    print(f"Precision : {precision_score(y_true, y_pred, zero_division=0) * 100:.2f}%")
    print(f"Recall    : {recall_score(y_true, y_pred, zero_division=0) * 100:.2f}%")
    print(f"F1-score  : {f1_score(y_true, y_pred, zero_division=0) * 100:.2f}%")
    if len(set(y_true)) == 2:
        print(f"ROC-AUC   : {roc_auc_score(y_true, y_score):.4f}")
        eer, eer_threshold = compute_eer(y_true, y_score)
        print(f"EER       : {eer * 100:.2f}% (at threshold {eer_threshold:.3f})")
    else:
        print("EER       : n/a (need both classes present to compute)")

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    print("\nConfusion matrix (rows=actual, columns=predicted)")
    print(cm)


if __name__ == "__main__":
    main()
