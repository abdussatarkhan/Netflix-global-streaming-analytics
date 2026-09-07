"""
Unit & Integration tests for FastAPI REST Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient with active lifespan context."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint(client):
    """Test GET /health returns operational status and database metrics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["operational", "degraded"]
    assert "database" in data
    assert "embedder_model" in data
    assert "timestamp" in data


def test_analytics_summary_endpoint(client):
    """Test GET /analytics/summary returns catalog and telemetry aggregations."""
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_titles" in data
    assert "content_type_distribution" in data
    assert "top_countries" in data
    assert "top_genres" in data
    assert isinstance(data["content_type_distribution"], list)


def test_semantic_recommendation_endpoint(client):
    """Test POST /recommendations/semantic returns ranked items for a prompt."""
    payload = {
        "query": "supernatural mystery involving missing child and dark experiments",
        "top_k": 3
    }
    response = client.post("/recommendations/semantic", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["top_k"] == 3
    assert len(data["recommendations"]) <= 3
    if data["recommendations"]:
        first_rec = data["recommendations"][0]
        assert "title" in first_rec
        assert "score" in first_rec
        assert "match_reason" in first_rec


def test_user_recommendation_endpoint_cold_start(client):
    """Test GET /recommendations/user/{user_id} handles non-existent cold users."""
    response = client.get("/recommendations/user/unknown_user_99999?top_k=4")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "new_user"
    assert data["strategy"] == "cold_start_popularity_diversity"
    assert data["user_consumed_count"] == 0
    assert len(data["recommendations"]) == 4


def test_simulate_stream_endpoint(client):
    """Test POST /pipeline/simulate-stream ingests clickstream telemetry events."""
    payload = {
        "events": [
            {
                "user_id": "test_user_qa",
                "show_id": "s1",
                "interaction_type": "watch",
                "watch_duration_pct": 95.0
            },
            {
                "user_id": "test_user_qa",
                "show_id": "s1",
                "interaction_type": "like",
                "watch_duration_pct": 100.0
            }
        ]
    }
    response = client.post("/pipeline/simulate-stream", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["ingested_events"] == 2
