"""
Video management API endpoints.
Handles video upload, metadata extraction, listing, deletion, and sample generation.
"""
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database.connection import get_db
from backend.database import crud
from backend.schemas.payload import VideoResponse, VideoUploadResponse
from backend.utils.video_utils import get_video_metadata
from backend.utils.sample_generator import generate_sample_traffic_video
from backend.logger import logger

router = APIRouter(prefix="/api/videos", tags=["Videos"])

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.post("/upload", response_model=VideoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a video file (MP4, AVI, MOV), validate metadata, and store in database.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Sanitize and prepare destination
    clean_filename = f"upload_{Path(file.filename).name}"
    save_path = settings.UPLOAD_DIR / clean_filename

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save video file: {str(e)}"
        )

    # Extract video properties
    try:
        meta = get_video_metadata(save_path)
    except Exception as e:
        # If metadata extraction fails, still keep basic record
        logger.warning(f"Could not probe video metadata: {e}")
        meta = {"width": 0, "height": 0, "fps": 0.0, "total_frames": 0, "duration": 0.0}

    video_record = crud.create_video(
        db=db,
        filename=file.filename,
        filepath=str(save_path),
        source_type="upload",
        duration=meta.get("duration", 0.0),
        width=meta.get("width", 0),
        height=meta.get("height", 0),
        fps=meta.get("fps", 0.0),
        total_frames=meta.get("total_frames", 0),
        status="ready"
    )

    logger.info(f"Video uploaded successfully: {file.filename} (ID: {video_record.id})")

    return {
        "message": "Video uploaded successfully",
        "video": video_record
    }


@router.get("", response_model=List[VideoResponse])
def list_videos(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all registered videos."""
    return crud.get_all_videos(db=db, skip=skip, limit=limit)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get single video details by ID."""
    video = crud.get_video_by_id(db=db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
    return video


@router.delete("/{video_id}", status_code=status.HTTP_200_OK)
def delete_video(video_id: int, db: Session = Depends(get_db)):
    """Delete a video and its associated detections and counts."""
    video = crud.get_video_by_id(db=db, video_id=video_id)
    if not video:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")

    # Remove file from disk if exists
    try:
        vpath = Path(video.filepath)
        if vpath.exists():
            vpath.unlink()
    except Exception as e:
        logger.warning(f"Error removing video file from disk: {e}")

    crud.delete_video(db=db, video_id=video_id)
    return {"message": f"Video {video_id} deleted successfully"}


@router.post("/generate-sample", response_model=VideoResponse)
def create_sample_video(db: Session = Depends(get_db)):
    """Generate a synthetic traffic video for instant testing."""
    sample_file = settings.SAMPLE_DIR / "sample_traffic.mp4"
    generate_sample_traffic_video(output_path=sample_file)
    meta = get_video_metadata(sample_file)

    video = crud.create_video(
        db=db,
        filename="sample_traffic.mp4",
        filepath=str(sample_file),
        source_type="sample",
        duration=meta.get("duration", 0.0),
        width=meta.get("width", 0),
        height=meta.get("height", 0),
        fps=meta.get("fps", 0.0),
        total_frames=meta.get("total_frames", 0),
        status="ready"
    )
    return video
