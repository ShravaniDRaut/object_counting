"""
OpenCV Frame Annotator module.
Renders bounding boxes, tracking labels, movement trails, counting lines, and on-screen HUD.
"""
from typing import Tuple, List, Dict, Any, Set
import cv2
import numpy as np

CLASS_COLORS = {
    "person": (255, 204, 0),       # Cyan / Light Blue
    "car": (0, 255, 0),             # Lime Green
    "bus": (0, 165, 255),           # Orange
    "truck": (255, 0, 128),         # Purple / Magenta
    "motorcycle": (0, 215, 255),    # Yellow
    "bicycle": (203, 192, 255)      # Soft Pink
}
DEFAULT_COLOR = (200, 200, 200)


class FrameAnnotator:
    """Draws visual annotations and HUD banners on OpenCV frames."""

    def __init__(self):
        self.show_boxes = True
        self.show_trails = True
        self.show_line = True
        self.show_hud = True

    def annotate(
        self,
        frame: np.ndarray,
        tracked_objects: List[Dict[str, Any]],
        track_histories: Dict[int, List[Tuple[float, float]]],
        line_start: Tuple[int, int],
        line_end: Tuple[int, int],
        has_new_crossing: bool,
        stats: Dict[str, Any]
    ) -> np.ndarray:
        """Annotates the video frame in-place or returns a copy."""
        img = frame.copy()
        h, w = img.shape[:2]
        active_ids = {obj["track_id"] for obj in tracked_objects}

        # 1. Draw Trajectory Trails
        if self.show_trails:
            for tid, history in track_histories.items():
                if tid in active_ids and len(history) > 1:
                    pts = np.array(history, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(img, [pts], isClosed=False, color=(0, 220, 255), thickness=2)

        # 2. Draw Bounding Boxes and Labels
        if self.show_boxes:
            for obj in tracked_objects:
                x1, y1, x2, y2 = map(int, obj["bbox"])
                cls_name = obj["class_name"]
                conf = obj["confidence"]
                tid = obj["track_id"]
                color = CLASS_COLORS.get(cls_name, DEFAULT_COLOR)

                # Box rectangle
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

                # Label background & text
                label = f"#{tid} {cls_name.capitalize()} {conf:.2f}"
                (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                cv2.rectangle(img, (x1, max(0, y1 - 20)), (x1 + lw + 6, max(0, y1)), color, -1)
                cv2.putText(
                    img, label, (x1 + 3, max(14, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA
                )

                # Ground contact marker (bottom-center)
                cx, cy = map(int, obj["bottom_center"])
                cv2.circle(img, (cx, cy), 4, (0, 0, 255), -1)

        # 3. Draw Virtual Counting Line
        if self.show_line:
            p1 = (int(line_start[0]), int(line_start[1]))
            p2 = (int(line_end[0]), int(line_end[1]))
            line_color = (0, 0, 255) if has_new_crossing else (0, 255, 255)

            cv2.line(img, p1, p2, line_color, 3)
            cv2.circle(img, p1, 6, (0, 255, 0), -1)
            cv2.circle(img, p2, 6, (0, 255, 0), -1)

            mid_x = (p1[0] + p2[0]) // 2
            mid_y = (p1[1] + p2[1]) // 2 - 10
            cv2.putText(
                img, "COUNTING LINE", (mid_x - 55, mid_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 2, cv2.LINE_AA
            )

        # 4. Draw HUD Overlays
        if self.show_hud:
            self._draw_hud(img, stats)

        return img

    def _draw_hud(self, img: np.ndarray, stats: Dict[str, Any]):
        """Renders responsive header banner and footer controls HUD."""
        h, w = img.shape[:2]

        # Dynamic scale based on width
        scale = max(0.35, min(0.6, (w / 1280.0) * 0.6))
        small_scale = max(0.3, scale * 0.82)
        thickness = 1 if w < 640 else 2

        # Extract stats
        fps = stats.get("fps", 0.0)
        in_frame_count = stats.get("in_frame_count", 0)
        total_unique = stats.get("total_unique_detected", 0)
        total_in = stats.get("total_in", 0)
        total_out = stats.get("total_out", 0)
        total_crossed = stats.get("total_crossed", total_in + total_out)
        in_frame_classes = stats.get("in_frame_classes", {})
        cumulative_classes = stats.get("cumulative_class_counts", {})

        # Top Header Banner
        top_h = max(68, int(h * 0.16))
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, top_h), (18, 22, 30), -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
        cv2.line(img, (0, top_h), (w, top_h), (0, 215, 255), 2)

        # Line 1: Primary Metrics (FPS, In-Frame Objects, Total Objects Seen, Line Crossings)
        y1 = int(top_h * 0.38)
        line1_text = (
            f"FPS: {fps:.1f}  |  "
            f"IN FRAME: {in_frame_count}  |  "
            f"TOTAL DETECTED: {total_unique}  |  "
            f"CROSSED: {total_crossed} (IN:{total_in} OUT:{total_out})"
        )
        cv2.putText(img, line1_text, (10, y1), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 255), thickness, cv2.LINE_AA)

        # Line 2: In-Frame Object Type Breakdown
        y2 = int(top_h * 0.65)
        if in_frame_classes:
            frame_cats = [f"{k.capitalize()}: {v}" for k, v in sorted(in_frame_classes.items())]
            frame_str = "In-Frame Types: " + " | ".join(frame_cats)
        else:
            frame_str = "In-Frame Types: None"
        cv2.putText(img, frame_str, (10, y2), cv2.FONT_HERSHEY_SIMPLEX, small_scale, (100, 255, 100), 1, cv2.LINE_AA)

        # Line 3: Cumulative Unique Objects by Category
        y3 = int(top_h * 0.90)
        if cumulative_classes:
            cum_cats = [f"{k.capitalize()}: {v}" for k, v in sorted(cumulative_classes.items())]
            cum_str = "Cumulative Unique: " + " | ".join(cum_cats)
        else:
            cum_str = "Target Categories: Person, Car, Bus, Truck, Motorcycle, Bicycle"
        cv2.putText(img, cum_str, (10, y3), cv2.FONT_HERSHEY_SIMPLEX, small_scale, (200, 200, 210), 1, cv2.LINE_AA)

        # Bottom Controls Banner
        bot_h = max(26, int(h * 0.05))
        cv2.rectangle(overlay, (0, h - bot_h), (w, h), (15, 18, 25), -1)
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)
        controls_text = "[Q] Quit | [P] Pause | [R] Reset | [H] HUD | [T] Trails | [S] Snapshot"
        cv2.putText(img, controls_text, (10, h - int(bot_h * 0.28)), cv2.FONT_HERSHEY_SIMPLEX, small_scale, (0, 220, 255), 1, cv2.LINE_AA)
