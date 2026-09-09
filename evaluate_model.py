import argparse
from pathlib import Path

import librosa
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

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


def predict_file(adapter, path: Path):
    waveform, sample_rate = librosa.load(path, sr=None, mono=True)
    result = adapter.predict(waveform, sample_rate)
    return int(result.spoof_probability >= 0.5), result.spoof_probability


def main():
    parser = argparse.ArgumentParser(description="Evaluate VoiceCloneGuard on a labeled audio folder.")
    parser.add_argument("--model", default="models/voice_cloning_model.pkl")
    parser.add_argument("--data", default="evaluation_data")
    args = parser.parse_args()

    adapter = VoiceCloningModelAdapter(args.model)
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

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    print("\nConfusion matrix (rows=actual, columns=predicted)")
    print(cm)


if __name__ == "__main__":
    main()
