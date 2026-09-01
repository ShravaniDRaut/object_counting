"""
Tests for DatabaseManager, SQLAlchemy schema, and SQLite CRUD.
"""
import pytest
from src.database import DatabaseManager, Base

TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    manager = DatabaseManager(db_url=TEST_DB_URL)
    yield manager


def test_create_and_query_video(test_db):
    video = test_db.create_video_record(
        source="traffic.mp4",
        source_type="video",
        duration=15.0,
        width=1280,
        height=720,
        fps=30.0,
        total_frames=450
    )
    assert video.id is not None
    assert video.source == "traffic.mp4"
    assert video.fps == 30.0


def test_log_crossing_and_summary(test_db):
    test_db.log_crossing(track_id=1, class_name="car", direction="IN")
    test_db.log_crossing(track_id=2, class_name="car", direction="OUT")
    test_db.log_crossing(track_id=3, class_name="person", direction="IN")
    test_db.log_crossing(track_id=4, class_name="bus", direction="IN")

    crossings = test_db.get_all_crossings()
    assert len(crossings) == 4

    summary = test_db.get_summary_stats()
    assert summary["total_in"] == 3
    assert summary["total_out"] == 1
    assert summary["total_count"] == 4
    assert summary["person_count"] == 1
    assert summary["vehicle_count"] == 3
    assert "car" in summary["class_breakdown"]
    assert summary["class_breakdown"]["car"]["TOTAL"] == 2
