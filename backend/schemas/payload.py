"""
Pydantic schema definitions for API requests, responses, and stream controls.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# Video Schemas
class VideoResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    source_type: str
    duration: float
    width: int
    height: int
    fps: float
    total_frames: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoUploadResponse(BaseModel):
    message: str
    video: VideoResponse


# Stream & Line Configuration Schemas
class LineConfigPayload(BaseModel):
    line_start_x: float = Field(0.1, ge=0.0, le=1.0, description="Normalized X start (0.0 to 1.0)")
    line_start_y: float = Field(0.5, ge=0.0, le=1.0, description="Normalized Y start (0.0 to 1.0)")
    line_end_x: float = Field(0.9, ge=0.0, le=1.0, description="Normalized X end (0.0 to 1.0)")
    line_end_y: float = Field(0.5, ge=0.0, le=1.0, description="Normalized Y end (0.0 to 1.0)")
    direction_mode: str = Field("bidirectional", description="bidirectional, in_only, or out_only")


class StreamConfigPayload(BaseModel):
    source_type: str = Field("sample", description="'sample', 'upload', or 'webcam'")
    video_id: Optional[int] = None
    webcam_index: int = 0
    confidence_threshold: float = Field(0.35, ge=0.05, le=1.0)
    iou_threshold: float = Field(0.45, ge=0.1, le=1.0)
    line_config: Optional[LineConfigPayload] = None
    target_classes: Optional[List[int]] = None


# Detection & Count Schemas
class DetectionRecord(BaseModel):
    track_id: int
    class_name: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class ObjectCountRecord(BaseModel):
    id: int
    track_id: int
    class_name: str
    direction: str
    crossing_time: datetime
    video_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# Stream Live Stats Schema
class StreamStatsResponse(BaseModel):
    is_active: bool
    source_type: str
    fps: float
    current_frame: int
    total_in: int
    total_out: int
    total_count: int
    person_count: int
    vehicle_count: int
    active_tracks_count: int
    class_counts: Dict[str, Dict[str, int]]
    recent_events: List[Dict[str, Any]]
    confidence_threshold: float


# Analytics Schemas
class AnalyticsSummaryResponse(BaseModel):
    total_in: int
    total_out: int
    total_count: int
    person_count: int
    vehicle_count: int
    class_breakdown: Dict[str, Dict[str, int]]
    recent_crossings: List[ObjectCountRecord]


class TimeSeriesDataPoint(BaseModel):
    timestamp: str
    total_in: int
    total_out: int
    person_count: int
    vehicle_count: int
    fps: float


class AnalyticsTimeSeriesResponse(BaseModel):
    data_points: List[TimeSeriesDataPoint]
