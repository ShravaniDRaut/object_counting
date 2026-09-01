"""
Database schema and persistence module for Object Counting System.
Tables:
- videos: video/source metadata and processing stats
- detections: frame-level bounding boxes and tracking IDs
- object_counts: line-crossing events with direction (IN/OUT) and timestamps
- analytics: session-level aggregated summary and throughput metrics
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, DateTime, ForeignKey, Index, Text, func, desc
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from src.config import cfg
from src.logger import logger

Base = declarative_base()


class Video(Base):
    """Metadata for processed video files or webcam streams."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(512), nullable=False)
    source_type = Column(String(50), default="video")  # video or webcam
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    total_frames = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    detections = relationship("Detection", back_populates="video", cascade="all, delete-orphan")
    counts = relationship("ObjectCount", back_populates="video", cascade="all, delete-orphan")
    analytics = relationship("AnalyticsSnapshot", back_populates="video", cascade="all, delete-orphan")


class Detection(Base):
    """Frame-by-frame object detections with tracking ID and bounding box."""
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    frame_idx = Column(Integer, nullable=False, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    x1 = Column(Float, nullable=False)
    y1 = Column(Float, nullable=False)
    x2 = Column(Float, nullable=False)
    y2 = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    video = relationship("Video", back_populates="detections")

    __table_args__ = (
        Index("ix_det_video_frame", "video_id", "frame_idx"),
    )


class ObjectCount(Base):
    """Unique line-crossing events with direction (IN/OUT)."""
    __tablename__ = "object_counts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    class_name = Column(String(50), nullable=False, index=True)
    direction = Column(String(20), nullable=False)  # IN or OUT
    crossing_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    video = relationship("Video", back_populates="counts")


class AnalyticsSnapshot(Base):
    """Aggregated session analytics and performance throughput."""
    __tablename__ = "analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    total_in = Column(Integer, default=0)
    total_out = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    person_count = Column(Integer, default=0)
    vehicle_count = Column(Integer, default=0)
    avg_fps = Column(Float, default=0.0)
    class_counts_json = Column(Text, default="{}")

    video = relationship("Video", back_populates="analytics")


class DatabaseManager:
    """Manages SQLite connection, sessions, and CRUD operations."""

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or cfg.DATABASE_URL
        connect_args = {"check_same_thread": False} if self.db_url.startswith("sqlite") else {}
        self.engine = create_engine(self.db_url, connect_args=connect_args, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_db()

    def init_db(self):
        """Create tables if they don't exist."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database initialized successfully.")

    def get_session(self) -> Session:
        return self.SessionLocal()

    def create_video_record(
        self,
        source: str,
        source_type: str = "video",
        duration: float = 0.0,
        width: int = 0,
        height: int = 0,
        fps: float = 0.0,
        total_frames: int = 0
    ) -> Video:
        session = self.get_session()
        try:
            video = Video(
                source=str(source),
                source_type=source_type,
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                total_frames=total_frames,
                created_at=datetime.now(timezone.utc)
            )
            session.add(video)
            session.commit()
            session.refresh(video)
            return video
        finally:
            session.close()

    def log_crossing(
        self,
        track_id: int,
        class_name: str,
        direction: str,
        video_id: Optional[int] = None,
        crossing_time: Optional[datetime] = None
    ) -> ObjectCount:
        session = self.get_session()
        try:
            entry = ObjectCount(
                video_id=video_id,
                track_id=track_id,
                class_name=class_name,
                direction=direction.upper(),
                crossing_time=crossing_time or datetime.now(timezone.utc)
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry
        finally:
            session.close()

    def save_analytics_snapshot(
        self,
        total_in: int,
        total_out: int,
        person_count: int,
        vehicle_count: int,
        avg_fps: float,
        video_id: Optional[int] = None,
        class_counts_json: str = "{}"
    ) -> AnalyticsSnapshot:
        session = self.get_session()
        try:
            snapshot = AnalyticsSnapshot(
                video_id=video_id,
                timestamp=datetime.now(timezone.utc),
                total_in=total_in,
                total_out=total_out,
                total_count=total_in + total_out,
                person_count=person_count,
                vehicle_count=vehicle_count,
                avg_fps=avg_fps,
                class_counts_json=class_counts_json
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)
            return snapshot
        finally:
            session.close()

    def get_all_crossings(self, video_id: Optional[int] = None) -> List[ObjectCount]:
        session = self.get_session()
        try:
            query = session.query(ObjectCount)
            if video_id is not None:
                query = query.filter(ObjectCount.video_id == video_id)
            return query.order_by(ObjectCount.crossing_time.desc()).all()
        finally:
            session.close()

    def get_summary_stats(self, video_id: Optional[int] = None) -> Dict[str, Any]:
        session = self.get_session()
        try:
            query = session.query(
                ObjectCount.class_name,
                ObjectCount.direction,
                func.count(ObjectCount.id).label("count")
            )
            if video_id is not None:
                query = query.filter(ObjectCount.video_id == video_id)

            results = query.group_by(ObjectCount.class_name, ObjectCount.direction).all()

            breakdown: Dict[str, Dict[str, int]] = {}
            total_in = 0
            total_out = 0

            for cls_name, direction, count in results:
                if cls_name not in breakdown:
                    breakdown[cls_name] = {"IN": 0, "OUT": 0, "TOTAL": 0}
                dir_key = direction.upper()
                breakdown[cls_name][dir_key] = count
                breakdown[cls_name]["TOTAL"] += count
                if dir_key == "IN":
                    total_in += count
                elif dir_key == "OUT":
                    total_out += count

            person_cnt = breakdown.get("person", {}).get("TOTAL", 0)
            veh_classes = ["car", "bus", "truck", "motorcycle", "bicycle"]
            veh_cnt = sum(breakdown.get(c, {}).get("TOTAL", 0) for c in veh_classes)

            return {
                "total_in": total_in,
                "total_out": total_out,
                "total_count": total_in + total_out,
                "person_count": person_cnt,
                "vehicle_count": veh_cnt,
                "class_breakdown": breakdown
            }
        finally:
            session.close()


db = DatabaseManager()
