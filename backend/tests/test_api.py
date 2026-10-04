import io
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Resolve path relative to this file so tests work from any working directory
SAMPLE_CSN_PATH = Path(__file__).parent.parent.parent / "sample_data" / "sample_csn.json"
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_upload_csn_api():
    with open(SAMPLE_CSN_PATH, "rb") as f:
        file_content = f.read()

    response = client.post(
        "/api/upload",
        files={"file": ("sample_csn.json", io.BytesIO(file_content), "application/json")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data
    assert data["object_count"] > 0
    assert data["relationship_count"] > 0


def test_load_sample_api():
    response = client.post("/api/load-sample")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    session_id = data["session_id"]

    # Test GET metadata
    meta_resp = client.get(f"/api/metadata/{session_id}")
    assert meta_resp.status_code == 200
    meta_data = meta_resp.json()
    assert meta_data["object_count"] == data["object_count"]

    # Test GET objects
    objs_resp = client.get(f"/api/objects/{session_id}")
    assert objs_resp.status_code == 200
    objs = objs_resp.json()
    assert len(objs) == data["object_count"]

    # Test GET specific object
    obj_resp = client.get(f"/api/object/{session_id}/Current_Month_OI_Analytic_Model")
    assert obj_resp.status_code == 200
    obj_data = obj_resp.json()
    assert obj_data["name"] == "Current_Month_OI_Analytic_Model"
    assert obj_data["modeling_pattern"] == "ANALYTICAL_CUBE"

    # Test GET lineage
    lin_resp = client.get(f"/api/lineage/{session_id}/Current_Month_OI_Analytic_Model")
    assert lin_resp.status_code == 200
    lin_data = lin_resp.json()
    assert "Current_Month_OI_Heirarchy" in lin_data["upstream"]
    assert len(lin_data["nodes"]) > 0
    assert len(lin_data["edges"]) > 0

    # Test GET impact
    imp_resp = client.get(f"/api/impact/{session_id}/Time_table_heirarchy")
    assert imp_resp.status_code == 200
    imp_data = imp_resp.json()
    assert "Current_Month_OI_Analytic_Model" in imp_data["downstream_dependents"]

    # Test Chat
    chat_resp = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "What is the lineage of Current_Month_OI_Analytic_Model?"},
    )
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert "get_lineage" in chat_data["tools_used"]


def test_invalid_upload_format():
    response = client.post(
        "/api/upload",
        files={"file": ("test.txt", io.BytesIO(b"not json"), "text/plain")},
    )
    assert response.status_code == 400


def test_unknown_session_not_found():
    response = client.get("/api/metadata/non-existent-session-id")
    assert response.status_code == 404


def test_chat_unknown_object_reports_missing_metadata():
    response = client.post("/api/load-sample")
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    chat_resp = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "What is the lineage of XYZ_NON_EXISTENT?",
        },
    )

    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert chat_data["tools_used"] == ["get_lineage"]
    assert "not found" in chat_data["answer"].lower()
