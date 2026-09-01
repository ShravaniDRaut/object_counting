"""
Report export API routes.
Allows exporting counting events and summary analytics to CSV.
"""
import io
import csv
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.database import crud
from backend.logger import logger

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/export-csv")
def export_counting_events_csv(
    video_id: Optional[int] = Query(None, description="Filter by video ID"),
    db: Session = Depends(get_db)
):
    """
    Generate and download CSV report of all object crossing events.
    """
    records = crud.get_all_counts_for_export(db=db, video_id=video_id)

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Event ID",
        "Video ID",
        "Track ID",
        "Object Class",
        "Direction",
        "Line ID",
        "Crossing Timestamp (UTC)"
    ])

    for r in records:
        writer.writerow([
            r.id,
            r.video_id or "Live/Sample",
            r.track_id,
            r.class_name,
            r.direction,
            r.line_id,
            r.crossing_time.strftime("%Y-%m-%d %H:%M:%S") if r.crossing_time else ""
        ])

    output.seek(0)
    filename = f"object_counting_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export-summary-csv")
def export_summary_csv(
    video_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate and download CSV summary by object category.
    """
    summary = crud.get_counts_summary(db=db, video_id=video_id)
    class_breakdown = summary.get("class_breakdown", {})

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Category", "IN (Entering)", "OUT (Exiting)", "Total Count"])

    for cls_name, counts in class_breakdown.items():
        writer.writerow([
            cls_name.capitalize(),
            counts.get("IN", 0),
            counts.get("OUT", 0),
            counts.get("TOTAL", 0)
        ])

    # Totals Row
    writer.writerow([
        "GRAND TOTAL",
        summary["total_in"],
        summary["total_out"],
        summary["total_count"]
    ])

    output.seek(0)
    filename = f"object_counting_summary_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
