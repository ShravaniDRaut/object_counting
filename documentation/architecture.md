# System Architecture - Standalone Computer Vision System

## Architecture Overview

VisionCount AI is a pure, standalone Computer Vision application designed for high-throughput, low-latency video and webcam processing.

```
┌─────────────────────────────────────────────────────────────┐
│                 Video Ingestion & Hardware                  │
│       - Local video file (MP4, AVI, MOV)                    │
│       - USB Webcam or CCTV IP Camera stream (Index / RTSP)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ cv2.VideoCapture (Frame Loop)
┌──────────────────────────────▼──────────────────────────────┐
│                  Machine Learning Pipeline                  │
│  - YOLOv8 (ultralytics): Person, Car, Bus, Truck, Moto, Bike│
│  - ByteTrack Tracker: Persistent IDs & Trajectory History   │
│  - LineCrossingCounter: 2D Vector Straddle & CCW Test       │
└──────────────────────────────┬──────────────────────────────┘
                               │ Crossings & Detections
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
┌─────────────────────────────┐             ┌─────────────────┐
│     OpenCV Annotator        │             │ SQLite Database │
│ - Bounding Boxes & Tags     │             │ - videos        │
│ - Movement Trails           │             │ - detections    │
│ - Counting Line             │             │ - object_counts │
│ - On-screen HUD Overlay     │             │ - analytics     │
└──────────────┬──────────────┘             └────────┬────────┘
               │                                     │
               ▼                                     ▼
      [ cv2.imshow GUI ]                  [ CSV & Plotly Reports ]
      (Key controls: Q,P,R,E,A)           - events.csv
                                          - summary.csv
                                          - dashboard.html
```

## Mathematical Modeling

### Vector Line-Crossing
Given a counting segment $L = (P_1, P_2)$ and an object moving between frame positions $C_{prev}$ and $C_{curr}$:
$$\text{ccw}(A, B, C) = (B_x - A_x)(C_y - A_y) - (B_y - A_y)(C_x - A_x)$$
The object intersects the line segment if:
$$\text{sign}(\text{ccw}(P_1, P_2, C_{prev})) \neq \text{sign}(\text{ccw}(P_1, P_2, C_{curr})) \land \text{sign}(\text{ccw}(C_{prev}, C_{curr}, P_1)) \neq \text{sign}(\text{ccw}(C_{prev}, C_{curr}, P_2))$$

### Direction Determination
Direction is evaluated based on the sign of the normal orientation relative to the directed vector $\vec{L} = P_2 - P_1$:
- Transition from negative to positive $\implies$ **IN**
- Transition from positive to negative $\implies$ **OUT**
