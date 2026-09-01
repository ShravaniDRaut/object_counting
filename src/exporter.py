"""
CSV Report Exporter module.
Exports object crossing audit events and categorized traffic summaries to CSV files.
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
import csv
import pandas as pd

from src.config import cfg
from src.database import db
from src.logger import logger


def export_events_csv(output_path: Optional[Path] = None, video_id: Optional[int] = None) -> Path:
    """Exports all line-crossing events to a CSV file."""
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = cfg.EXPORT_DIR / f"crossing_events_{ts}.csv"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = db.get_all_crossings(video_id=video_id)

    with open(output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Event ID",
            "Video ID",
            "Track ID",
            "Object Class",
            "Direction",
            "Timestamp (UTC)"
        ])

        for r in records:
            writer.writerow([
                r.id,
                r.video_id or "Live/Webcam",
                r.track_id,
                r.class_name,
                r.direction,
                r.crossing_time.strftime("%Y-%m-%d %H:%M:%S") if r.crossing_time else ""
            ])

    logger.info(f"Exported {len(records)} events to CSV: {output_path}")
    return output_path


def export_summary_csv(output_path: Optional[Path] = None, video_id: Optional[int] = None) -> Path:
    """Exports categorized count summaries to a CSV file."""
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = cfg.EXPORT_DIR / f"counting_summary_{ts}.csv"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = db.get_summary_stats(video_id=video_id)
    breakdown = summary.get("class_breakdown", {})

    rows = []
    for cls_name, data in breakdown.items():
        rows.append({
            "Category": cls_name.capitalize(),
            "IN (Entering)": data.get("IN", 0),
            "OUT (Exiting)": data.get("OUT", 0),
            "Total Count": data.get("TOTAL", 0)
        })

    # Summary grand total row
    rows.append({
        "Category": "GRAND TOTAL",
        "IN (Entering)": summary["total_in"],
        "OUT (Exiting)": summary["total_out"],
        "Total Count": summary["total_count"]
    })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(f"Exported summary report to CSV: {output_path}")
    return output_path
