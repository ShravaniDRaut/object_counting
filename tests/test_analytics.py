"""
Tests for Plotly Visual Analytics dashboard generation.
"""
from pathlib import Path
from src.database import db
from src.analytics import generate_analytics_dashboard


def test_generate_analytics_dashboard(tmp_path):
    db.log_crossing(track_id=10, class_name="car", direction="IN")
    db.log_crossing(track_id=11, class_name="truck", direction="OUT")

    out_html = tmp_path / "test_dashboard.html"
    res = generate_analytics_dashboard(output_html=out_html, open_in_browser=False)

    assert res.exists()
    content = res.read_text(encoding="utf-8")
    assert "plotly" in content.lower()
    assert "Object Category Distribution" in content
    assert "Directional Flow (IN vs OUT)" in content
