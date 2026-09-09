from collections import deque

from .models import Context, DetectionResult, RiskResult


class RollingRiskEngine:
    """Temporal fusion and conservative security policy."""

    def __init__(
        self,
        maxlen: int = 8,
        verify_threshold: float = 0.55,
        escalate_threshold: float = 0.78,
    ) -> None:
        if maxlen < 1:
            raise ValueError("maxlen must be at least 1")
        if not 0 <= verify_threshold <= escalate_threshold <= 1:
            raise ValueError("thresholds must satisfy 0 <= verify <= escalate <= 1")

        self.scores = deque(maxlen=maxlen)
        self.ood_scores = deque(maxlen=maxlen)
        self.verify_threshold = verify_threshold
        self.escalate_threshold = escalate_threshold

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def update(self, det: DetectionResult, ctx: Context) -> RiskResult:
        p = self._clamp(det.spoof_probability)
        ood = self._clamp(det.ood_score)
        transaction_risk = self._clamp(ctx.transaction_risk)

        self.scores.append(p)
        self.ood_scores.append(ood)

        weights = list(range(1, len(self.scores) + 1))
        smoothed = sum(score * weight for score, weight in zip(self.scores, weights)) / sum(weights)
        avg_ood = sum(self.ood_scores) / len(self.ood_scores)

        # Context changes the response policy, not the model probability.
        context_boost = 0.10 * transaction_risk
        risk = self._clamp(0.82 * smoothed + context_boost)

        reasons: list[str] = []
        if smoothed >= self.verify_threshold:
            reasons.append("Synthetic-voice signal is persistently elevated")
        if avg_ood >= 0.60:
            reasons.append("Audio differs from the model's known distribution")
        if transaction_risk >= 0.70:
            reasons.append("High-risk transaction context")
        if ctx.verified_contact:
            reasons.append("Known contact context available")

        # Uncertainty lowers confidence instead of manufacturing certainty.
        confidence = self._clamp((1.0 - avg_ood) * (0.55 + 0.45 * abs(smoothed - 0.5) * 2))
        if avg_ood >= 0.60:
            confidence *= 0.60
        confidence = self._clamp(confidence)

        if risk >= self.escalate_threshold and confidence >= 0.55:
            action: str = "escalate"
        elif risk >= self.verify_threshold or avg_ood >= 0.60:
            action = "verify"
        else:
            action = "allow"

        return RiskResult(
            risk_score=risk,
            confidence=confidence,
            action=action,  # type: ignore[arg-type]
            reasons=reasons,
        )
