from app.models import Context, DetectionResult
from app.risk_engine import RollingRiskEngine


def test_low_risk_allows():
    engine = RollingRiskEngine()
    result = engine.update(DetectionResult(0.1), Context())
    assert result.action == "allow"
    assert 0 <= result.risk_score <= 1


def test_persistent_high_score_escalates():
    engine = RollingRiskEngine(maxlen=4, verify_threshold=0.5, escalate_threshold=0.7)
    result = None
    for _ in range(4):
        result = engine.update(DetectionResult(0.95, ood_score=0.1), Context(transaction_risk=0.9))
    assert result is not None
    assert result.action == "escalate"


def test_ood_forces_verification():
    engine = RollingRiskEngine()
    result = engine.update(DetectionResult(0.2, ood_score=0.9), Context())
    assert result.action == "verify"
    assert result.confidence < 0.6
