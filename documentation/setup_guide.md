# Setup & Installation Guide

## 1. Prerequisites
- Python 3.10+ (Python 3.11 or 3.12 recommended)
- Git
- (Optional) NVIDIA GPU with CUDA 11.8+ or 12.1+ for accelerated inference.

---

## 2. Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/object-counting-system.git
cd object-counting-system
```

### Step 2: Create & Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Running the System

### Run with Default Sample Video
```bash
python main.py
```

### Run with Live Webcam
```bash
python main.py --source 0
```

### Run with Custom Video File
```bash
python main.py --source "path/to/traffic_cctv.mp4"
```

---

## 4. Running Automated Tests

```bash
pytest tests/ -v
```
