"""
Real-time Computer Vision Pipeline.
Integrates detection, ByteTrack tracking, line-crossing counting, visual annotation, and FPS calculation.
"""
import time
from typing import Tuple, Optional, List, Dict, Any
import cv2
import numpy as np

from backend.config import settings
from backend.logger import logger
from backend.ml.tracker import ByteTrackerManager
from backend.ml.line_counter import LineCrossingCounter

# Color palette for classes (BGR)
CLASS_COLORS = {
    "person": (255, 204, 0),       # Cyan / Light Blue
    "car": (0, 255, 0),             # Lime Green
    "bus": (0, 165, 255),           # Orange
    "truck": (255, 0, 128),         # Purple / Pink
    "motorcycle": (0, 215, 255),    # Golden Yellow
    "bicycle": (203, 192, 255)      # Light Pink
}
DEFAULT_COLOR = (200, 200, 200)


class VisionPipeline:
    """
    Complete end-to-end pipeline processing video frames:
    Frame -> ByteTrack -> Line Counter -> Frame Annotation (Boxes, Trails, HUD) -> Database Callback
    """

    def __init__(
        self,
        line_start: Optional[Tuple[float, float]] = None,
        line_end: Optional[Tuple[float, float]] = None,
        direction_mode: str = "bidirectional",
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        target_classes: Optional[List[int]] = None
    ):
        # Default line: (10% x, 50% y) -> (90% x, 50% y) normalized
        self.norm_line_start = line_start or (settings.LINE_START_X, settings.LINE_START_Y)
        self.norm_line_end = line_end or (settings.LINE_END_X, settings.LINE_END_Y)

        self.tracker = ByteTrackerManager(
            conf_thresh=confidence_threshold,
            iou_thresh=iou_threshold,
            target_classes=target_classes
        )

        # Line counter initialized with temporary pixel values, updated on first frame dimensions
        self.counter = LineCrossingCounter(
            line_start=(100, 360),
            line_end=(1180, 360),
            direction_mode=direction_mode
        )

        self.frame_idx = 0
        self.fps = 0.0
        self.prev_time = time.time()
        self.frame_width = 1280
        self.frame_height = 720
        self.line_initialized = False

        # Visual toggle flags
        self.show_boxes = True
        self.show_trails = True
        self.show_line = True
        self.show_hud = True

    def set_line_coordinates(self, start: Tuple[float, float], end: Tuple[float, float]):
        """Set normalized (0.0 to 1.0) coordinates for counting line."""
        self.norm_line_start = start
        self.norm_line_end = end
        # Update pixel line based on current frame dimensions
        px_start = (self.norm_line_start[0] * self.frame_width, self.norm_line_start[1] * self.frame_height)
        px_end = (self.norm_line_end[0] * self.frame_width, self.norm_line_end[1] * self.frame_height)
        self.counter.update_line(px_start, px_end)

    def set_confidence(self, conf: float):
        """Update detector confidence threshold on the fly."""
        self.tracker.conf = conf

    def reset(self):
        """Reset state for a new video stream."""
        self.counter.reset_counts()
        self.frame_idx = 0
        self.fps = 0.0
        self.prev_time = time.time()

    def process_frame(
        self,
        frame: np.ndarray,
        on_crossing_callback=None,
        on_detections_callback=None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process single frame through tracking, line counting, and visual annotation.
        Returns:
            annotated_frame (np.ndarray), stats_dict (dict)
        """
        self.frame_idx += 1
        h, w = frame.shape[:2]
        self.frame_height = h
        self.frame_width = w

        # Calculate FPS
        current_time = time.time()
        dt = current_time - self.prev_time
        if dt > 0:
            current_fps = 1.0 / dt
            self.fps = 0.9 * self.fps + 0.1 * current_fps if self.fps > 0 else current_fps
        self.prev_time = current_time

        # Ensure counting line is scaled to frame dimensions
        px_start = (self.norm_line_start[0] * w, self.norm_line_start[1] * h)
        px_end = (self.norm_line_end[0] * w, self.norm_line_end[1] * h)
        self.counter.update_line(px_start, px_end)

        # 1. ByteTrack Object Tracking
        tracked_objects = self.tracker.track(frame)
        active_track_ids = set()
        new_crossing_events = []

        # 2. Line Crossing Detection
        for obj in tracked_objects:
            tid = obj["track_id"]
            active_track_ids.add(tid)
            # Use bottom-center for ground plane crossing accuracy
            point_of_interest = obj["bottom_center"]
            cls_name = obj["class_name"]
            conf = obj["confidence"]

            event = self.counter.process_track(
                track_id=tid,
                centroid=point_of_interest,
                class_name=cls_name,
                frame_idx=self.frame_idx,
                confidence=conf
            )

            if event:
                new_crossing_events.append(event)
                if on_crossing_callback:
                    try:
                        on_crossing_callback(event)
                    except Exception as e:
                        logger.error(f"Error in on_crossing_callback: {e}")

        # Optional detection callback (for database batch logging)
        if on_detections_callback and tracked_objects:
            try:
                on_detections_callback(self.frame_idx, tracked_objects)
            except Exception as e:
                logger.error(f"Error in on_detections_callback: {e}")

        # 3. Visual Annotation
        annotated = frame.copy()

        # Draw trajectory trails
        if self.show_trails:
            for tid, history in self.counter.track_histories.items():
                if tid in active_track_ids and len(history) > 1:
                    pts = np.array(history, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated, [pts], isClosed=False, color=(0, 220, 255), thickness=2)

        # Draw bounding boxes & labels
        if self.show_boxes:
            for obj in tracked_objects:
                x1, y1, x2, y2 = map(int, obj["bbox"])
                cls_name = obj["class_name"]
                conf = obj["confidence"]
                tid = obj["track_id"]
                color = CLASS_COLORS.get(cls_name, DEFAULT_COLOR)

                # Bounding box
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

                # Label tag
                label = f"#{tid} {cls_name.capitalize()} {conf:.2f}"
                (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(annotated, (x1, max(0, y1 - 22)), (x1 + lw + 6, max(0, y1)), color, -1)
                cv2.putText(annotated, label, (x1 + 3, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

                # Ground point marker
                cx, cy = map(int, obj["bottom_center"])
                cv2.circle(annotated, (cx, cy), 4, (0, 0, 255), -1)

        # Draw virtual counting line
        if self.show_line:
            p1 = (int(px_start[0]), int(px_start[1]))
            p2 = (int(px_end[0]), int(px_end[1]))
            line_color = (0, 0, 255) if len(new_crossing_events) > 0 else (0, 255, 255)  # Flash red when crossed
            cv2.line(annotated, p1, p2, line_color, 3)
            # Line endpoints
            cv2.circle(annotated, p1, 6, (0, 200, 0), -1)
            cv2.circle(annotated, p2, 6, (0, 200, 0), -1)
            # Line Label
            mid_x = (p1[0] + p2[0]) // 2
            mid_y = (p1[1] + p2[1]) // 2 - 10
            cv2.putText(annotated, "COUNTING LINE", (mid_x - 60, mid_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2, cv2.LINE_AA)

        # Draw HUD overlay
        if self.show_hud:
            self._draw_hud(annotated)

        # Current frame statistics
        stats = {
            "fps": round(self.fps, 1),
            "frame_idx": self.frame_idx,
            "total_in": self.counter.total_in,
            "total_out": self.counter.total_out,
            "total_count": self.counter.total_in + self.counter.total_out,
            "active_tracks": len(active_track_ids),
            "class_counts": self.counter.class_counts,
            "recent_events": self.counter.recent_events[:10],
            "new_crossings": new_crossing_events
        }

        return annotated, stats

    def _draw_hud(self, img: np.ndarray):
        """Draw on-screen semi-transparent HUD banner with live counters."""
        h, w = img.shape[:2]
        banner_h = 75
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (w, banner_h), (20, 24, 33), -1)
        cv2.addWeighted(overlay, 0.75, img, 0.25, 0, img)

        # Top border accent
        cv2.line(img, (0, banner_h), (w, banner_h), (0, 200, 255), 2)

        # HUD Text items
        fps_text = f"FPS: {self.fps:.1f}"
        in_text = f"IN: {self.counter.total_in}"
        out_text = f"OUT: {self.counter.total_out}"
        total_text = f"TOTAL: {self.counter.total_in + self.counter.total_out}"

        cv2.putText(img, fps_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2, cv2.LINE_AA)
        cv2.putText(img, in_text, (180, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(img, out_text, (320, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 100, 255), 2, cv2.LINE_AA)
        cv2.putText(img, total_text, (480, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        # Class breakdown sub-line
        cats = [f"{k.capitalize()}: {v['TOTAL']}" for k, v in self.counter.class_counts.items() if v['TOTAL'] > 0]
        cat_text = " | ".join(cats) if cats else "Waiting for detections..."
        cv2.putText(img, cat_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 190, 200), 1, cv2.LINE_AA)
