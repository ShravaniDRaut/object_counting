"""
Tests for SQLAlchemy database schema, relationships, and CRUD logic.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Video, Detection, ObjectCount
from backend.database import crud

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_create_and_query_video(db_session):
    video = crud.create_video(
        db=db_session,
        filename="test_video.mp4",
        filepath="/tmp/test_video.mp4",
        source_type="upload",
        duration=12.5,
        width=1280,
        height=720,
        fps=30.0
    )
    assert video.id is not None
    assert video.filename == "test_video.mp4"

    fetched = crud.get_video_by_id(db_session, video.id)
    assert fetched is not None
    assert fetched.fps == 30.0


def test_record_counts_and_summary(db_session):
    # Record crossings
    crud.record_count(db=db_session, track_id=1, class_name="car", direction="IN")
    crud.record_count(db=db_session, track_id=2, class_name="car", direction="OUT")
    crud.record_count(db=db_session, track_id=3, class_name="person", direction="IN")
    crud.record_count(db=db_session, track_id=4, class_name="bus", direction="IN")

    summary = crud.get_counts_summary(db=db_session)
    assert summary["total_in"] == 3
    assert summary["total_out"] == 1
    assert summary["total_count"] == 4
    assert summary["person_count"] == 1
    assert summary["vehicle_count"] == 3
    assert "car" in summary["class_breakdown"]
    assert summary["class_breakdown"]["car"]["TOTAL"] == 2
