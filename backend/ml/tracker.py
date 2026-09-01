"""
Object Tracking module using ByteTrack via YOLOv8.
Maintains persistent IDs across video frames and extracts ground-contact / centroid coordinates.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import torch
from ultralytics import YOLO

from backend.config import settings
from backend.logger import logger


class ByteTrackerManager:
    """Manages ByteTrack tracking using YOLOv8 persistent tracking pipeline."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        tracker_type: str = "bytetrack.yaml",
        conf_thresh: Optional[float] = None,
        iou_thresh: Optional[float] = None,
        target_classes: Optional[List[int]] = None
    ):
        self.model_path = model_path or settings.MODEL_PATH
        self.tracker_type = tracker_type or settings.TRACKER_TYPE
        self.conf = conf_thresh or settings.CONFIDENCE_THRESHOLD
        self.iou = iou_thresh or settings.IOU_THRESHOLD
        self.target_classes = target_classes if target_classes is not None else settings.TARGET_CLASSES

        # Determine optimal device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        logger.info(f"Initializing ByteTracker with model {self.model_path} on {self.device}")
        self.model = YOLO(self.model_path)
        logger.info("ByteTracker initialized.")

    def track(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs tracking on a frame. Returns list of tracked objects with IDs and centroids:
        [{
            'track_id': int,
            'class_id': int,
            'class_name': str,
            'confidence': float,
            'bbox': [x1, y1, x2, y2],
            'centroid': (cx, cy),
            'bottom_center': (cx, y2)
        }]
        """
        results = self.model.track(
            source=frame,
            persist=True,
            tracker=self.tracker_type,
            conf=self.conf,
            iou=self.iou,
            classes=self.target_classes,
            device=self.device,
            verbose=False
        )

        tracked_objects = []
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            if boxes is not None and boxes.id is not None:
                track_ids = boxes.id.cpu().numpy().astype(int).tolist()
                classes = boxes.cls.cpu().numpy().astype(int).tolist()
                confs = boxes.conf.cpu().numpy().astype(float).tolist()
                xyxys = boxes.xyxy.cpu().numpy().tolist()

                for tid, cls_id, conf, xyxy in zip(track_ids, classes, confs, xyxys):
                    x1, y1, x2, y2 = xyxy
                    # Centroid and bottom-center (ground plane contact)
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    bottom_center = (cx, y2)

                    class_name = settings.CLASS_NAMES.get(cls_id, result.names.get(cls_id, f"class_{cls_id}"))

                    tracked_objects.append({
                        "track_id": int(tid),
                        "class_id": int(cls_id),
                        "class_name": class_name,
                        "confidence": float(conf),
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "centroid": (float(cx), float(cy)),
                        "bottom_center": (float(bottom_center[0]), float(bottom_center[1]))
                    })

        return tracked_objects
