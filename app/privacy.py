from datetime import datetime, timezone
from typing import Any


def make_event(
    *,
    risk_score: float,
    confidence: float,
    action: str,
    reasons: list[str],
    session_id: str,
) -> dict[str, Any]:
    """Create metadata-only evidence; raw audio is intentionally excluded."""

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "risk_score": round(float(risk_score), 4),
        "confidence": round(float(confidence), 4),
        "action": action,
        "reasons": list(reasons[:6]),
        "raw_audio_retained": False,
    }
