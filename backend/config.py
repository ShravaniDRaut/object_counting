"""
Application configuration and environment settings.
"""
from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "AI Real-Time Object Counting System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Model & Tracking Configuration
    MODEL_PATH: str = str(BASE_DIR / "models" / "yolov8n.pt")
    CONFIDENCE_THRESHOLD: float = 0.35
    IOU_THRESHOLD: float = 0.45
    TRACKER_TYPE: str = "bytetrack.yaml"
    
    # Target Class IDs (COCO: 0=person, 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck)
    TARGET_CLASSES: Union[List[int], str] = [0, 1, 2, 3, 5, 7]

    @field_validator("TARGET_CLASSES", mode="before")
    @classmethod
    def parse_target_classes(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                import json
                return [int(x) for x in json.loads(v)]
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    CLASS_NAMES: dict = {
        0: "person",
        1: "bicycle",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck"
    }

    # Virtual Line Configuration (Normalized coordinates: 0.0 to 1.0)
    # Default line horizontally across the middle of the frame: (0.1, 0.5) -> (0.9, 0.5)
    LINE_START_X: float = 0.1
    LINE_START_Y: float = 0.5
    LINE_END_X: float = 0.9
    LINE_END_Y: float = 0.5

    # Storage Paths
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'object_counting.db'}"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    EXPORT_DIR: Path = BASE_DIR / "data" / "exports"
    SAMPLE_DIR: Path = BASE_DIR / "data" / "samples"
    MODELS_DIR: Path = BASE_DIR / "models"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Ensure directories exist
for path in [settings.UPLOAD_DIR, settings.EXPORT_DIR, settings.SAMPLE_DIR, settings.MODELS_DIR]:
    path.mkdir(parents=True, exist_ok=True)
