# Janus

Janus is a local face-comparison app. Upload two face photos, choose the detected face when an image contains more than one, and Janus compares the selected faces with InsightFace/ArcFace.

Photos are processed in memory and are not stored.

## Run locally

```powershell
.\run_janus.ps1
```

Open:

```text
http://127.0.0.1:8010
```

## Manual install

```powershell
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

## Public tunnel

This project can be exposed from the local PC with Cloudflare Tunnel. The current same-origin frontend setup expects the app and API to share one domain, for example:

```text
https://janus.sentirax.com
```

The local backend serves both:

- UI at `/`
- Health check at `/api/health`
- Detection at `/api/detect`
- Comparison at `/api/compare`

## Settings

Defaults:

- `JANUS_MODEL=buffalo_l`
- `JANUS_MATCH_THRESHOLD=0.5`
- face detection confidence threshold: `0.70`

Optional environment variables:

```powershell
$env:JANUS_MATCH_THRESHOLD="0.5"
$env:JANUS_SCORE_STEEPNESS="18.0"
$env:JANUS_DEVICE="cpu"
```

Use `JANUS_DEVICE=cuda` only when the InsightFace ONNX Runtime CUDA provider is installed.
