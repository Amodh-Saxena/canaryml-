import pytest
from fastapi.testclient import TestClient


# Mock the model before importing the app
class MockModel:
    def predict(self, texts):
        # Return 1 for all texts
        return [1] * len(texts)

import app.model_loader

app.model_loader.load_model = lambda: MockModel()

from app.main import app as fastapi_app


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    monkeypatch.setenv("MODEL_VERSION", "v1-test")
    monkeypatch.setenv("MODEL_PATH", "dummy.joblib")

def test_healthz():
    with TestClient(fastapi_app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_predict_no_label():
    with TestClient(fastapi_app) as client:
        response = client.post("/predict", json={"text": "Hello world"})
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == 1
        assert data["model_version"] == "v1-test"

def test_predict_with_label():
    with TestClient(fastapi_app) as client:
        response = client.post("/predict", json={"text": "Hello world", "true_label": 1})
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == 1

def test_metrics():
    with TestClient(fastapi_app) as client:
        # Make a request to ensure some metrics are recorded
        client.post("/predict", json={"text": "Hello world", "true_label": 1})
        
        response = client.get("/metrics")
        assert response.status_code == 200
        text = response.text
        
        # Check that our custom metrics are present
        assert "http_requests_total" in text
        assert "http_request_duration_seconds" in text
        assert "model_predictions_total" in text
        assert 'model_version="v1-test"' in text
        assert 'correct="true"' in text
