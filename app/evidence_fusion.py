from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FusionResult:
    """Combined security evidence without replacing the primary detector."""

    primary_risk: float
    ood_risk: float
    fused_risk: float
    confidence_adjustment: float
    adjusted_confidence: float
    action_hint: str
    reasons: list[str]


class EvidenceFusion:
    """
    Conservative evidence-fusion layer.

    Primary detector remains dominant. OOD is a bounded secondary signal.

    Policy:
    - High spoof + high OOD:
        corroborating evidence -> modest risk increase + confidence boost.
    - Elevated spoof + watch/high OOD:
        supporting evidence -> modest risk increase.
    - Low spoof + high OOD:
        unfamiliar audio -> small risk increase + confidence penalty.
    - Low spoof + normal OOD:
        preserve the primary result.
    """

    MAX_OOD_RISK_CONTRIBUTION = 0.10

    HIGH_SPOOF_THRESHOLD = 0.75
    VERIFY_SPOOF_THRESHOLD = 0.55

    HIGH_OOD_RISK = 0.75
    WATCH_OOD_RISK = 0.50

    HIGH_OOD_SUPPORT_CONFIDENCE = 0.06
    HIGH_OOD_UNCERTAINTY_PENALTY = 0.10
    WATCH_OOD_UNCERTAINTY_PENALTY = 0.04

    def combine(
        self,
        primary_risk: float,
        primary_confidence: float,
        spoof_probability: float,
        ood_risk: float | None,
        ood_status: str | None,
        primary_action: str,
    ) -> FusionResult:
        """Combine existing risk with calibrated OOD evidence."""

        primary_risk = self._clip(primary_risk)
        primary_confidence = self._clip(primary_confidence)
        spoof_probability = self._clip(spoof_probability)

        if ood_risk is None:
            return FusionResult(
                primary_risk=primary_risk,
                ood_risk=0.0,
                fused_risk=primary_risk,
                confidence_adjustment=0.0,
                adjusted_confidence=primary_confidence,
                action_hint=primary_action,
                reasons=[],
            )

        ood_risk = self._clip(ood_risk)
        status = (ood_status or "normal").lower()

        # OOD is intentionally bounded so it cannot dominate the
        # primary spoof detector.
        contribution = (
            ood_risk * self.MAX_OOD_RISK_CONTRIBUTION
        )

        # For low-spoof audio, OOD indicates unfamiliarity rather than
        # synthetic evidence. Keep its direct risk contribution smaller.
        if spoof_probability < self.VERIFY_SPOOF_THRESHOLD:
            contribution = min(contribution, 0.04)

        fused_risk = self._clip(
            primary_risk + contribution
        )

        confidence_adjustment = 0.0
        reasons: list[str] = []

        high_ood = (
            status == "high"
            or ood_risk >= self.HIGH_OOD_RISK
        )

        watch_ood = (
            status == "watch"
            or ood_risk >= self.WATCH_OOD_RISK
        )

        if high_ood and spoof_probability >= self.VERIFY_SPOOF_THRESHOLD:
            # The two independent signals corroborate the primary
            # suspicion, so confidence in the security assessment rises.
            confidence_adjustment = (
                self.HIGH_OOD_SUPPORT_CONFIDENCE
            )
            reasons.append(
                "Synthetic signal and acoustic unfamiliarity agree."
            )

        elif high_ood:
            # Low spoof + high OOD is an uncertainty condition, not a
            # deepfake verdict.
            confidence_adjustment = (
                -self.HIGH_OOD_UNCERTAINTY_PENALTY
            )
            reasons.append(
                "Audio is acoustically unfamiliar despite a low synthetic signal."
            )

        elif watch_ood:
            confidence_adjustment = (
                -self.WATCH_OOD_UNCERTAINTY_PENALTY
            )
            reasons.append(
                "Acoustic profile shows some unfamiliarity."
            )

        adjusted_confidence = self._clip(
            primary_confidence + confidence_adjustment
        )

        if (
            spoof_probability >= self.HIGH_SPOOF_THRESHOLD
            and high_ood
        ):
            action_hint = "strong_verification"

        elif (
            spoof_probability >= self.VERIFY_SPOOF_THRESHOLD
            and watch_ood
        ):
            action_hint = "verify"

        elif (
            spoof_probability < self.VERIFY_SPOOF_THRESHOLD
            and high_ood
        ):
            action_hint = "caution"

        elif (
            spoof_probability < self.VERIFY_SPOOF_THRESHOLD
            and watch_ood
        ):
            action_hint = "allow_with_caution"

        else:
            action_hint = primary_action

        return FusionResult(
            primary_risk=primary_risk,
            ood_risk=ood_risk,
            fused_risk=fused_risk,
            confidence_adjustment=confidence_adjustment,
            adjusted_confidence=adjusted_confidence,
            action_hint=action_hint,
            reasons=reasons,
        )

    @staticmethod
    def _clip(value: float) -> float:
        return float(np.clip(value, 0.0, 1.0))
