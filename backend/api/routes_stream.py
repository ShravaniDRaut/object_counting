"""
Real-time Video Streaming and Inference API routes.
Provides MJPEG streaming feed, live statistics, dynamic line configuration, and stream controls.
"""
import time
import threading
from typing import Optional, Dict, Any
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.connection import SessionLocal, get_db
from backend.database import crud
from backend.ml.pipeline import VisionPipeline
from backend.utils.video_utils import VideoStreamSource
from backend.utils.sample_generator import generate_sample_traffic_video
from backend.schemas.payload import (
    StreamConfigPayload,
    LineConfigPayload,
    StreamStatsResponse
)
from backend.logger import logger

router = APIRouter(prefix="/api/stream", tags=["Streaming"])


class StreamManager:
    """Singleton-style manager controlling real-time video capture and ML pipeline."""

    def __init__(self):
        self.lock = threading.Lock()
        self.is_active = False
        self.source_type = "sample"
        self.video_id: Optional[int] = None
        self.source: Optional[VideoStreamSource] = None
        self.pipeline: Optional[VisionPipeline] = None
        self.latest_stats: Dict[str, Any] = {
            "is_active": False,
            "source_type": self.source_type,
            "fps": 0.0,
            "current_frame": 0,
            "total_in": 0,
            "total_out": 0,
            "total_count": 0,
            "person_count": 0,
            "vehicle_count": 0,
            "active_tracks_count": 0,
            "class_counts": {},
            "recent_events": [],
            "confidence_threshold": settings.CONFIDENCE_THRESHOLD
        }

    def start(
        self,
        source_type: str = "sample",
        video_id: Optional[int] = None,
        webcam_idx: int = 0,
        confidence: float = 0.35,
        iou: float = 0.45,
        line_config: Optional[LineConfigPayload] = None
    ):
        with self.lock:
            # Stop existing stream if running
            if self.source:
                self.source.release()
                self.source = None

            self.source_type = source_type
            self.video_id = video_id

            # Determine source path
            if source_type == "webcam":
                source_input = webcam_idx
            elif source_type == "upload" and video_id is not None:
                db = SessionLocal()
                try:
                    v = crud.get_video_by_id(db, video_id)
                    if not v or not Path(v.filepath).exists():
                        raise ValueError("Selected video file does not exist")
                    source_input = v.filepath
                finally:
                    db.close()
            else:
                # Default to sample video
                sample_path = settings.SAMPLE_DIR / "sample_traffic.mp4"
                if not sample_path.exists():
                    generate_sample_traffic_video(sample_path)
                source_input = str(sample_path)
                self.source_type = "sample"

            self.source = VideoStreamSource(source_input, loop=True)

            # Initialize Vision Pipeline
            line_start = (line_config.line_start_x, line_config.line_start_y) if line_config else (settings.LINE_START_X, settings.LINE_START_Y)
            line_end = (line_config.line_end_x, line_config.line_end_y) if line_config else (settings.LINE_END_X, settings.LINE_END_Y)
            direction_mode = line_config.direction_mode if line_config else "bidirectional"

            self.pipeline = VisionPipeline(
                line_start=line_start,
                line_end=line_end,
                direction_mode=direction_mode,
                confidence_threshold=confidence,
                iou_threshold=iou
            )

            self.is_active = True
            logger.info(f"Streaming started with source: {source_type} ({source_input})")

    def stop(self):
        with self.lock:
            self.is_active = False
            if self.source:
                self.source.release()
                self.source = None
            if self.pipeline:
                self.pipeline.reset()
            self.latest_stats["is_active"] = False
            logger.info("Streaming stopped.")

    def on_crossing_event(self, event: dict):
        """Callback executed when an object crosses the virtual line."""
        # Persist event asynchronously to database
        def _save():
            db = SessionLocal()
            try:
                crud.record_count(
                    db=db,
                    track_id=event["track_id"],
                    class_name=event["class_name"],
                    direction=event["direction"],
                    video_id=self.video_id
                )
            except Exception as e:
                logger.error(f"Failed to record count in DB: {e}")
            finally:
                db.close()

        threading.Thread(target=_save, daemon=True).start()

    def generate_frames(self):
        """Generator yielding MJPEG frame stream."""
        while self.is_active and self.source:
            frame = self.source.read_frame()
            if frame is None:
                time.sleep(0.03)
                continue

            # Run inference & line crossing
            annotated_frame, stats = self.pipeline.process_frame(
                frame,
                on_crossing_callback=self.on_crossing_event
            )

            # Update latest stats
            class_counts = stats["class_counts"]
            person_cnt = class_counts.get("person", {}).get("TOTAL", 0)
            veh_classes = ["car", "bus", "truck", "motorcycle", "bicycle"]
            vehicle_cnt = sum(class_counts.get(c, {}).get("TOTAL", 0) for c in veh_classes)

            self.latest_stats = {
                "is_active": True,
                "source_type": self.source_type,
                "fps": stats["fps"],
                "current_frame": stats["frame_idx"],
                "total_in": stats["total_in"],
                "total_out": stats["total_out"],
                "total_count": stats["total_count"],
                "person_count": person_cnt,
                "vehicle_count": vehicle_cnt,
                "active_tracks_count": stats["active_tracks"],
                "class_counts": class_counts,
                "recent_events": stats["recent_events"],
                "confidence_threshold": self.pipeline.tracker.conf
            }

            # Encode as JPEG
            ret, buffer = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue

            frame_bytes = buffer.tobytes()
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")

            # Regulate frame rate to prevent CPU flooding (cap ~30 FPS)
            time.sleep(0.015)


