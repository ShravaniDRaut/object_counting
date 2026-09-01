# 🎯 AI-Powered Real-Time Object Counting System

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00ffff.svg)](https://ultralytics.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10+-red.svg)](https://opencv.org/)
[![ByteTrack](https://img.shields.io/badge/Tracker-ByteTrack-green.svg)](https://github.com/ifzhang/ByteTrack)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-lightgrey.svg)](https://sqlite.org/)

A high-performance standalone Computer Vision application that detects, tracks, and counts objects in real-time from webcam streams or video files (MP4, AVI, MOV). Powered by **YOLOv8**, **ByteTrack**, and a precision 2D vector-geometry line-crossing engine, the system logs bidirectional traffic (**IN** / **OUT**) directly into an **SQLite** database.

---

## 🌟 Core Features

- 📹 **Multi-Source Input**: Real-time processing for video files (MP4, AVI, MOV) or live webcam feeds (`--source 0`).
- ⚡ **YOLOv8 Object Detection**: High-accuracy real-time detection with automatic CPU/GPU (CUDA/MPS) acceleration.
- 🏷️ **6 Targeted Object Categories**:
  - 🚶 **Person** (Pedestrians)
  - 🚗 **Car** (Automobiles)
  - 🚌 **Bus** (Public Transit)
  - 🚚 **Truck** (Commercial Freight)
  - 🏍️ **Motorcycle** (Two-wheelers)
  - 🚲 **Bicycle** (Cyclists)
- 🆔 **ByteTrack Tracking**: Persistent tracklet ID assignment and motion trajectory trails across video frames.
- 📏 **Precision Line-Crossing Math**: 2D vector segment intersection tests using ground-contact centroid tracking, orientation checking (IN vs OUT), and double-counting prevention cooldowns.
- 🖥️ **Interactive OpenCV Display & Hotkeys**:
  - Live bounding boxes, class labels, and confidence tags
  - Dynamic virtual counting line (pulses red on crossing)
  - Top & bottom on-screen Heads-Up Display (HUD) with FPS and live counts
  - Interactive keyboard shortcuts during playback
- 🗄️ **Relational Database Persistence**: Stores video metadata and line-crossing events into SQLite with SQLAlchemy.

---

## ⌨️ Interactive Keyboard Controls

While the OpenCV video window is active:

| Key | Action |
|:---|:---|
| `Q` / `ESC` | **Quit** application and save session summary |
| `P` / `SPACE` | **Pause / Resume** video playback |
| `R` | **Reset** live counters to zero |
| `H` | **Toggle HUD** on-screen banner visibility |
| `T` | **Toggle Trails** motion history lines |
| `S` | **Save Snapshot** screenshot to `data/outputs/` |

---

## 📐 Architecture & Math

```
[ Video File (MP4, AVI, MOV) / Webcam (0) ]
                     │
                     ▼
       [ cv2.VideoCapture Ingestion ]
                     │
                     ▼
   [ YOLOv8 Inference (Classes: 0,1,2,3,5,7) ]
                     │
                     ▼
  [ ByteTrack Tracker: Persistent IDs & Trajectories ]
                     │
                     ▼
  [ Vector Line-Crossing Counter (Straddle & CCW Test) ]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 [ SQLite Database ]    [ OpenCV Frame Annotator ]
(Videos, Detections,    (BBoxes, Line, Trails, HUD)
  Object Counts)                 │
                                 ▼
                      [ High-Performance GUI ]
```

### Vector Line-Crossing Formula
Given virtual line segment $L = (P_1, P_2)$ and object centroid movement $S = (C_{t-1}, C_t)$:
$$\text{ccw}(A, B, C) = (B_x - A_x)(C_y - A_y) - (B_y - A_y)(C_x - A_x)$$
The object intersects the virtual line if and only if:
$$\text{sign}(\text{ccw}(P_1, P_2, C_{t-1})) \neq \text{sign}(\text{ccw}(P_1, P_2, C_t)) \land \text{sign}(\text{ccw}(C_{t-1}, C_t, P_1)) \neq \text{sign}(\text{ccw}(C_{t-1}, C_t, P_2))$$

---

## 📁 Project Structure

```
object_counting/
├── src/
│   ├── annotator.py      # OpenCV visual rendering (BBoxes, labels, trails, line, HUD)
│   ├── config.py         # Application configuration and .env loading
│   ├── database.py       # SQLite database persistence (videos, detections, counts)
│   ├── detector.py       # YOLOv8 object detector wrapper
│   ├── line_counter.py   # 2D vector geometry line crossing engine
│   ├── logger.py         # Centralized structured logger
│   └── tracker.py        # ByteTrack tracking manager
├── data/
│   ├── outputs/          # Saved video snapshots and recordings
│   └── samples/          # Test videos (e.g. sample_traffic.mp4)
├── models/
│   └── yolov8n.pt        # YOLOv8 neural network weights
├── tests/
│   ├── test_database.py  # SQLite schema & persistence tests
│   └── test_line_counter.py # Vector cross-product & cooldown tests
├── documentation/
│   ├── architecture.md   # System architecture specification
│   ├── cli_reference.md  # CLI command line options
│   └── setup_guide.md    # Environment setup instructions
├── requirements.txt      # Minimal Python dependencies
├── .env.example / .env   # Configuration settings
├── main.py               # Main CLI application runner
└── README.md             # Project documentation
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and set up a Python virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1    # On Windows
# source venv/bin/activate     # On Linux / macOS

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Run with Sample Video
```bash
python main.py
```

### 3. Run with Live Webcam
```bash
python main.py --source 0
```

### 4. Run with Custom Video and Line Coordinates
```bash
python main.py --source path/to/your_video.mp4 --conf 0.40 --line 0.1,0.6,0.9,0.6 --direction bidirectional
```

### 5. Run Headless / Batch Mode
Process a video in background without an OpenCV display window:
```bash
python main.py --source path/to/video.mp4 --no-display
```

---

## 🧪 Testing

Run automated unit and integration tests:
```bash
pytest tests/ -v
```

---

## 📜 License
MIT License. Created for Computer Vision, AI, and Machine Learning portfolios.
