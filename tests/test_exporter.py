"""
Tests for CSV Report Exporter module.
"""
from pathlib import Path
import pandas as pd
from src.database import db
from src.exporter import export_events_csv, export_summary_csv


def test_export_events_csv(tmp_path):
    # Log a test crossing
    db.log_crossing(track_id=99, class_name="motorcycle", direction="IN")

    out_file = tmp_path / "test_events.csv"
    res = export_events_csv(output_path=out_file)
    assert res.exists()

    df = pd.read_csv(res)
    assert "Event ID" in df.columns
    assert "Object Class" in df.columns
    assert "Direction" in df.columns
    assert len(df) > 0


def test_export_summary_csv(tmp_path):
    out_file = tmp_path / "test_summary.csv"
    res = export_summary_csv(output_path=out_file)
    assert res.exists()

    df = pd.read_csv(res)
    assert "Category" in df.columns
    assert "Total Count" in df.columns
    assert "GRAND TOTAL" in df["Category"].values
