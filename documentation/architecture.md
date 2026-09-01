# System Architecture & Technical Specifications

## High-Level Architecture Overview

VisionCount AI is designed as a modular, low-latency computer vision pipeline paired with a high-throughput asynchronous web application.

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Layer                          │
│   (HTML5 + Tailwind CSS + Plotly.js Interactive Dashboard)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / MJPEG Stream
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Web Application                  │
│  - StreamManager (Thread-safe MJPEG frame generator)        │
│  - Video Management API (Upload, metadata, probing)         │
│  - Analytics API (Plotly-ready JSON endpoints)              │
│  - Reports API (Streaming CSV exporter)                     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Frame & Event Pipeline
┌──────────────────────────────▼──────────────────────────────┐
│                  Computer Vision Pipeline                   │
│  - Frame Capture (VideoStreamSource: MP4 / AVI / Webcam)    │
│  - YOLOv8 Detector (ultralytics PyTorch neural network)     │
│  - ByteTracker (Persistent tracking & tracklet association) │
│  - LineCrossingCounter (Vector 2D segment intersection)    │
│  - Visual Annotator (BBoxes, Trails, HUD Overlay)           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Async Event Dispatch
┌──────────────────────────────▼──────────────────────────────┐
│                   Database & Analytics                      │
│  - SQLite Engine via SQLAlchemy ORM                         │
│  - Tables: videos, detections, object_counts, analytics     │
│  - Pandas aggregation engine for statistical reporting      │
└─────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Vision Pipeline (`backend/ml/pipeline.py`)
- Coordinates the ingestion of raw frames from local files, IP cameras, or USB webcams.
- Maintains rolling FPS calculations using moving average smoothing:
  $$\text{FPS}_{t} = 0.9 \cdot \text{FPS}_{t-1} + 0.1 \cdot \left(\frac{1}{\Delta t}\right)$$
- Passes bounding boxes, track IDs, and ground contact points to the line counter.
- Annotates frames with high-contrast color palettes and status overlays.

### 2. Line Crossing Engine (`backend/ml/line_counter.py`)
- Employs 2D vector cross-product geometry:
  $$\text{ccw}(A, B, C) = (B_x - A_x)(C_y - A_y) - (B_y - A_y)(C_x - A_x)$$
- Segment intersection condition:
  $$\text{straddle}(AB, CD) \iff \text{sign}(\text{ccw}(A, C, D)) \neq \text{sign}(\text{ccw}(B, C, D)) \land \text{sign}(\text{ccw}(A, B, C)) \neq \text{sign}(\text{ccw}(A, B, D))$$
- Direction determination:
  Evaluates the sign transition of the object centroid relative to the oriented line vector $\vec{L} = P_{end} - P_{start}$.
- Double-counting prevention:
  Maintains a frame-cooldown window (e.g., 60 frames) and track ID register to prevent jitter along boundary edges.

### 3. Database Layer (`backend/database/`)
- Relational schema mapping:
  - `videos`: Master video files and stream metadata.
  - `detections`: Per-frame object spatial coordinates.
  - `object_counts`: Distinct line-crossing events with timestamps and directions.
  - `analytics`: Periodically sampled system throughput and density metrics.
