"""
Analytics API routes.
Provides aggregated analytics, time-series data, and Plotly-ready visualization datasets.
"""
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from backend.database.connection import get_db
from backend.database import crud
from backend.schemas.payload import AnalyticsSummaryResponse, ObjectCountRecord
from backend.logger import logger

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def get_analytics_summary(
    video_id: Optional[int] = Query(None, description="Filter by video ID"),
    db: Session = Depends(get_db)
):
    """Retrieve cumulative count totals, class breakdown, and recent crossing events."""
    summary = crud.get_counts_summary(db=db, video_id=video_id)
    recent_counts = crud.get_recent_counts(db=db, video_id=video_id, limit=20)

    return {
        "total_in": summary["total_in"],
        "total_out": summary["total_out"],
        "total_count": summary["total_count"],
        "person_count": summary["person_count"],
        "vehicle_count": summary["vehicle_count"],
        "class_breakdown": summary["class_breakdown"],
        "recent_crossings": recent_counts
    }


@router.get("/plotly-data")
def get_plotly_chart_data(
    video_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns structured data for client-side Plotly rendering:
    1. Class distribution donut chart
    2. In vs Out directional bar chart
    3. Time-series crossing event density
    """
    summary = crud.get_counts_summary(db=db, video_id=video_id)
    class_breakdown = summary.get("class_breakdown", {})

    # 1. Donut Chart Data (Distribution by class)
    labels = []
    values = []
    for cls_name, data in class_breakdown.items():
        if data.get("TOTAL", 0) > 0:
            labels.append(cls_name.capitalize())
            values.append(data["TOTAL"])

    if not labels:
        labels = ["No Data Yet"]
        values = [1]

    donut_data = {
        "labels": labels,
        "values": values,
        "type": "pie",
        "hole": 0.55,
        "marker": {
            "colors": ["#00e5ff", "#00e676", "#ff9100", "#d500f9", "#ffd600", "#ff4081"]
        }
    }

    # 2. In vs Out Bar Chart Data
    bar_classes = list(class_breakdown.keys()) if class_breakdown else ["person", "car"]
    in_counts = [class_breakdown.get(c, {}).get("IN", 0) for c in bar_classes]
    out_counts = [class_breakdown.get(c, {}).get("OUT", 0) for c in bar_classes]

    bar_data = [
        {
            "x": [c.capitalize() for c in bar_classes],
            "y": in_counts,
            "name": "IN (Entering)",
            "type": "bar",
            "marker": {"color": "#00e676"}
        },
        {
            "x": [c.capitalize() for c in bar_classes],
            "y": out_counts,
            "name": "OUT (Exiting)",
            "type": "bar",
            "marker": {"color": "#ff5252"}
        }
    ]

    # 3. Time Series Activity
    recent_events = crud.get_all_counts_for_export(db=db, video_id=video_id)
    time_series = []
    if recent_events:
        # Group by 1-minute bins
        bins: Dict[str, int] = {}
        for ev in reversed(recent_events):
            t_str = ev.crossing_time.strftime("%H:%M")
            bins[t_str] = bins.get(t_str, 0) + 1
        time_series = [{"time": k, "count": v} for k, v in bins.items()]

    return {
        "donut": donut_data,
        "bar": bar_data,
        "time_series": time_series,
        "summary": summary
    }


@router.post("/clear")
def clear_analytics_history(
    video_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Clear historical counts and detections."""
    crud.clear_history_for_video(db=db, video_id=video_id)
    return {"status": "success", "message": "History cleared"}
