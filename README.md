# Janus

Janus is a local face-comparison app. Upload two face photos, choose the detected face when an image contains more than one, and Janus compares the selected faces with InsightFace/ArcFace.

Photos are processed in memory and are not stored.

Try it directly:

```text
https://janus.sentirax.com
```

## Features

- Two-image face comparison
- Multiple-face selection per image
- Face-focused previews
- Cosine similarity scoring
- English and Turkish UI
- Local web UI and FastAPI endpoints

## Requirements

- Python 3.11
- Microsoft C++ Build Tools on Windows

## Install

PowerShell:

```powershell
git clone https://github.com/juliuskalume/facecompare.git
cd facecompare
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
```

Bash:

```bash
git clone https://github.com/juliuskalume/facecompare.git
cd facecompare
python3.11 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt
```

## Run

PowerShell:

```powershell
.\run_janus.ps1
```

Bash:

```bash
./run_janus.sh
```

Open:

```text
http://127.0.0.1:8010
```

## Configuration

Defaults:

- Model: `buffalo_l`
- Match threshold: `0.5`
- Face detection threshold: `0.70`

Optional environment variables:

PowerShell:

```powershell
$env:JANUS_MODEL="buffalo_l"
$env:JANUS_MATCH_THRESHOLD="0.5"
$env:JANUS_SCORE_STEEPNESS="18.0"
$env:JANUS_DEVICE="cpu"
```

Bash:

```bash
export JANUS_MODEL="buffalo_l"
export JANUS_MATCH_THRESHOLD="0.5"
export JANUS_SCORE_STEEPNESS="18.0"
export JANUS_DEVICE="cpu"
```

Use `JANUS_DEVICE=cuda` only when the InsightFace ONNX Runtime CUDA provider is installed.

## API

```text
GET  /api/health
POST /api/detect
POST /api/compare
```

`POST /api/compare` accepts multipart form fields:

- `left`: first image
- `right`: second image
- `left_index`: selected detected face index, default `0`
- `right_index`: selected detected face index, default `0`
- `lang`: `en` or `tr`, default `en`
