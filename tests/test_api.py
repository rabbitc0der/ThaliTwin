"""
test_api.py
Automated integration tests for the ThaliTwin Production FastAPI Clinical Service.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from thalitwin.api.service import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    """Tests the /health system readiness probe."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["active_participants"] == 45

def test_get_patients_triage(client):
    """Tests ward triage patient list."""
    res = client.get("/api/v1/patients")
    assert res.status_code == 200
    patients = res.json()
    assert len(patients) == 45
    p1 = patients[0]
    assert p1["subject_id"] == 1
    assert "91-9999" in p1["abha_id"]
    assert "shrinkage_weight_w" in p1

def test_get_single_patient(client):
    """Tests single patient detail retrieval."""
    res = client.get("/api/v1/patients/1")
    assert res.status_code == 200
    p = res.json()
    assert p["subject_id"] == 1
    assert p["age"] > 0
    assert p["active_tier"] == "T2_Frugal"

def test_predict_excursion_api(client):
    """Tests real-time postprandial glycemic forecast and audit logging."""
    payload = {
        "current_glucose": 110.0,
        "glucose_slope_15m": 0.5,
        "carbs_g": 65.0,
        "fiber_g": 4.0,
        "protein_g": 12.0,
        "fat_g": 8.0,
        "glycemic_load": 28.0,
        "tier": "T2_Frugal",
        "hour_of_day": 13.0
    }
    res = client.post("/api/v1/twin/1/predict", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "predicted_risk" in data
    assert 0.0 <= data["predicted_risk"] <= 1.0
    assert "conformal_lower_bound" in data
    assert "conformal_upper_bound" in data
    assert data["conformal_upper_bound"] > data["conformal_lower_bound"]

def test_whatif_simulate_api(client):
    """Tests nutritional counterfactual simulation endpoint."""
    payload = {
        "dish_id_or_name": "D01",  # Masala Dosa
        "portion_factor": 1.0,
        "post_meal_walk_minutes": 0,
        "compare_with_swap": True,
        "tier": "T2_Frugal"
    }
    res = client.post("/api/v1/twin/1/whatif", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "primary_scenario" in data
    assert data["primary_scenario"]["dish_name"] == "Idli (2 pcs) with Sambar & Coconut Chutney"
    assert "counterfactual_swap" in data
    assert data["predicted_glycemic_attenuation_mg_dl"] > 0

def test_active_inquiry_api(client):
    """Tests unlogged snack velocity anomaly detection."""
    # Fast rise: +30 mg/dL in 15 min = 2.0 mg/dL/min
    payload = {
        "last_glucose": 100.0,
        "current_glucose": 135.0,
        "elapsed_minutes": 15.0,
        "recent_activity_steps": 50
    }
    res = client.post("/api/v1/twin/1/active-inquiry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["anomaly_detected"] is True
    assert "tea" in data["prompt_message"].lower() or "snack" in data["prompt_message"].lower()

def test_abdm_fhir_api(client):
    """Tests ABDM FHIR R4 clinical bundle export endpoint."""
    res = client.get("/api/v1/abdm/fhir/1")
    assert res.status_code == 200
    bundle = res.json()
    assert bundle["resourceType"] == "Bundle"
    assert len(bundle["entry"]) >= 2

def test_audit_logs_api(client):
    """Tests cryptographic audit trail retrieval endpoint."""
    res = client.get("/api/v1/audit/logs?limit=10")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert "request_hash_sha256" in logs[0]
