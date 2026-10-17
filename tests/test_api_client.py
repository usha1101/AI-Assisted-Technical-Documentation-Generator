import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root_redirect(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert response.headers.get("location") == "/docs"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "generator_type" in data
    assert "device" in data


def test_generate_docs_simple_function(client):
    sample_code = """
def multiply(x: int, y: int) -> int:
    return x * y
"""
    response = client.post("/generate-docs", json={
        "source_code": sample_code,
        "style": "google"
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    item = data["results"][0]
    assert item["entity_name"] == "multiply"
    assert item["entity_type"] == "function"
    assert len(item["generated_docstring"]) > 0
    assert "Args:" in item["generated_docstring"]


def test_generate_documented_file(client):
    sample_code = """def subtract(a: int, b: int) -> int:
    return a - b
"""
    response = client.post("/generate-documented-file", json={
        "source_code": sample_code,
        "style": "google"
    })
    assert response.status_code == 200
    data = response.json()
    assert "documented_code" in data
    assert "def subtract" in data["documented_code"]
    assert '"""' in data["documented_code"]


def test_export_markdown(client):
    sample_code = "def sample_func(): pass"
    response = client.post("/export-markdown", json={"source_code": sample_code})
    assert response.status_code == 200
    assert "# Technical Documentation" in response.text
    assert "sample_func" in response.text


def test_generate_docs_empty_code(client):
    response = client.post("/generate-docs", json={"source_code": "   "})
    assert response.status_code == 400


def test_history_endpoint(client):
    session_id = "test-session-456"
    client.post("/generate-docs", json={
        "source_code": "def ping(): pass",
        "session_id": session_id,
        "save_history": True
    })

    hist_response = client.get(f"/history/{session_id}")
    assert hist_response.status_code == 200
    history_items = hist_response.json()
    assert len(history_items) >= 1
    assert history_items[0]["session_id"] == session_id
