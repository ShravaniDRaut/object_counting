"""
Precision Line-Crossing Counting Algorithm.
Uses 2D vector geometry and segment intersection to detect line-crossing events,
determine movement direction (IN vs OUT), and prevent double-counting.
"""
from typing import Tuple, Dict, Set, Optional, List
from datetime import datetime, timezone
import numpy as np


class LineCrossingCounter:
    """Tracks trajectory history and computes line crossings."""

    def __init__(
        self,
        line_start: Tuple[float, float],
        line_end: Tuple[float, float],
        direction_mode: str = "bidirectional",
        history_len: int = 30,
        cooldown_frames: int = 60
    ):
        self.line_start = np.array(line_start, dtype=np.float32)
        self.line_end = np.array(line_end, dtype=np.float32)
        self.direction_mode = direction_mode
        self.history_len = history_len
        self.cooldown_frames = cooldown_frames

        # Trajectory & state tracking
        self.track_histories: Dict[int, List[Tuple[float, float]]] = {}
        self.track_last_counted: Dict[int, int] = {}
        self.counted_ids: Set[int] = set()

        # Cumulative counters
        self.total_in = 0
        self.total_out = 0
        self.class_counts: Dict[str, Dict[str, int]] = {}
        self.recent_events: List[dict] = []

    def update_line(self, line_start: Tuple[float, float], line_end: Tuple[float, float]):
        self.line_start = np.array(line_start, dtype=np.float32)
        self.line_end = np.array(line_end, dtype=np.float32)

    def reset_counts(self):
        self.track_histories.clear()
        self.track_last_counted.clear()
        self.counted_ids.clear()
        self.total_in = 0
        self.total_out = 0
        self.class_counts.clear()
        self.recent_events.clear()

    @staticmethod
    def _ccw(A: np.ndarray, B: np.ndarray, C: np.ndarray) -> float:
        """Counter-clockwise cross product test."""
        return (C[1] - A[1]) * (B[0] - A[0]) - (B[1] - A[1]) * (C[0] - A[0])

    def _intersect(self, A: np.ndarray, B: np.ndarray, C: np.ndarray, D: np.ndarray) -> bool:
        """Determines if segment AB (trajectory) intersects segment CD (counting line)."""
        ccw1 = self._ccw(A, C, D)
        ccw2 = self._ccw(B, C, D)
        ccw3 = self._ccw(A, B, C)
        ccw4 = self._ccw(A, B, D)
        return ((ccw1 > 0) != (ccw2 > 0)) and ((ccw3 > 0) != (ccw4 > 0))

    def _determine_direction(self, prev_pos: np.ndarray, curr_pos: np.ndarray) -> str:
        """Determines direction relative to line orientation."""
        side_prev = self._ccw(self.line_start, self.line_end, prev_pos)
        side_curr = self._ccw(self.line_start, self.line_end, curr_pos)
        if side_prev <= 0 and side_curr > 0:
            return "IN"
        elif side_prev >= 0 and side_curr < 0:
            return "OUT"
        return "IN" if side_curr > 0 else "OUT"

    def process_track(
        self,
        track_id: int,
        centroid: Tuple[float, float],
        class_name: str,
        frame_idx: int,
        confidence: float = 1.0
    ) -> Optional[dict]:
        """Processes an object position and returns an event dict if line is crossed."""
        curr_pt = np.array(centroid, dtype=np.float32)

        if track_id not in self.track_histories:
            self.track_histories[track_id] = [centroid]
            return None

        history = self.track_histories[track_id]
        prev_pt = np.array(history[-1], dtype=np.float32)
        history.append(centroid)

        if len(history) > self.history_len:
            self.track_histories[track_id] = history[-self.history_len:]

        # Cooldown test to prevent edge chatter double-counting
        last_frame = self.track_last_counted.get(track_id, -self.cooldown_frames)
        if (frame_idx - last_frame) < self.cooldown_frames:
            return None

        # Intersection test
        if self._intersect(prev_pt, curr_pt, self.line_start, self.line_end):
            direction = self._determine_direction(prev_pt, curr_pt)

            if self.direction_mode == "in_only" and direction != "IN":
                return None
            if self.direction_mode == "out_only" and direction != "OUT":
                return None

            self.track_last_counted[track_id] = frame_idx
            self.counted_ids.add(track_id)

            if direction == "IN":
                self.total_in += 1
            else:
                self.total_out += 1

            if class_name not in self.class_counts:
                self.class_counts[class_name] = {"IN": 0, "OUT": 0, "TOTAL": 0}
            self.class_counts[class_name][direction] += 1
            self.class_counts[class_name]["TOTAL"] += 1

            event = {
                "track_id": track_id,
                "class_name": class_name,
                "direction": direction,
                "confidence": round(float(confidence), 2),
                "frame_idx": frame_idx,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            self.recent_events.insert(0, event)
            if len(self.recent_events) > 20:
                self.recent_events = self.recent_events[:20]

            return event

        return None
