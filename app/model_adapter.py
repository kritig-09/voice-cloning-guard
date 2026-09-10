from abc import ABC, abstractmethod
from pathlib import Path

import joblib
import librosa
import numpy as np

from .models import DetectionResult


class ModelAdapter(ABC):
    """Interface shared by detector implementations."""

    @abstractmethod
    def predict(self, waveform: np.ndarray, sample_rate: int) -> DetectionResult:
        raise NotImplementedError


class VoiceCloningModelAdapter(ModelAdapter):
    """Adapter for the original ``voice_cloning_model.pkl`` detector.

    The original model expects 16 kHz mono audio, 13 mean MFCC features,
    and the original class convention of 0 = AI-cloned and 1 = real voice.
    """

    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path.resolve()}")
        self.model = joblib.load(self.model_path)
        # Metadata for UI/health transparency. The original model predates the
        # bundle-with-metadata format the improved model uses, so these are
        # fixed constants describing the known, fixed pipeline rather than
        # values read from the file itself.
        self.feature_count = 13
        self.feature_version = "original_mfcc13"
        self.sample_count = None

    def predict(self, waveform: np.ndarray, sample_rate: int) -> DetectionResult:
        waveform = np.asarray(waveform, dtype=np.float32)
        if waveform.ndim > 1:
            waveform = np.mean(waveform, axis=1)
        if waveform.size == 0:
            return DetectionResult(0.0, ood_score=1.0, explanation=["Empty audio received."])

        if sample_rate != 16000:
            waveform = librosa.resample(waveform, orig_sr=sample_rate, target_sr=16000)

        if float(np.max(np.abs(waveform))) < 0.01:
            return DetectionResult(0.0, ood_score=1.0, explanation=["Audio is silent or extremely low level."])

        mfcc = librosa.feature.mfcc(y=waveform, sr=16000, n_mfcc=13)
        features = np.mean(mfcc, axis=1).reshape(1, -1)
        probabilities = self.model.predict_proba(features)[0]

        classes = {int(label): index for index, label in enumerate(self.model.classes_)}
        spoof_index = classes.get(0, 0)
        real_index = classes.get(1, min(1, len(probabilities) - 1))

        spoof_probability = float(probabilities[spoof_index])
        real_probability = float(probabilities[real_index])

        return DetectionResult(
            spoof_probability=spoof_probability,
            ood_score=0.0,
            explanation=[
                f"AI-cloned probability: {spoof_probability:.3f}",
                f"Real-voice probability: {real_probability:.3f}",
                "13 MFCC mean features analyzed.",
            ],
        )
