"""
Integration tests for FastAPI endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.connection import init_db

init_db()
client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_get_videos_list():
    response = client.get("/api/videos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_stream_stats():
    response = client.get("/api/stream/stats")
    assert response.status_code == 200
    data = response.json()
    assert "is_active" in data
    assert "total_count" in data


def test_analytics_summary():
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_in" in data
    assert "total_out" in data
    assert "class_breakdown" in data


def test_plotly_chart_data():
    response = client.get("/api/analytics/plotly-data")
    assert response.status_code == 200
    data = response.json()
    assert "donut" in data
    assert "bar" in data
    assert "time_series" in data


def test_export_reports_csv():
    response = client.get("/api/reports/export-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Event ID" in response.text
