"""Serving-endpoint tests. Auto-skips when MODEL_NAME isn't set (e.g. in CI),
so it never breaks the existing suite. Run locally after setting the env vars."""
from __future__ import annotations
import os
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("MODEL_NAME"),
    reason="MODEL_NAME not set; skipping endpoint tests (e.g. CI).",
)

VALID = {
    "LeftRight": "L", "Area": "North", "Brand": "BrandA", "Make": "Make1",
    "Test_Quarter": "Q3", "Test_Year": 2022, "Size": 10, "Number_of_Owners": 1,
    "Age_as_of_Test": 2.5, "Usage_Rate": 8.0, "Liveline_Ratio": 0.6,
}

@pytest.fixture(scope="module")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c

def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

def test_predict_happy_path(client):
    r = client.post("/predict", json=VALID)
    assert r.status_code == 200 and r.json()["label"] in ("fail", "pass")

def test_predict_missing_field_422(client):
    bad = {k: v for k, v in VALID.items() if k != "Age_as_of_Test"}
    assert client.post("/predict", json=bad).status_code == 422

def test_predict_extra_key_422(client):
    assert client.post("/predict", json=dict(VALID, sabotage=1)).status_code == 422
