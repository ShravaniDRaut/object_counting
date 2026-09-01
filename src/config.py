"""
Configuration module for standalone Computer Vision Object Counting System.
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
load_dotenv(BASE_DIR / ".env")


class Config:
    # Application Info
    APP_NAME = os.getenv("APP_NAME", "AI Real-Time Object Counting System")
    APP_VERSION = "2.0.0"

    # Computer Vision & Detection Parameters
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "yolov8n.pt"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
    IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.45"))
    TRACKER_TYPE = os.getenv("TRACKER_TYPE", "bytetrack.yaml")

    # Target Class IDs (COCO: 0=person, 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck)
    _raw_classes = os.getenv("TARGET_CLASSES", "[0, 1, 2, 3, 5, 7]").strip()
    try:
        TARGET_CLASSES = json.loads(_raw_classes) if _raw_classes.startswith("[") else [int(x) for x in _raw_classes.split(",") if x.strip()]
    except Exception:
        TARGET_CLASSES = [0, 1, 2, 3, 5, 7]

    CLASS_NAMES = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    # Virtual Line Default Normalized Coordinates (x1, y1, x2, y2)
    _raw_line = os.getenv("LINE_COORDS", "0.1,0.5,0.9,0.5").split(",")
    LINE_START_X = float(_raw_line[0]) if len(_raw_line) > 0 else 0.1
    LINE_START_Y = float(_raw_line[1]) if len(_raw_line) > 1 else 0.5
    LINE_END_X = float(_raw_line[2]) if len(_raw_line) > 2 else 0.9
    LINE_END_Y = float(_raw_line[3]) if len(_raw_line) > 3 else 0.5

    # Storage Paths
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'object_counting.db'}")
    EXPORT_DIR = BASE_DIR / os.getenv("EXPORT_DIR", "data/exports")
    SAMPLE_DIR = BASE_DIR / os.getenv("SAMPLE_DIR", "data/samples")
    OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "data/outputs")
    MODELS_DIR = BASE_DIR / "models"


cfg = Config()

# Create directories
for p in [cfg.EXPORT_DIR, cfg.SAMPLE_DIR, cfg.OUTPUT_DIR, cfg.MODELS_DIR]:
    p.mkdir(parents=True, exist_ok=True)
