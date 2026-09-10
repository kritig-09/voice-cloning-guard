import argparse
from pathlib import Path

import joblib
import librosa
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_predict
from sklearn.neural_network import MLPClassifier

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


def build_random_forest():
    return RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def build_tuned_random_forest(X, y, min_class_count):
    """RandomizedSearchCV over RandomForest hyperparameters.

    Search folds are capped by the smallest class count, the same constraint
    used for the outer cross-validation reporting below, so this degrades
    gracefully on small datasets instead of crashing on too few folds.
    """
    base = RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1)
    param_distributions = {
        "n_estimators": [200, 300, 500, 800],
        "max_depth": [None, 8, 16, 32],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", 0.5],
    }
    n_splits = min(5, max(2, min_class_count))
    n_iter = min(12, 4 * 4 * 3 * 3)
    search = RandomizedSearchCV(
        base,
        param_distributions,
        n_iter=n_iter,
        cv=StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42),
        scoring="roc_auc",
        random_state=42,
        n_jobs=-1,
    )
    search.fit(X, y)
    print(f"\nBest params from search: {search.best_params_}")
    print(f"Best CV ROC-AUC during search: {search.best_score_:.4f}")
    return search.best_estimator_


def build_ensemble():
    """Soft-voting ensemble of three different model families.

    Averaging across RandomForest, GradientBoosting, and a small MLP tends to
    reduce variance versus any single model and gives steadier probability
    estimates -- useful on a small-dataset prototype where one model's
    cross-validation score can swing a lot between folds.
    """
    rf = RandomForestClassifier(n_estimators=400, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1)
    gb = GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=42)
    mlp = MLPClassifier(hidden_layer_sizes=(64,), max_iter=2000, random_state=42)
    return VotingClassifier(estimators=[("rf", rf), ("gb", gb), ("mlp", mlp)], voting="soft")


def main():
    parser = argparse.ArgumentParser(description="Train VoiceCloneGuard's rich-feature prototype model.")
    parser.add_argument("--data", default="evaluation_data")
    parser.add_argument("--output", default="models/improved_voice_model.pkl")
    parser.add_argument(
        "--model-type",
        choices=["rf", "tuned-rf", "ensemble"],
        default="rf",
        help=(
            "rf: current fixed RandomForest (previous default behavior). "
            "tuned-rf: RandomizedSearchCV over RandomForest hyperparameters. "
            "ensemble: soft-voting RandomForest + GradientBoosting + MLP."
        ),
    )
    args = parser.parse_args()

    X, y, _ = load_dataset(Path(args.data))
    print(f"\nSamples: {len(y)}")
    print(f"Features: {X.shape[1]}")
    print(f"Real: {(y == 0).sum()} | AI-cloned: {(y == 1).sum()}")

    min_class_count = int(min(np.sum(y == 0), np.sum(y == 1)))

    if args.model_type == "tuned-rf":
        if min_class_count < 2:
            print("\nNot enough samples per class to run hyperparameter search; falling back to the default RandomForest.")
            model = build_random_forest()
        else:
            model = build_tuned_random_forest(X, y, min_class_count)
    elif args.model_type == "ensemble":
        model = build_ensemble()
    else:
        model = build_random_forest()

    if min_class_count >= 2:
        n_splits = min(5, min_class_count)
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        probabilities = cross_val_predict(model, X, y, cv=cv, method="predict_proba", n_jobs=-1)
        predictions = np.argmax(probabilities, axis=1)
        print(f"\nCross-validation estimates ({args.model_type})")
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
            "model_type": args.model_type,
        },
        output,
    )
    print(f"\nSaved prototype model to {output}")


if __name__ == "__main__":
    main()
