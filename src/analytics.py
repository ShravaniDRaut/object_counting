"""
Plotly Visual Analytics module.
Generates an interactive, standalone HTML analytics dashboard from SQLite counting records.
"""
from pathlib import Path
from typing import Optional
import webbrowser
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.config import cfg
from src.database import db
from src.logger import logger


def generate_analytics_dashboard(
    output_html: Optional[Path] = None,
    video_id: Optional[int] = None,
    open_in_browser: bool = False
) -> Path:
    """
    Generates a rich interactive Plotly analytics dashboard and writes to an HTML file.
    """
    if output_html is None:
        output_html = cfg.EXPORT_DIR / "analytics_dashboard.html"

    output_html = Path(output_html)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    summary = db.get_summary_stats(video_id=video_id)
    records = db.get_all_crossings(video_id=video_id)

    # 1. Donut Chart - Class Distribution
    breakdown = summary.get("class_breakdown", {})
    categories = []
    total_vals = []
    for c, d in breakdown.items():
        if d["TOTAL"] > 0:
            categories.append(c.capitalize())
            total_vals.append(d["TOTAL"])

    if not categories:
        categories = ["No Activity Recorded"]
        total_vals = [1]

    # 2. Bar Chart - IN vs OUT
    bar_cats = list(breakdown.keys()) if breakdown else ["Person", "Car"]
    in_vals = [breakdown.get(c, {}).get("IN", 0) for c in bar_cats]
    out_vals = [breakdown.get(c, {}).get("OUT", 0) for c in bar_cats]

    # 3. Time Series Activity
    time_bins = {}
    for r in records:
        t_str = r.crossing_time.strftime("%H:%M")
        time_bins[t_str] = time_bins.get(t_str, 0) + 1
    sorted_times = sorted(time_bins.keys())
    counts_per_min = [time_bins[t] for t in sorted_times]

    # Create Subplot Grid
    fig = make_subplots(
        rows=2, cols=2,
        column_widths=[0.45, 0.55],
        row_heights=[0.5, 0.5],
        specs=[
            [{"type": "domain"}, {"type": "xy"}],
            [{"colspan": 2, "type": "xy"}, None]
        ],
        subplot_titles=(
            "Object Category Distribution",
            "Directional Flow (IN vs OUT)",
            "Crossing Activity Over Time"
        )
    )

    # Add Donut Chart
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=total_vals,
            hole=0.55,
            marker_colors=["#00e5ff", "#00e676", "#ff9100", "#d500f9", "#ffd600", "#ff4081"],
            textinfo="label+percent"
        ),
        row=1, col=1
    )

    # Add Bar Chart
    fig.add_trace(
        go.Bar(
            name="IN (Entering)",
            x=[c.capitalize() for c in bar_cats],
            y=in_vals,
            marker_color="#00e676"
        ),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(
            name="OUT (Exiting)",
            x=[c.capitalize() for c in bar_cats],
            y=out_vals,
            marker_color="#ff5252"
        ),
        row=1, col=2
    )

    # Add Time-Series Line
    fig.add_trace(
        go.Scatter(
            x=sorted_times if sorted_times else ["00:00"],
            y=counts_per_min if counts_per_min else [0],
            mode="lines+markers",
            name="Crossings / Min",
            line=dict(color="#6366f1", width=3, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(99, 102, 241, 0.15)"
        ),
        row=2, col=1
    )

    # Styling for modern dark theme
    fig.update_layout(
        template="plotly_dark",
        title_text=f"📊 {cfg.APP_NAME} - Analytics Dashboard<br><sup>Total Crossings: {summary['total_count']} (IN: {summary['total_in']} | OUT: {summary['total_out']})</sup>",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font=dict(family="sans-serif", color="#e5e7eb"),
        barmode="group",
        height=750,
        showlegend=True
    )

    fig.write_html(str(output_html))
    logger.info(f"Interactive analytics dashboard generated: {output_html}")

    if open_in_browser:
        webbrowser.open(output_html.as_uri())

    return output_html


if __name__ == "__main__":
    generate_analytics_dashboard(open_in_browser=True)
