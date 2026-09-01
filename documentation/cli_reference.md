# CLI Reference & Options

## Command Line Arguments

```bash
python main.py [OPTIONS]
```

### Options:

| Argument | Type | Default | Description |
|:---|:---|:---|:---|
| `--source` | `str` | `data/samples/sample_traffic.mp4` | Video file path, `0` for webcam, or RTSP URL |
| `--conf` | `float` | `0.35` | YOLOv8 confidence threshold (0.05 to 1.0) |
| `--iou` | `float` | `0.45` | IoU threshold for NMS tracking |
| `--line` | `str` | `0.1,0.5,0.9,0.5` | Normalized line coordinates: `x1,y1,x2,y2` |
| `--direction` | `str` | `bidirectional` | Direction filter: `bidirectional`, `in_only`, `out_only` |
| `--save-output` | `str` | `None` | Optional file path to save annotated output video (`.mp4`) |
| `--no-display` | flag | `False` | Run headless without OpenCV GUI window |
| `--max-frames` | `int` | `None` | Maximum frames to process before exiting |
| `--loop` | flag | `False` | Loop playback continuously when reaching end of video |

---

## Keyboard Shortcuts in OpenCV Window

| Key | Description |
|:---|:---|
| `Q` / `ESC` | Exit application and finalize session |
| `P` / `SPACE` | Pause / Resume playback |
| `R` | Reset count registers to 0 |
| `H` | Toggle on-screen HUD banner |
| `T` | Toggle tracking trails |
| `S` | Save snapshot screenshot to `data/outputs/` |
