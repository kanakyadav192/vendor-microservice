import json
import tempfile
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.db import get_session as real_get_session
from app import models

# Use a temporary sqlite file for integration testing
@pytest.fixture(scope="function")
def client():
    # create a temp sqlite database file
    db_file = tempfile.NamedTemporaryFile(suffix=".db")
    db_url = f"sqlite:///{db_file.name}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # create tables
    SQLModel.metadata.create_all(engine)

    # dependency override to use this test engine/session
    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[real_get_session] = override_get_session
    client = TestClient(app)
    yield client
    # cleanup
    app.dependency_overrides.pop(real_get_session, None)
    db_file.close()


def test_create_vendor_and_post_metric(client):
    # 1) create vendor
    r = client.post("/vendors", json={"name": "Test Vendor", "category": "supplier"})
    assert r.status_code == 200
    vendor = r.json()
    vid = vendor["id"]

    # 2) post metric
    payload = {
        "timestamp": "2025-11-24T10:00:00Z",
        "on_time_delivery_rate": 92.5,
        "complaint_count": 1,
        "missing_documents": False,
        "compliance_score": 85.0
    }
    r2 = client.post(f"/vendors/{vid}/metrics", json=payload)
    assert r2.status_code == 200
    resp = r2.json()
    assert resp["vendor_id"] == vid
    assert resp["metric_id"] is not None
    # score should be present (float)
    assert "score" in resp
    assert isinstance(resp["score"], (int, float))

    # 3) get vendor + latest score
    r3 = client.get(f"/vendors/{vid}")
    assert r3.status_code == 200
    j = r3.json()
    assert j["id"] == vid
    assert j["latest_score"] is not None

def test_score_history_endpoint(client):
    r = client.post("/vendors", json={"name": "Hist Vendor", "category": "dealer"})
    vid = r.json()["id"]
    payload = {
        "timestamp": "2025-11-24T10:00:00Z",
        "on_time_delivery_rate": 50.0,
        "complaint_count": 2,
        "missing_documents": False,
        "compliance_score": 50.0
    }
    client.post(f"/vendors/{vid}/metrics", json=payload)
    res = client.get(f"/vendors/{vid}/scores")
    assert res.status_code == 200
    arr = res.json()
    assert isinstance(arr, list)
