"""Pydantic Schemas Package."""
from .payload import (
    VideoResponse,
    VideoUploadResponse,
    LineConfigPayload,
    StreamConfigPayload,
    StreamStatsResponse,
    ObjectCountRecord,
    AnalyticsSummaryResponse,
    DetectionRecord
)

__all__ = [
    "VideoResponse",
    "VideoUploadResponse",
    "LineConfigPayload",
    "StreamConfigPayload",
    "StreamStatsResponse",
    "ObjectCountRecord",
    "AnalyticsSummaryResponse",
    "DetectionRecord"
]
