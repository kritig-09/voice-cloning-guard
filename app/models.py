from dataclasses import dataclass, field
from typing import Literal, Optional

Action = Literal["allow", "verify", "escalate"]


@dataclass
class DetectionResult:
    """Model-level evidence for one audio window."""

    spoof_probability: float
    ood_score: float = 0.0
    speaker_consistency: Optional[float] = None
    explanation: list[str] = field(default_factory=list)


@dataclass
class Context:
    """Optional context that can raise the response level."""

    transaction_risk: float = 0.0
    channel: str = "unknown"
    verified_contact: bool = False


@dataclass
class RiskResult:
    """Policy result after temporal/context fusion."""

    risk_score: float
    confidence: float
    action: Action
    reasons: list[str]
