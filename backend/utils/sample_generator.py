"""
Synthetic Test Video Generator.
Generates a realistic mock traffic scene video with simulated vehicles and pedestrians
crossing a virtual boundary. Allows instantaneous verification and testing without
needing a physical camera or external video downloads.
"""
from pathlib import Path
import cv2
import numpy as np

from backend.config import settings
from backend.logger import logger


def generate_sample_traffic_video(
    output_path: Path = settings.SAMPLE_DIR / "sample_traffic.mp4",
    duration_sec: int = 10,
    fps: int = 25,
    width: int = 800,
    height: int = 600
) -> Path:
    """
    Generates a synthetic traffic video with animated vehicles and pedestrians crossing
    a road line to test object detection, tracking, and counting.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Attempt to download real benchmark video for realistic detection
    benchmark_url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4"
    try:
        import urllib.request
        logger.info(f"Fetching benchmark video from {benchmark_url}...")
        urllib.request.urlretrieve(benchmark_url, str(output_path))
        logger.info(f"Benchmark video saved to {output_path}")
        return output_path
    except Exception as e:
        logger.warning(f"Could not download benchmark video ({e}); generating synthetic video...")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    total_frames = duration_sec * fps
    logger.info(f"Generating synthetic traffic video: {total_frames} frames at {output_path}")

    # Simulated objects with starting positions, speeds, colors, and types
    objects = [
        # Cars moving downward (Southbound, crossing line downwards: direction OUT/IN)
        {"type": "car", "x": 260, "y": -80, "speed_y": 6, "speed_x": 0, "w": 70, "h": 120, "color": (50, 50, 220), "label": "Car"},
        {"type": "car", "x": 270, "y": -350, "speed_y": 7, "speed_x": 0, "w": 75, "h": 130, "color": (200, 50, 50), "label": "Car"},
        {"type": "truck", "x": 160, "y": -220, "speed_y": 5, "speed_x": 0, "w": 90, "h": 180, "color": (150, 150, 150), "label": "Truck"},
        {"type": "bus", "x": 150, "y": -550, "speed_y": 4, "speed_x": 0, "w": 100, "h": 220, "color": (20, 160, 240), "label": "Bus"},
        
        # Vehicles moving upward (Northbound)
        {"type": "car", "x": 480, "y": height + 100, "speed_y": -6, "speed_x": 0, "w": 70, "h": 120, "color": (40, 200, 40), "label": "Car"},
        {"type": "motorcycle", "x": 600, "y": height + 250, "speed_y": -8, "speed_x": 0, "w": 40, "h": 70, "color": (0, 215, 255), "label": "Motorcycle"},
        {"type": "car", "x": 500, "y": height + 480, "speed_y": -6, "speed_x": 0, "w": 70, "h": 120, "color": (220, 180, 50), "label": "Car"},

        # Pedestrians crossing horizontally / vertically on sidewalk
        {"type": "person", "x": 60, "y": height + 50, "speed_y": -2.5, "speed_x": 0, "w": 30, "h": 60, "color": (180, 100, 220), "label": "Person"},
        {"type": "person", "x": 720, "y": -60, "speed_y": 2.5, "speed_x": 0, "w": 30, "h": 60, "color": (220, 120, 100), "label": "Person"},
        {"type": "bicycle", "x": 680, "y": height + 80, "speed_y": -4, "speed_x": 0, "w": 35, "h": 70, "color": (100, 220, 180), "label": "Bicycle"},
    ]

    for f in range(total_frames):
        # 1. Draw Road Background
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Asphalt roadway
        frame[:, :] = (45, 45, 48)

        # Sidewalks
        frame[:, 0:110] = (90, 95, 100)      # West sidewalk
        frame[:, width - 110:] = (90, 95, 100) # East sidewalk

        # Road curbs
        cv2.line(frame, (110, 0), (110, height), (220, 220, 220), 3)
        cv2.line(frame, (width - 110, 0), (width - 110, height), (220, 220, 220), 3)

        # Double yellow center divider line
        cv2.line(frame, (width // 2 - 3, 0), (width // 2 - 3, height), (0, 215, 255), 2)
        cv2.line(frame, (width // 2 + 3, 0), (width // 2 + 3, height), (0, 215, 255), 2)

        # Dashed lane markings
        dash_len = 30
        dash_gap = 25
        for y_dash in range(0, height, dash_len + dash_gap):
            cv2.line(frame, (280, y_dash), (280, y_dash + dash_len), (220, 220, 220), 2)
            cv2.line(frame, (520, y_dash), (520, y_dash + dash_len), (220, 220, 220), 2)

        # Pedestrian Crosswalk stripes near middle (y: 280 to 320)
        stripe_width = 30
        for x_stripe in range(120, width - 120, 50):
            cv2.rectangle(frame, (x_stripe, 285), (x_stripe + stripe_width, 315), (240, 240, 240), -1)

        # 2. Update and Draw Moving Objects
        for obj in objects:
            obj["y"] += obj["speed_y"]
            obj["x"] += obj["speed_x"]

            ox = int(obj["x"])
            oy = int(obj["y"])
            ow = obj["w"]
            oh = obj["h"]

            # Only draw if visible on screen
            if -oh <= oy <= height + oh and -ow <= ox <= width + ow:
                color = obj["color"]

                if obj["type"] in ["car", "truck", "bus"]:
                    # Draw Vehicle Body
                    cv2.rectangle(frame, (ox - ow // 2, oy - oh // 2), (ox + ow // 2, oy + oh // 2), color, -1)
                    # Vehicle Windshield & Roof
                    cv2.rectangle(frame, (ox - ow // 2 + 5, oy - oh // 4), (ox + ow // 2 - 5, oy + oh // 4), (30, 30, 30), -1)
                    # Headlights
                    if obj["speed_y"] > 0:
                        cv2.circle(frame, (ox - ow // 2 + 8, oy + oh // 2 - 5), 4, (200, 255, 255), -1)
                        cv2.circle(frame, (ox + ow // 2 - 8, oy + oh // 2 - 5), 4, (200, 255, 255), -1)
                    else:
                        cv2.circle(frame, (ox - ow // 2 + 8, oy - oh // 2 + 5), 4, (200, 255, 255), -1)
                        cv2.circle(frame, (ox + ow // 2 - 8, oy - oh // 2 + 5), 4, (200, 255, 255), -1)

                elif obj["type"] == "person":
                    # Head
                    cv2.circle(frame, (ox, oy - oh // 2 + 10), 10, (230, 190, 170), -1)
                    # Torso
                    cv2.rectangle(frame, (ox - 10, oy - oh // 2 + 20), (ox + 10, oy + oh // 2), color, -1)

                elif obj["type"] == "motorcycle" or obj["type"] == "bicycle":
                    # Wheels & Body
                    cv2.circle(frame, (ox, oy - oh // 3), 8, (20, 20, 20), -1)
                    cv2.circle(frame, (ox, oy + oh // 3), 8, (20, 20, 20), -1)
                    cv2.line(frame, (ox, oy - oh // 3), (ox, oy + oh // 3), color, 4)

        out.write(frame)

    out.release()
    logger.info(f"Sample video created successfully: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_sample_traffic_video()
