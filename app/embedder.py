"""Face detection and ArcFace embeddings via InsightFace."""
import os
from threading import Lock

import cv2
import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image

MODEL_NAME = os.environ.get("JANUS_MODEL", os.environ.get("FACESEARCH_MODEL", "buffalo_l"))
USE_GPU = os.environ.get("JANUS_DEVICE", os.environ.get("FACESEARCH_DEVICE", "cpu")).lower() in ("cuda", "gpu")
DEVICE_ID = 0 if USE_GPU else -1
PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"] if USE_GPU else ["CPUExecutionProvider"]
DET_SIZE = tuple(int(v) for v in os.environ.get("JANUS_DET_SIZE", "640,640").split(",", 1))
MAX_SIDE = 1600
CROP_FALLBACK_MAX_SIDE = 256
CROP_FALLBACK_MIN_SIDE = 64

_app = None
_app_lock = Lock()


def _get_app():
    global _app
    if _app is None:
        with _app_lock:
            if _app is None:
                app = FaceAnalysis(name=MODEL_NAME, providers=PROVIDERS)
                app.prepare(ctx_id=DEVICE_ID, det_size=DET_SIZE)
                _app = app
    return _app


def _prep(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE))
    return img


def _bgr(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


def _embed_crop(img: Image.Image):
    rec = _get_app().models["recognition"]
    crop = img.resize(rec.input_size, Image.Resampling.BILINEAR)
    emb = rec.get_feat(_bgr(crop)).flatten().astype("float32")
    emb /= np.linalg.norm(emb)
    return emb


def _should_fallback_to_crop(img: Image.Image) -> bool:
    w, h = img.size
    ratio = max(w, h) / max(1, min(w, h))
    return min(w, h) >= CROP_FALLBACK_MIN_SIDE and max(w, h) <= CROP_FALLBACK_MAX_SIDE and ratio <= 2.0


def embed_faces(img: Image.Image, min_prob: float = 0.70, allow_crop_fallback: bool = False):
    """Return [(embedding[512], (x1, y1, x2, y2), probability)] largest face first."""
    img = _prep(img)
    app = _get_app()
    faces = [f for f in app.get(_bgr(img)) if float(f.det_score) >= min_prob]
    if not faces and allow_crop_fallback and _should_fallback_to_crop(img):
        return [(_embed_crop(img), (0.0, 0.0, float(img.width), float(img.height)), 0.0)]
    if not faces:
        return []

    out = []
    for face in faces:
        emb = getattr(face, "normed_embedding", None)
        if emb is None:
            emb = face.embedding / np.linalg.norm(face.embedding)
        box = tuple(float(v) for v in face.bbox)
        out.append((emb.astype("float32"), box, float(face.det_score)))

    return sorted(out, key=lambda item: -((item[1][2] - item[1][0]) * (item[1][3] - item[1][1])))