# Global stream manager instance
stream_manager = StreamManager()


@router.post("/start")
def start_stream(config: StreamConfigPayload):
    """Start streaming and object counting with specified configuration."""
    try:
        stream_manager.start(
            source_type=config.source_type,
            video_id=config.video_id,
            webcam_idx=config.webcam_index,
            confidence=config.confidence_threshold,
            iou=config.iou_threshold,
            line_config=config.line_config
        )
        return {"status": "success", "message": f"Stream started for {config.source_type}"}
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/stop")
def stop_stream():
    """Stop active video stream."""
    stream_manager.stop()
    return {"status": "success", "message": "Stream stopped"}


@router.get("/feed")
def video_feed():
    """MJPEG live video stream feed."""
    if not stream_manager.is_active or stream_manager.source is None:
        # Auto-start with sample video if not currently running
        stream_manager.start(source_type="sample")

    return StreamingResponse(
        stream_manager.generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.get("/stats", response_model=StreamStatsResponse)
def get_stream_stats():
    """Get current live inference and counting statistics."""
    return stream_manager.latest_stats


@router.post("/line-config")
def update_line_configuration(config: LineConfigPayload):
    """Dynamically adjust counting line position in real-time."""
    if stream_manager.pipeline:
        stream_manager.pipeline.set_line_coordinates(
            (config.line_start_x, config.line_start_y),
            (config.line_end_x, config.line_end_y)
        )
        stream_manager.pipeline.counter.direction_mode = config.direction_mode
        return {"status": "success", "message": "Line configuration updated"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not active")


@router.post("/confidence")
def update_confidence(conf: float = Query(..., ge=0.05, le=1.0)):
    """Update detection confidence threshold in real-time."""
    if stream_manager.pipeline:
        stream_manager.pipeline.set_confidence(conf)
        return {"status": "success", "confidence": conf}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not active")


@router.post("/reset-counts")
def reset_counts():
    """Reset the current stream count registers."""
    if stream_manager.pipeline:
        stream_manager.pipeline.counter.reset_counts()
        return {"status": "success", "message": "Counts reset"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not active")


@router.post("/toggle")
def toggle_visuals(
    boxes: Optional[bool] = None,
    trails: Optional[bool] = None,
    line: Optional[bool] = None,
    hud: Optional[bool] = None
):
    """Toggle visual overlay elements."""
    if stream_manager.pipeline:
        if boxes is not None:
            stream_manager.pipeline.show_boxes = boxes
        if trails is not None:
            stream_manager.pipeline.show_trails = trails
        if line is not None:
            stream_manager.pipeline.show_line = line
        if hud is not None:
            stream_manager.pipeline.show_hud = hud
        return {"status": "success", "message": "Visual overlays updated"}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stream is not active")
