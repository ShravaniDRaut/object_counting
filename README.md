# 🎯 AI-Powered Real-Time Object Counting System

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00ffff.svg)](https://ultralytics.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10+-red.svg)](https://opencv.org/)
[![SQLite](https://img.shields.io/badge/Database-SQLite%20%2F%20SQLAlchemy-lightgrey.svg)](https://sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

A production-grade Computer Vision web application that detects, tracks, and counts objects in real time from video files, webcam streams, or CCTV footage. Powered by **YOLOv8**, **ByteTrack**, and a vector-geometry line crossing algorithm, the system logs bidirectional traffic (IN / OUT) into an SQLite database and renders live analytics with **Plotly**.

---

## 🌟 Core Features

- 📹 **Multi-Source Input**: Real-time processing for uploaded videos (MP4, AVI, MOV), live webcams, or synthetic traffic simulations.
- ⚡ **YOLOv8 Real-Time Inference**: High-accuracy object detection optimized for both CPU and GPU (CUDA/MPS).
- 🏷️ **6 Targeted Object Categories**:
  - 🚶 **Person** (Pedestrians)
  - 🚗 **Car** (Automobiles)
  - 🚌 **Bus** (Public Transit)
  - 🚚 **Truck** (Commercial Freight)
  - 🏍️ **Motorcycle** (Two-wheelers)
  - 🚲 **Bicycle** (Cyclists)
- 🆔 **ByteTrack Tracking**: Persistent tracklet ID assignment and motion trail visualization across frames.
- 📏 **Precision Line-Crossing Math**: 2D vector segment intersection tests with ground-contact centroid tracking, orientation checking (IN vs OUT), and double-counting prevention cooldowns.
- 🎛️ **Dynamic Calibration**: Reposition the virtual counting line and adjust detection confidence in real time directly from the web UI.
- 📊 **Interactive Analytics Dashboard**:
  - Live metric cards (Total In, Total Out, Net Crossings, FPS)
  - Category breakdown distribution (Donut chart via Plotly.js)
  - Directional traffic comparison (IN vs OUT bar chart)
  - Time-series crossing density timeline
- 📥 **CSV Reporting**: One-click download of audit event logs and categorized summaries.
- 🗄️ **Relational Database**: Four structured SQLite/SQLAlchemy tables (`videos`, `detections`, `object_counts`, `analytics`).
- 🐳 **Deployment Ready**: Fully containerized with Docker & Docker Compose.

---

## 📐 Architecture & Math

```
[ Video / Webcam / RTSP ]
           │
           ▼
[ Frame Ingestion: VideoStreamSource ]
           │
           ▼
[ YOLOv8 Object Detection (Classes: 0,1,2,3,5,7) ]
           │
           ▼
[ ByteTrack: Persistent ID & Centroid Estimation ]
           │
           ▼
[ Vector Line-Crossing Counter (Straddle & CCW Test) ]
           │
     ┌─────┴────────────────────────────┐
     ▼                                  ▼
[ SQLite Database ]            [ Visual Frame Annotator ]
(Detections & Counts)          (BBoxes, Trails, Counting Line)
     │                                  │
     ▼                                  ▼
[ Plotly Analytics & CSV ]     [ MJPEG HTTP Live Stream ]
                                        │
                                        ▼
                           [ Responsive Web Dashboard ]
```

### Line-Crossing Geometry
Given a virtual line $L = (P_1, P_2)$ and an object moving between frame centroids $C_{t-1}$ and $C_t$:
$$\text{ccw}(A, B, C) = (B_x - A_x)(C_y - A_y) - (B_y - A_y)(C_x - A_x)$$
A crossing occurs if and only if the trajectories straddle:
$$\text{sign}(\text{ccw}(P_1, P_2, C_{t-1})) \neq \text{sign}(\text{ccw}(P_1, P_2, C_t)) \land \text{sign}(\text{ccw}(C_{t-1}, C_t, P_1)) \neq \text{sign}(\text{ccw}(C_{t-1}, C_t, P_2))$$

---

## 📁 Project Structure

```
object_counting/
├── backend/
│   ├── api/                   # FastAPI routes (stream, video, analytics, reports)
│   ├── database/              # SQLAlchemy models, connection, and CRUD ops
│   ├── ml/                    # YOLOv8 detector, ByteTrack tracker, Line counter
│   ├── schemas/               # Pydantic data schemas
│   ├── utils/                 # Video probe & synthetic traffic video generator
│   ├── config.py              # Centralized environment settings
│   ├── logger.py              # Structured logging
│   └── main.py                # FastAPI app entrypoint
├── frontend/
│   ├── static/                # CSS styling, Plotly charts, and client-side logic
│   └── templates/index.html   # Modern responsive dark-theme dashboard
├── data/
│   ├── uploads/               # Uploaded video storage
│   ├── samples/               # Synthetic traffic test videos
│   └── exports/               # Generated CSV reports
├── models/                    # YOLOv8 model weights (auto-cached)
├── tests/                     # Unit & integration test suite
├── documentation/             # Architecture, API reference, and setup guides
├── Dockerfile                 # Docker container specification
├── docker-compose.yml         # Container orchestration
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # Project overview and documentation
```

---

## 🚀 Quickstart Guide

### 1. Installation
Clone the repository and create an isolated virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1    # On Windows
# source venv/bin/activate     # On Linux / macOS

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to:
- **Dashboard**: `http://localhost:8000`
- **Interactive Swagger API Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing

Execute automated unit and integration tests:
```bash
pytest tests/ -v
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build -d
```
Access at `http://localhost:8000`.

---

## 📜 License
MIT License. Built for Computer Vision & AI Engineering portfolios.
