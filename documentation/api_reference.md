# API Reference Documentation

Base URL: `http://localhost:8000`

---

## 1. Video Management Endpoints

### `POST /api/videos/upload`
Uploads a video file for processing.
- **Content-Type**: `multipart/form-data`
- **Body**: `file`: File (MP4, AVI, MOV)
- **Response**: `201 Created`
```json
{
  "message": "Video uploaded successfully",
  "video": {
    "id": 1,
    "filename": "traffic_intersection.mp4",
    "filepath": "data/uploads/upload_traffic_intersection.mp4",
    "duration": 45.2,
    "width": 1920,
    "height": 1080,
    "fps": 30.0,
    "status": "ready"
  }
}
```

### `GET /api/videos`
Returns all registered and uploaded videos.

### `DELETE /api/videos/{video_id}`
Deletes a video and cascading detection records.

### `POST /api/videos/generate-sample`
Generates a deterministic synthetic traffic video for testing.

---

## 2. Real-Time Streaming & Controls

### `GET /api/stream/feed`
Live MJPEG stream of processed frames with bounding boxes, tracking trails, and live HUD.
- **Content-Type**: `multipart/x-mixed-replace; boundary=frame`

### `POST /api/stream/start`
Starts detection stream on the selected video source.
- **Body**:
```json
{
  "source_type": "sample",
  "video_id": null,
  "webcam_index": 0,
  "confidence_threshold": 0.35,
  "iou_threshold": 0.45,
  "line_config": {
    "line_start_x": 0.1,
    "line_start_y": 0.5,
    "line_end_x": 0.9,
    "line_end_y": 0.5,
    "direction_mode": "bidirectional"
  }
}
```

### `POST /api/stream/stop`
Stops the current stream and releases capture hardware.

### `GET /api/stream/stats`
Retrieves live inference counts and active tracks.
- **Response**:
```json
{
  "is_active": true,
  "source_type": "sample",
  "fps": 28.5,
  "current_frame": 142,
  "total_in": 12,
  "total_out": 8,
  "total_count": 20,
  "person_count": 5,
  "vehicle_count": 15,
  "active_tracks_count": 4,
  "class_counts": {
    "car": { "IN": 8, "OUT": 5, "TOTAL": 13 },
    "person": { "IN": 4, "OUT": 1, "TOTAL": 5 }
  }
}
```

### `POST /api/stream/line-config`
Calibrates counting line coordinates in real time without restarting the pipeline.

### `POST /api/stream/reset-counts`
Resets the count registers to 0.

---

## 3. Analytics & Plotly Endpoints

### `GET /api/analytics/summary`
Returns cumulative counting totals, class breakdown, and recent crossings.

### `GET /api/analytics/plotly-data`
Returns pre-formatted datasets ready for client-side Plotly.js charts (donut, bar, timeline).

### `POST /api/analytics/clear`
Clears historical detections and counting records.

---

## 4. Reports & Data Export

### `GET /api/reports/export-csv`
Downloads a detailed CSV file of every individual line-crossing event.

### `GET /api/reports/export-summary-csv`
Downloads a categorized CSV summary of all object totals.
