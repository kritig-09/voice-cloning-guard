from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np


class OODDetector:
    """
    Calibrated out-of-distribution detector for VoiceCloneGuard.

    The underlying model is an Isolation Forest trained on bona-fide
    reference speech plus controlled channel variations.

    IMPORTANT:
    OOD risk measures acoustic unfamiliarity relative to the reference
    distribution. It is NOT an AI/deepfake probability and it is NOT
    speaker identity verification.
    """

    DEFAULT_WATCH_THRESHOLD = -0.024532160645153823
    DEFAULT_HIGH_THRESHOLD = -0.010862184863862976

    def __init__(
        self,
        model_path: str | Path,
        calibration_path: str | Path | None = None,
    ) -> None:
        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"OOD model not found: {self.model_path}"
            )

        artifact: dict[str, Any] = joblib.load(self.model_path)

        required = {
            "model",
            "scaler",
            "feature_count",
            "feature_version",
        }
        missing = required.difference(artifact)

        if missing:
            raise ValueError(
                "Invalid OOD artifact. "
                f"Missing keys: {sorted(missing)}"
            )

        self.model = artifact["model"]
        self.scaler = artifact["scaler"]
        self.feature_count = int(artifact["feature_count"])
        self.feature_version = str(artifact["feature_version"])

        if self.feature_count != 102:
            raise ValueError(
                f"Expected 102 OOD features, got {self.feature_count}"
            )

        self.real_score_sorted: np.ndarray | None = None

        # Prefer thresholds from the calibration artifact when available.
        self.watch_threshold = self.DEFAULT_WATCH_THRESHOLD
        self.high_threshold = self.DEFAULT_HIGH_THRESHOLD

        if calibration_path is not None:
            calibration_file = Path(calibration_path)

            if calibration_file.exists():
                calibration: dict[str, Any] = joblib.load(
                    calibration_file
                )

                scores = np.asarray(
                    calibration.get("real_score_sorted", []),
                    dtype=np.float64,
                )

                if scores.size:
                    self.real_score_sorted = np.sort(scores)

                if "watch_threshold" in calibration:
                    self.watch_threshold = float(
                        calibration["watch_threshold"]
                    )

                if "high_threshold" in calibration:
                    self.high_threshold = float(
                        calibration["high_threshold"]
                    )

    @property
    def WATCH_THRESHOLD(self) -> float:
        """Backward-compatible threshold name."""
        return self.watch_threshold

    @property
    def HIGH_THRESHOLD(self) -> float:
        """Backward-compatible threshold name."""
        return self.high_threshold

    def _percentile(self, raw_score: float) -> float | None:
        """
        Estimate the percentile of a raw anomaly score relative to the
        held-out bona-fide calibration distribution.
        """
        if (
            self.real_score_sorted is None
            or self.real_score_sorted.size == 0
        ):
            return None

        scores = self.real_score_sorted
        position = np.searchsorted(
            scores,
            raw_score,
            side="right",
        )

        percentile = (
            position / scores.size
        ) * 100.0

        return float(
            np.clip(percentile, 0.0, 100.0)
        )

    def _normalized_risk(self, raw_score: float) -> float:
        """
        Convert the calibrated percentile into a smooth 0-1
        acoustic-unfamiliarity risk signal.

        This is NOT an AI/deepfake probability.
        """
        percentile = self._percentile(raw_score)

        if percentile is None:
            # Fallback when no calibration distribution is available.
            span = self.high_threshold - self.watch_threshold

            if span <= 0:
                return 0.0

            fallback = (
                raw_score - self.watch_threshold
            ) / span

            return float(
                np.clip(fallback, 0.0, 1.0)
            )

        # Map the central percentile range to [0, 1], then square it
        # so only the upper tail produces strong OOD risk.
        normalized = np.clip(
            (percentile - 50.0) / 50.0,
            0.0,
            1.0,
        )

        shaped = normalized ** 2.0

        return float(
            np.clip(shaped, 0.0, 1.0)
        )

    def score(self, features: np.ndarray) -> dict[str, Any]:
        """
        Score one 102-dimensional rich acoustic feature vector.

        Returns raw anomaly score, calibrated OOD risk, calibration
        percentile, categorical status, and a plain-English interpretation.
        """
        x = np.asarray(
            features,
            dtype=np.float32,
        ).reshape(1, -1)

        if x.shape[1] != self.feature_count:
            raise ValueError(
                f"Expected {self.feature_count} features, "
                f"got {x.shape[1]}"
            )

        if not np.isfinite(x).all():
            raise ValueError(
                "OOD features contain NaN or infinite values."
            )

        x_scaled = self.scaler.transform(x)

        # Isolation Forest:
        # decision_function higher => more in-distribution.
        # Negation gives an intuitive anomaly direction.
        raw_score = float(
            -self.model.decision_function(x_scaled)[0]
        )

        percentile = self._percentile(raw_score)
        ood_risk = self._normalized_risk(raw_score)

        if raw_score >= self.high_threshold:
            status = "high"
            interpretation = (
                "Audio differs substantially from the "
                "reference speech distribution."
            )
        elif raw_score >= self.watch_threshold:
            status = "watch"
            interpretation = (
                "Audio shows some acoustic unfamiliarity "
                "and may require additional evidence."
            )
        else:
            status = "normal"
            interpretation = (
                "Audio is broadly consistent with the "
                "reference speech distribution."
            )

        return {
            "raw_score": raw_score,
            "ood_risk": ood_risk,
            "percentile": percentile,
            "status": status,
            "interpretation": interpretation,
        }
