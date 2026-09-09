from pathlib import Path

import joblib
import numpy as np

from .feature_extractor import extract_features
from .models import DetectionResult


class ImprovedVoiceModelAdapter:
    """Adapter for the prototype's rich-feature Random Forest model."""

    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Improved model not found: {self.model_path.resolve()}")

        bundle = joblib.load(self.model_path)
        if not isinstance(bundle, dict) or "model" not in bundle:
            raise ValueError("Improved model file does not contain the expected model bundle.")

        self.model = bundle["model"]
        self.feature_count = int(bundle["feature_count"])
        self.feature_version = bundle.get("feature_version", "unknown")
        self.sample_count = int(bundle.get("sample_count", 0))

    def predict(self, waveform: np.ndarray, sample_rate: int) -> DetectionResult:
        waveform = np.asarray(waveform, dtype=np.float32)
        if waveform.ndim > 1:
            waveform = np.mean(waveform, axis=1)
        if waveform.size == 0:
            return DetectionResult(0.0, ood_score=1.0, explanation=["Empty audio received."])

        features = extract_features(waveform, sample_rate)
        if features.shape[0] != self.feature_count:
            raise ValueError(
                f"Feature count mismatch: expected {self.feature_count}, got {features.shape[0]}."
            )

        probabilities = self.model.predict_proba(features.reshape(1, -1))[0]
        classes = {int(label): index for index, label in enumerate(self.model.classes_)}
        real_index = classes[0]
        spoof_index = classes[1]

        real_probability = float(probabilities[real_index])
        spoof_probability = float(probabilities[spoof_index])

        return DetectionResult(
            spoof_probability=spoof_probability,
            ood_score=0.0,  # Explicitly a hook; no OOD model is trained yet.
            explanation=[
                f"AI-cloned probability: {spoof_probability:.3f}",
                f"Real-voice probability: {real_probability:.3f}",
                f"{self.feature_count} rich audio features analyzed.",
                f"Feature pipeline: {self.feature_version}.",
            ],
        )
