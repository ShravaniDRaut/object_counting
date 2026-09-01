"""
YOLOv8 Object Detector Wrapper.
Loads the model onto CPU/CUDA and performs class-filtered object detection.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import torch
from ultralytics import YOLO

from src.config import cfg
from src.logger import logger


class ObjectDetector:
    """YOLOv8 Detector specialized for vehicles and pedestrians."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_thresh: Optional[float] = None,
        iou_thresh: Optional[float] = None,
        target_classes: Optional[List[int]] = None
    ):
        self.model_path = model_path or cfg.MODEL_PATH
        self.conf = conf_thresh if conf_thresh is not None else cfg.CONFIDENCE_THRESHOLD
        self.iou = iou_thresh if iou_thresh is not None else cfg.IOU_THRESHOLD
        self.target_classes = target_classes if target_classes is not None else cfg.TARGET_CLASSES

        # Device selection
        if torch.cuda.is_available():
            self.device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        logger.info(f"Loading YOLOv8 detector: {self.model_path} on {self.device}")
        self.model = YOLO(self.model_path)
        logger.info("YOLOv8 detector loaded.")

    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Run inference on a single BGR frame.
        Returns:
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
            boxes = results[0].boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].cpu().numpy().tolist()
                    class_name = cfg.CLASS_NAMES.get(cls_id, results[0].names.get(cls_id, f"class_{cls_id}"))

                    detections.append({
                        "bbox": xyxy,
                        "confidence": conf,
                        "class_id": cls_id,
                        "class_name": class_name
                    })

        return detections
