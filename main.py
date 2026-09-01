"""
AI-Powered Real-Time Object Counting System - Main CLI Entrypoint.
Executes YOLOv8 object detection, ByteTrack tracking, and virtual line counting.
"""
import sys
import os
import subprocess
from pathlib import Path

# Automatically hand off to project virtual environment if available
_venv_py = Path(__file__).resolve().parent / "venv" / "Scripts" / "python.exe"
if _venv_py.exists() and Path(sys.executable).resolve() != _venv_py.resolve():
    os.environ["VIRTUAL_ENV"] = str(_venv_py.parent.parent)
    sys.exit(subprocess.call([str(_venv_py)] + sys.argv))

import argparse
import time
import cv2
import numpy as np

from src.config import cfg
from src.logger import logger
from src.database import db
from src.tracker import ByteTrackerManager
from src.line_counter import LineCrossingCounter
from src.annotator import FrameAnnotator


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI-Powered Real-Time Object Counting System (YOLOv8 + ByteTrack + OpenCV)"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="data/samples/sample_traffic.mp4",
        help="Input source: video file path (MP4, AVI, MOV), '0' for live webcam, or sample video"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=cfg.CONFIDENCE_THRESHOLD,
        help="Confidence threshold for YOLOv8 object detection (default: 0.35)"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=cfg.IOU_THRESHOLD,
        help="IoU threshold for NMS tracking (default: 0.45)"
    )
    parser.add_argument(
        "--line",
        type=str,
        default=f"{cfg.LINE_START_X},{cfg.LINE_START_Y},{cfg.LINE_END_X},{cfg.LINE_END_Y}",
        help="Normalized line coordinates 'x1,y1,x2,y2' (default: 0.1,0.5,0.9,0.5)"
    )
    parser.add_argument(
        "--direction",
        type=str,
        choices=["bidirectional", "in_only", "out_only"],
        default="bidirectional",
        help="Counting direction mode"
    )
    parser.add_argument(
        "--save-output",
        type=str,
        default=None,
        help="Optional path to save annotated output video (.mp4)"
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Run headless without showing OpenCV GUI window"
    )
    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Maximum frames to process before exiting"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop video playback when it reaches the end"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info("=" * 60)
    logger.info(f"Starting {cfg.APP_NAME} v{cfg.APP_VERSION}")
    logger.info("=" * 60)

    # 1. Resolve Input Source
    source_val = args.source
    is_webcam = source_val.isdigit()
    source_input = int(source_val) if is_webcam else source_val

    # Auto-generate or download sample if default sample does not exist
    if not is_webcam and not Path(source_input).exists():
        logger.info(f"Input file '{source_input}' not found. Generating sample traffic video...")
        from urllib.request import urlretrieve
        sample_path = Path(source_input)
        sample_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
            urlretrieve(url, str(sample_path))
            logger.info("Sample video prepared.")
        except Exception as e:
            logger.warning(f"Could not download sample video ({e}).")

    cap = cv2.VideoCapture(source_input)
    if not cap.isOpened():
        logger.error(f"Cannot open video source: {args.source}")
        sys.exit(1)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
    duration = total_frames / source_fps if source_fps > 0 else 0.0

    logger.info(f"Source: {args.source} | Resolution: {width}x{height} | FPS: {source_fps:.1f}")

    # 2. Register Video In Database
    video_rec = db.create_video_record(
        source=str(args.source),
        source_type="webcam" if is_webcam else "video",
        duration=round(duration, 2),
        width=width,
        height=height,
        fps=round(source_fps, 2),
        total_frames=total_frames
    )
    video_id = video_rec.id

    # 3. Parse Line Coordinates
    try:
        coords = [float(x.strip()) for x in args.line.split(",")]
        norm_start = (coords[0], coords[1])
        norm_end = (coords[2], coords[3])
    except Exception:
        norm_start = (cfg.LINE_START_X, cfg.LINE_START_Y)
        norm_end = (cfg.LINE_END_X, cfg.LINE_END_Y)

    px_line_start = (int(norm_start[0] * width), int(norm_start[1] * height))
    px_line_end = (int(norm_end[0] * width), int(norm_end[1] * height))

    # 4. Initialize ML Components
    tracker = ByteTrackerManager(
        conf_thresh=args.conf,
        iou_thresh=args.iou
    )
    counter = LineCrossingCounter(
        line_start=px_line_start,
        line_end=px_line_end,
        direction_mode=args.direction
    )
    annotator = FrameAnnotator()

    # Optional Video Writer for output recording
    writer = None
    if args.save_output:
        out_path = Path(args.save_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, source_fps, (width, height))
        logger.info(f"Recording annotated output to: {out_path}")

    # Window Setup
    window_name = f"{cfg.APP_NAME} - YOLOv8 + ByteTrack"
    if not args.no_display:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, min(1280, width), min(720, height))

    frame_idx = 0
    fps = 0.0
    prev_time = time.time()
    is_paused = False

    logger.info("Inference loop running. Press [Q] to quit, [P] to pause, [R] to reset, [S] to snapshot.")

    try:
        while True:
            if not is_paused:
                ret, frame = cap.read()
                if not ret:
                    if args.loop and not is_webcam:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        logger.info("End of video stream reached.")
                        break

                frame_idx += 1
                if args.max_frames and frame_idx > args.max_frames:
                    break

                # FPS smoothing
                now = time.time()
                dt = now - prev_time
                if dt > 0:
                    inst_fps = 1.0 / dt
                    fps = 0.9 * fps + 0.1 * inst_fps if fps > 0 else inst_fps
                prev_time = now

                # 1. ByteTrack Tracking
                tracked_objects = tracker.track(frame)
                has_crossing = False

                # 2. Line Crossing Test
                for obj in tracked_objects:
                    event = counter.process_track(
                        track_id=obj["track_id"],
                        centroid=obj["bottom_center"],
                        class_name=obj["class_name"],
                        frame_idx=frame_idx,
                        confidence=obj["confidence"]
                    )
                    if event:
                        has_crossing = True
                        # Persist to SQLite
                        db.log_crossing(
                            track_id=event["track_id"],
                            class_name=event["class_name"],
                            direction=event["direction"],
                            video_id=video_id
                        )
                        logger.info(
                            f"Crossing Detected -> Track #{event['track_id']} | "
                            f"{event['class_name'].capitalize()} | {event['direction']} | Frame: {frame_idx}"
                        )

                # In-frame object type breakdown
                in_frame_classes = {}
                for obj in tracked_objects:
                    cname = obj["class_name"]
                    in_frame_classes[cname] = in_frame_classes.get(cname, 0) + 1

                # 3. Frame Annotation
                stats = {
                    "fps": fps,
                    "frame_idx": frame_idx,
                    "in_frame_count": len(tracked_objects),
                    "in_frame_classes": in_frame_classes,
                    "total_unique_detected": counter.total_unique_detected,
                    "cumulative_class_counts": counter.cumulative_class_counts,
                    "total_in": counter.total_in,
                    "total_out": counter.total_out,
                    "total_crossed": counter.total_in + counter.total_out,
                    "class_counts": counter.class_counts
                }

                annotated = annotator.annotate(
                    frame=frame,
                    tracked_objects=tracked_objects,
                    track_histories=counter.track_histories,
                    line_start=px_line_start,
                    line_end=px_line_end,
                    has_new_crossing=has_crossing,
                    stats=stats
                )

                if writer:
                    writer.write(annotated)

                if not args.no_display:
                    cv2.imshow(window_name, annotated)

            # Keyboard Input Handling
            key = cv2.waitKey(1 if not is_paused else 30) & 0xFF

            if key in [ord("q"), 27]:  # 'q' or ESC
                logger.info("Exit requested by user.")
                break
            elif key in [ord("p"), 32]:  # 'p' or SPACE
                is_paused = not is_paused
                status_str = "PAUSED" if is_paused else "RESUMED"
                logger.info(f"Stream {status_str}")
            elif key == ord("r"):  # 'r'
                counter.reset_counts()
                logger.info("Counters reset to 0.")
            elif key == ord("h"):  # 'h'
                annotator.show_hud = not annotator.show_hud
            elif key == ord("t"):  # 't'
                annotator.show_trails = not annotator.show_trails
            elif key == ord("s"):  # 's'
                snap_path = cfg.OUTPUT_DIR / f"snapshot_frame_{frame_idx}.jpg"
                cv2.imwrite(str(snap_path), annotated)
                logger.info(f"Snapshot saved: {snap_path}")

    finally:
        cap.release()
        if writer:
            writer.release()
        if not args.no_display:
            cv2.destroyAllWindows()

        # Save Final Session Analytics to SQLite
        summary = db.get_summary_stats(video_id=video_id)
        import json
        db.save_analytics_snapshot(
            total_in=counter.total_in,
            total_out=counter.total_out,
            person_count=summary["person_count"],
            vehicle_count=summary["vehicle_count"],
            avg_fps=round(fps, 2),
            video_id=video_id,
            class_counts_json=json.dumps(counter.class_counts)
        )

        logger.info("=" * 60)
        logger.info("Session Completed Successfully!")
        logger.info(f"Total Unique Objects Detected: {counter.total_unique_detected}")
        logger.info(f"Unique Objects by Category: {counter.cumulative_class_counts}")
        logger.info(f"Total Line Crossings: {counter.total_in + counter.total_out} (IN: {counter.total_in} | OUT: {counter.total_out})")
        logger.info(f"Crossings by Category: {counter.class_counts}")
        logger.info(f"Database Record ID: {video_id}")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()
