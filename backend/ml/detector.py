"""
YOLOv8 Object Detector Wrapper.
Handles model loading, warm-up, device detection, and class filtering.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import torch
import numpy as np
from ultralytics import YOLO

from backend.config import settings
from backend.logger import logger


class ObjectDetector:
    """YOLOv8 Detector with COCO vehicle & pedestrian class filtering."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        target_classes: Optional[List[int]] = None
    ):
        self.model_path = model_path or settings.MODEL_PATH
        self.conf = confidence_threshold or settings.CONFIDENCE_THRESHOLD
        self.iou = iou_threshold or settings.IOU_THRESHOLD
        self.target_classes = target_classes if target_classes is not None else settings.TARGET_CLASSES

        # Determine optimal device
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        logger.info(f"Loading YOLOv8 model from {self.model_path} on device: {self.device}")
        self.model = YOLO(self.model_path)
        logger.info("YOLOv8 model loaded successfully.")

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run inference on a single BGR image/frame.
        Returns filtered detections list:
        [{'bbox': [x1, y1, x2, y2], 'confidence': float, 'class_id': int, 'class_name': str}]
        """
        results = self.model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            classes=self.target_classes,
            device=self.device,
            verbose=False
        )

        detections = []
        if results and len(results) > 0:
            result = results[0]
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    class_name = settings.CLASS_NAMES.get(cls_id, result.names.get(cls_id, f"class_{cls_id}"))

                    detections.append({
                        "bbox": xyxy,  # [x1, y1, x2, y2]
                        "confidence": conf,
                        "class_id": cls_id,
                        "class_name": class_name
                    })

        return detections
