import json
import os

import pytest


@pytest.fixture
def model_report():
    report_path = os.path.join(os.path.dirname(__file__), "..", "models", "report.json")
    if not os.path.exists(report_path):
        pytest.skip("Model report not found. Run training script first.")
    with open(report_path) as f:
        return json.load(f)

def test_v1_baseline_accuracy(model_report):
    assert "v1" in model_report
    # Baseline should have reasonable accuracy
    assert model_report["v1"] > 0.85

def test_v2_bad_degraded_accuracy(model_report):
    assert "v2-bad" in model_report
    # Bad model should be significantly worse than baseline
    assert model_report["v2-bad"] < 0.75
    assert model_report["v2-bad"] < model_report["v1"] - 0.1

def test_v3_good_improved_accuracy(model_report):
    assert "v3-good" in model_report
    # Good model should be at least as good as baseline
    assert model_report["v3-good"] >= model_report["v1"]
