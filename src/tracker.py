"""
Object Tracking module using ByteTrack.
Maintains persistent tracklet IDs across frames and extracts ground-contact points.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import torch
from ultralytics import YOLO

from src.config import cfg
from src.logger import logger


class ByteTrackerManager:
    """ByteTrack Tracker Manager integrating YOLOv8 tracking."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        tracker_type: Optional[str] = None,
        conf_thresh: Optional[float] = None,
        iou_thresh: Optional[float] = None,
        target_classes: Optional[List[int]] = None
    ):
        self.model_path = model_path or cfg.MODEL_PATH
        self.tracker_type = tracker_type or cfg.TRACKER_TYPE
        self.conf = conf_thresh if conf_thresh is not None else cfg.CONFIDENCE_THRESHOLD
        self.iou = iou_thresh if iou_thresh is not None else cfg.IOU_THRESHOLD
        self.target_classes = target_classes if target_classes is not None else cfg.TARGET_CLASSES

        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        logger.info(f"Initializing ByteTrack tracker with {self.model_path} on {self.device}")
        self.model = YOLO(self.model_path)
        logger.info("ByteTrack tracker initialized.")

    def track(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run tracking on a frame.
        Returns:
            [{'track_id': int, 'class_name': str, 'confidence': float, 'bbox': [x1,y1,x2,y2], 'bottom_center': (cx, y2), 'centroid': (cx, cy)}]
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

        tracked = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            if boxes is not None and boxes.id is not None:
                ids = boxes.id.cpu().numpy().astype(int).tolist()
                classes = boxes.cls.cpu().numpy().astype(int).tolist()
                confs = boxes.conf.cpu().numpy().astype(float).tolist()
                xyxys = boxes.xyxy.cpu().numpy().tolist()

                for tid, cls_id, conf, xyxy in zip(ids, classes, confs, xyxys):
                    x1, y1, x2, y2 = xyxy
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0
                    bottom_center = (cx, y2)
                    class_name = cfg.CLASS_NAMES.get(cls_id, results[0].names.get(cls_id, f"class_{cls_id}"))

                    tracked.append({
                        "track_id": int(tid),
                        "class_id": int(cls_id),
                        "class_name": class_name,
                        "confidence": float(conf),
                        "bbox": [float(x1), float(y1), float(x2), float(y2)],
                        "centroid": (float(cx), float(cy)),
                        "bottom_center": (float(bottom_center[0]), float(bottom_center[1]))
                    })

        return tracked
