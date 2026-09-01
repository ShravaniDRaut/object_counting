"""
SQLAlchemy ORM models for the Object Counting System.
Tables:
- videos
- detections
- object_counts
- analytics
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Video(Base):
    """Stores metadata for uploaded and processed video streams."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(512), nullable=False)
    source_type = Column(String(50), default="upload")  # upload, webcam, rtsp
    duration = Column(Float, default=0.0)  # in seconds
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    total_frames = Column(Integer, default=0)
    status = Column(String(50), default="ready")  # ready, processing, completed, error
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    counts = relationship("ObjectCount", back_populates="video", cascade="all, delete-orphan")
    analytics = relationship("AnalyticsSnapshot", back_populates="video", cascade="all, delete-orphan")


class Detection(Base):
    """Stores frame-by-frame object detection and tracking records."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    frame_number = Column(Integer, nullable=False, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    bbox_x1 = Column(Float, nullable=False)
    bbox_y1 = Column(Float, nullable=False)
    bbox_x2 = Column(Float, nullable=False)
    bbox_y2 = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    video = relationship("Video", back_populates="detections")

    __table_args__ = (
        Index("ix_detections_video_frame", "video_id", "frame_number"),
    )


class ObjectCount(Base):
    """Stores unique line-crossing counting events."""
    __tablename__ = "object_counts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(50), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # IN or OUT
    line_id = Column(String(50), default="primary_line")
    crossing_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    video = relationship("Video", back_populates="counts")

    __table_args__ = (
        Index("ix_counts_video_track", "video_id", "track_id"),
    )


class AnalyticsSnapshot(Base):
    """Stores aggregate snapshots and metrics over time for visualization."""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    person_count = Column(Integer, default=0)
    vehicle_count = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    avg_confidence = Column(Float, default=0.0)
    details_json = Column(Text, default="{}")  # Extra metadata/category breakdown json

    video = relationship("Video", back_populates="analytics")
