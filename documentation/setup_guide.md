# Setup & Installation Guide

## 1. Prerequisites
- Python 3.10+ (Recommended: Python 3.11 or 3.12)
- Git
- (Optional) NVIDIA GPU with CUDA 11.8+ or 12.1+ for accelerated inference.

---

## 2. Quickstart (Local Environment)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/object-counting-system.git
cd object-counting-system
```

### Step 2: Create and Activate Virtual Environment
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

### Step 4: Run the Application
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser and navigate to:
```
http://localhost:8000
```

---

## 3. Docker Deployment

To launch the system using Docker and Docker Compose:
```bash
docker-compose up --build -d
```
Access the application at `http://localhost:8000`.

To stop the container:
```bash
docker-compose down
```

---

## 4. Testing

Run the test suite using pytest:
```bash
pytest tests/ -v
```
