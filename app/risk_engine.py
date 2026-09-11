from collections import deque

from .models import Context, DetectionResult, RiskResult


class RollingRiskEngine:
    """Temporal fusion and conservative security policy."""

    def __init__(
        self,
        maxlen: int = 8,
        verify_threshold: float = 0.55,
        escalate_threshold: float = 0.78,
        ood_verify_threshold: float = 0.60,
    ) -> None:
        if maxlen < 1:
            raise ValueError("maxlen must be at least 1")

        if not 0 <= verify_threshold <= escalate_threshold <= 1:
            raise ValueError(
                "thresholds must satisfy 0 <= verify <= escalate <= 1"
            )

        if not 0 <= ood_verify_threshold <= 1:
            raise ValueError(
                "ood_verify_threshold must be between 0 and 1"
            )

        self.scores = deque(maxlen=maxlen)
        self.ood_scores = deque(maxlen=maxlen)

        self.verify_threshold = verify_threshold
        self.escalate_threshold = escalate_threshold
        self.ood_verify_threshold = ood_verify_threshold

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def update(
        self,
        det: DetectionResult,
        ctx: Context,
    ) -> RiskResult:
        spoof_probability = self._clamp(
            det.spoof_probability
        )

        ood_score = self._clamp(det.ood_score)
        transaction_risk = self._clamp(ctx.transaction_risk)

        self.scores.append(spoof_probability)
        self.ood_scores.append(ood_score)

        weights = list(range(1, len(self.scores) + 1))

        smoothed_spoof = (
            sum(
                score * weight
                for score, weight in zip(
                    self.scores,
                    weights,
                )
            )
            / sum(weights)
        )

        avg_ood = (
            sum(self.ood_scores)
            / len(self.ood_scores)
        )

        # Context affects policy, not classifier probability.
        context_boost = 0.10 * transaction_risk

        # OOD does NOT increase the synthetic score.
        risk = self._clamp(
            0.82 * smoothed_spoof
            + context_boost
        )

        reasons: list[str] = []

        if smoothed_spoof >= self.verify_threshold:
            reasons.append(
                "Synthetic-voice signal is elevated"
            )

        if avg_ood >= self.ood_verify_threshold:
            reasons.append(
                "Audio is outside the known reference distribution"
            )

        if transaction_risk >= 0.70:
            reasons.append(
                "High-risk transaction context"
            )

        if ctx.verified_contact:
            reasons.append(
                "Known contact context available"
            )

        # ----------------------------------------------------
        # MODEL CONFIDENCE
        # ----------------------------------------------------
        #
        # This measures how far the spoof probability is from
        # the ambiguous midpoint (0.5).
        #
        # OOD is intentionally NOT multiplied into this value.
        #
        model_confidence = self._clamp(
            0.55
            + 0.45 * abs(smoothed_spoof - 0.5) * 2
        )

        # ----------------------------------------------------
        # DECISION POLICY
        # ----------------------------------------------------
        #
        # High OOD means the model is operating outside the
        # reference distribution. Therefore do not escalate
        # automatically even when the spoof score is high.
        #
        if (
            risk >= self.escalate_threshold
            and model_confidence >= 0.55
            and avg_ood < self.ood_verify_threshold
        ):
            action: str = "escalate"

        elif (
            risk >= self.verify_threshold
            or avg_ood >= self.ood_verify_threshold
        ):
            action = "verify"

        else:
            action = "allow"

        return RiskResult(
            risk_score=risk,
            confidence=model_confidence,
            action=action,  # type: ignore[arg-type]
            reasons=reasons,
        )