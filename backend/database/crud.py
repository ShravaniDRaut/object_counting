"""
Database CRUD operations for videos, detections, counts, and analytics.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from backend.database.models import Video, Detection, ObjectCount, AnalyticsSnapshot
from backend.logger import logger


# Video CRUD
def create_video(
    db: Session,
    filename: str,
    filepath: str,
    source_type: str = "upload",
    duration: float = 0.0,
    width: int = 0,
    height: int = 0,
    fps: float = 0.0,
    total_frames: int = 0,
    status: str = "ready"
) -> Video:
    video = Video(
        filename=filename,
        filepath=filepath,
        source_type=source_type,
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        total_frames=total_frames,
        status=status,
        created_at=datetime.now(timezone.utc)
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    return video


def get_video_by_id(db: Session, video_id: int) -> Optional[Video]:
    return db.query(Video).filter(Video.id == video_id).first()


def get_all_videos(db: Session, skip: int = 0, limit: int = 100) -> List[Video]:
    return db.query(Video).order_by(desc(Video.created_at)).offset(skip).limit(limit).all()


def update_video_status(db: Session, video_id: int, status: str) -> Optional[Video]:
    video = get_video_by_id(db, video_id)
    if video:
        video.status = status
        db.commit()
        db.refresh(video)
    return video


def delete_video(db: Session, video_id: int) -> bool:
    video = get_video_by_id(db, video_id)
    if video:
        db.delete(video)
        db.commit()
        return True
    return False


# Detection CRUD
def create_detection(
    db: Session,
    video_id: Optional[int],
    frame_number: int,
    track_id: int,
    class_name: str,
    confidence: float,
    bbox_x1: float,
    bbox_y1: float,
    bbox_x2: float,
    bbox_y2: float,
    timestamp: Optional[datetime] = None
) -> Detection:
    det = Detection(
        video_id=video_id,
        frame_number=frame_number,
        track_id=track_id,
        class_name=class_name,
        confidence=confidence,
        bbox_x1=bbox_x1,
        bbox_y1=bbox_y1,
        bbox_x2=bbox_x2,
        bbox_y2=bbox_y2,
        timestamp=timestamp or datetime.now(timezone.utc)
    )
    db.add(det)
    db.commit()
    db.refresh(det)
    return det


def bulk_create_detections(db: Session, detections_data: List[dict]) -> None:
    if not detections_data:
        return
    db.bulk_insert_mappings(Detection, detections_data)
    db.commit()


# Object Count CRUD
def record_count(
    db: Session,
    track_id: int,
    class_name: str,
    direction: str,
    video_id: Optional[int] = None,
    line_id: str = "primary_line",
    crossing_time: Optional[datetime] = None
) -> ObjectCount:
    count_entry = ObjectCount(
        video_id=video_id,
        track_id=track_id,
        class_name=class_name,
        direction=direction.upper(),
        line_id=line_id,
        crossing_time=crossing_time or datetime.now(timezone.utc)
    )
    db.add(count_entry)
    db.commit()
    db.refresh(count_entry)
    return count_entry


def get_recent_counts(db: Session, video_id: Optional[int] = None, limit: int = 50) -> List[ObjectCount]:
    query = db.query(ObjectCount)
    if video_id:
        query = query.filter(ObjectCount.video_id == video_id)
    return query.order_by(desc(ObjectCount.crossing_time)).limit(limit).all()


def get_counts_summary(db: Session, video_id: Optional[int] = None) -> Dict[str, Any]:
    """Returns aggregated count statistics by class and direction."""
    query = db.query(
        ObjectCount.class_name,
        ObjectCount.direction,
        func.count(ObjectCount.id).label("count")
    )
    if video_id:
        query = query.filter(ObjectCount.video_id == video_id)

    results = query.group_by(ObjectCount.class_name, ObjectCount.direction).all()

    class_counts: Dict[str, Dict[str, int]] = {}
    total_in = 0
    total_out = 0

    for class_name, direction, cnt in results:
        if class_name not in class_counts:
            class_counts[class_name] = {"IN": 0, "OUT": 0, "TOTAL": 0}
        dir_key = direction.upper()
        class_counts[class_name][dir_key] = cnt
        class_counts[class_name]["TOTAL"] += cnt
        if dir_key == "IN":
            total_in += cnt
        elif dir_key == "OUT":
            total_out += cnt

    total_count = total_in + total_out
    person_count = class_counts.get("person", {}).get("TOTAL", 0)
    vehicle_classes = ["car", "bus", "truck", "motorcycle", "bicycle"]
    vehicle_count = sum(class_counts.get(cls, {}).get("TOTAL", 0) for cls in vehicle_classes)

    return {
        "total_in": total_in,
        "total_out": total_out,
        "total_count": total_count,
        "person_count": person_count,
        "vehicle_count": vehicle_count,
        "class_breakdown": class_counts
    }


# Analytics Snapshot CRUD
def record_analytics_snapshot(
    db: Session,
    total_in: int,
    total_out: int,
    person_count: int,
    vehicle_count: int,
    fps: float,
    avg_confidence: float = 0.0,
    video_id: Optional[int] = None,
    details_json: str = "{}"
) -> AnalyticsSnapshot:
    snapshot = AnalyticsSnapshot(
        video_id=video_id,
        timestamp=datetime.now(timezone.utc),
        total_in=total_in,
        total_out=total_out,
        total_count=total_in + total_out,
        person_count=person_count,
        vehicle_count=vehicle_count,
        fps=fps,
        avg_confidence=avg_confidence,
        details_json=details_json
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_analytics_timeline(db: Session, video_id: Optional[int] = None, limit: int = 100) -> List[AnalyticsSnapshot]:
    query = db.query(AnalyticsSnapshot)
    if video_id:
        query = query.filter(AnalyticsSnapshot.video_id == video_id)
    return query.order_by(AnalyticsSnapshot.timestamp.asc()).limit(limit).all()


def get_all_counts_for_export(db: Session, video_id: Optional[int] = None) -> List[ObjectCount]:
    query = db.query(ObjectCount)
    if video_id:
        query = query.filter(ObjectCount.video_id == video_id)
    return query.order_by(ObjectCount.crossing_time.desc()).all()


def clear_history_for_video(db: Session, video_id: Optional[int] = None) -> None:
    """Clear detections and counting events, optionally for a specific video or all."""
    if video_id is not None:
        db.query(ObjectCount).filter(ObjectCount.video_id == video_id).delete()
        db.query(Detection).filter(Detection.video_id == video_id).delete()
        db.query(AnalyticsSnapshot).filter(AnalyticsSnapshot.video_id == video_id).delete()
    else:
        db.query(ObjectCount).delete()
        db.query(Detection).delete()
        db.query(AnalyticsSnapshot).delete()
    db.commit()
