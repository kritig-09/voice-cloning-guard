from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_exists():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "model_connected" in payload


def test_score_endpoint():
    response = client.post(
        "/score",
        json={"spoof_probability": 0.1},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "result" in payload
    assert "evidence" in payload
