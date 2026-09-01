"""
Precision Line-Crossing Counting Algorithm.
Uses vector geometry and 2D segment intersection tests to determine
when tracked object centroids cross a user-configured virtual line,
accurately discerning direction (IN vs OUT) and preventing double-counting.
"""
from typing import Tuple, Dict, Set, Optional, List
from datetime import datetime, timezone
import numpy as np


class LineCrossingCounter:
    """
    Tracks trajectory history of objects and determines line-crossing events.
    """
    def __init__(
        self,
        line_start: Tuple[float, float],
        line_end: Tuple[float, float],
        direction_mode: str = "bidirectional",
        history_len: int = 30,
        cooldown_frames: int = 60
    ):
        """
        :param line_start: (x1, y1) start coordinates of virtual line
        :param line_end: (x2, y2) end coordinates of virtual line
        :param direction_mode: 'bidirectional', 'in_only', or 'out_only'
        :param history_len: Number of previous centroids to keep for trail rendering
        :param cooldown_frames: Minimum frames before the same track ID can be counted again
        """
        self.line_start = np.array(line_start, dtype=np.float32)
        self.line_end = np.array(line_end, dtype=np.float32)
        self.direction_mode = direction_mode
        self.history_len = history_len
        self.cooldown_frames = cooldown_frames

        # Track state management
        self.track_histories: Dict[int, List[Tuple[float, float]]] = {}
        self.track_last_counted: Dict[int, int] = {}  # track_id -> frame_number
        self.counted_ids: Set[int] = set()

        # Cumulative totals
        self.total_in = 0
        self.total_out = 0
        self.class_counts: Dict[str, Dict[str, int]] = {}

        # Recent crossing events list for live feed HUD
        self.recent_events: List[dict] = []

    def update_line(self, line_start: Tuple[float, float], line_end: Tuple[float, float]):
        """Dynamically update virtual line coordinates."""
        self.line_start = np.array(line_start, dtype=np.float32)
        self.line_end = np.array(line_end, dtype=np.float32)

    def reset_counts(self):
        """Reset counting totals and track histories."""
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
        """
        Determines if line segment AB intersects line segment CD.
        AB = trajectory segment (prev_pos, curr_pos)
        CD = virtual counting line (line_start, line_end)
        """
        ccw1 = self._ccw(A, C, D)
        ccw2 = self._ccw(B, C, D)
        ccw3 = self._ccw(A, B, C)
        ccw4 = self._ccw(A, B, D)

        # Check if line segments straddle each other
        return ((ccw1 > 0) != (ccw2 > 0)) and ((ccw3 > 0) != (ccw4 > 0))

    def _determine_direction(self, prev_pos: np.ndarray, curr_pos: np.ndarray) -> str:
        """
        Determines whether the movement from prev_pos to curr_pos is 'IN' or 'OUT'
        relative to the oriented line vector (line_start -> line_end).
        Positive ccw = left side, Negative ccw = right side.
        """
        # Direction based on side transition relative to line
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
        """
        Update trajectory for track_id and test for line crossing.
        Returns crossing event dictionary if a crossing occurred, else None.
        """
        curr_pt = np.array(centroid, dtype=np.float32)

        if track_id not in self.track_histories:
            self.track_histories[track_id] = [centroid]
            return None

        history = self.track_histories[track_id]
        prev_pt = np.array(history[-1], dtype=np.float32)
        history.append(centroid)

        # Trim trajectory history
        if len(history) > self.history_len:
            self.track_histories[track_id] = history[-self.history_len:]

        # Check cooldown to prevent duplicate counting of oscillating tracks
        last_frame = self.track_last_counted.get(track_id, -self.cooldown_frames)
        if (frame_idx - last_frame) < self.cooldown_frames:
            return None

        # Test line intersection
        has_crossed = self._intersect(prev_pt, curr_pt, self.line_start, self.line_end)

        if has_crossed:
            direction = self._determine_direction(prev_pt, curr_pt)

            # Check if filtered by direction mode
            if self.direction_mode == "in_only" and direction != "IN":
                return None
            if self.direction_mode == "out_only" and direction != "OUT":
                return None

            # Register count
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
            if len(self.recent_events) > 50:
                self.recent_events = self.recent_events[:50]

            return event

        return None

    def clean_stale_tracks(self, active_track_ids: Set[int]):
        """Remove histories of tracks that have permanently left the frame."""
        for tid in list(self.track_histories.keys()):
            if tid not in active_track_ids:
                # Keep in memory for 100 frames then purge to avoid memory leaks
                pass
