"""
Video processing utilities and capture abstractions.
"""
from pathlib import Path
from typing import Dict, Any, Generator, Optional, Union
import cv2
import numpy as np

from backend.logger import logger


def get_video_metadata(filepath: Union[str, Path]) -> Dict[str, Any]:
    """Extract resolution, fps, frame count, and duration from video file."""
    cap = cv2.VideoCapture(str(filepath))
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {filepath}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0.0

    cap.release()

    return {
        "width": width,
        "height": height,
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "duration": round(duration, 2)
    }


class VideoStreamSource:
    """
    Unified capture generator for video files, live webcam, and RTSP streams.
    Supports auto-looping for demonstration videos.
    """

    def __init__(self, source: Union[str, int, Path], loop: bool = True):
        self.source = str(source) if isinstance(source, Path) else source
        self.loop = loop
        self.cap = None
        self._open()

    def _open(self):
        # Convert numeric string to int if webcam index
        src = self.source
        if isinstance(src, str) and src.isdigit():
            src = int(src)
        self.cap = cv2.VideoCapture(src)
        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {self.source}")

    def read_frame(self) -> Optional[np.ndarray]:
        if self.cap is None or not self.cap.isOpened():
            self._open()
            if not self.cap.isOpened():
                return None

        ret, frame = self.cap.read()
        if not ret:
            if self.loop and not isinstance(self.source, int):
                # Reset to beginning if file
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
                if not ret:
                    return None
            else:
                return None

        return frame

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
