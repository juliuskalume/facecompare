import base64
import io
import os
import time
from typing import Annotated

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except Exception:
    pass

from .embedder import MAX_SIDE, embed_faces
from . import scoring

MAX_UPLOAD = 8 * 1024 * 1024

app = FastAPI(title="Janus Face Compare")

allowed_origins = [
    origin.strip()
    for origin in os.environ.get("JANUS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=bool(allowed_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)

MESSAGES = {
    "en": {
        "too_large": "{name} is larger than 8 MB.",
        "unreadable": "{name} is not a readable image.",
        "no_face": "No clear face found in {side}. Use a well-lit, front-facing photo.",
        "bad_face": "Selected face {index} is not available in {side}.",
        "image": "the image",
        "first": "the first image",
        "second": "the second image",
    },
    "tr": {
        "too_large": "{name} 8 MB'den büyük.",
        "unreadable": "{name} okunabilir bir görsel değil.",
        "no_face": "{side} içinde net bir yüz bulunamadı. İyi aydınlatılmış, önden çekilmiş bir fotoğraf kullanın.",
        "bad_face": "Seçilen yüz {side} içinde mevcut değil: {index}.",
        "image": "görsel",
        "first": "ilk görsel",
        "second": "ikinci görsel",
    },
}


def _lang(lang: str) -> str:
    return "tr" if lang == "tr" else "en"


def _msg(lang: str, key: str, **kwargs) -> str:
    return MESSAGES[_lang(lang)][key].format(**kwargs)


async def _read_image(file: UploadFile, lang: str = "en") -> Image.Image:
    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, _msg(lang, "too_large", name=file.filename or "Image"))
    try:
        return ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
    except UnidentifiedImageError:
        raise HTTPException(400, _msg(lang, "unreadable", name=file.filename or "Image"))


def _display_image(img: Image.Image):
    detection_img = img.convert("RGB")
    if max(detection_img.size) > MAX_SIDE:
        detection_img.thumbnail((MAX_SIDE, MAX_SIDE))
    return detection_img


def _detection_size(img: Image.Image):
    detection_img = _display_image(img)
    return detection_img.size


def _preview_data_url(img: Image.Image):
    buf = io.BytesIO()
    _display_image(img).save(buf, format="JPEG", quality=88, optimize=True)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def _face_payload(face, width: int, height: int, index: int):
    _, box, probability = face
    box = [round(float(v), 2) for v in box]
    x1, y1, x2, y2 = box
    center_x = round(((x1 + x2) / 2) / max(1, width) * 100, 2)
    center_y = round(((y1 + y2) / 2) / max(1, height) * 100, 2)
    return {
        "index": index,
        "box": box,
        "image_size": {"width": width, "height": height},
        "det_score": round(float(probability), 4),
        "object_position": {"x": center_x, "y": center_y},
    }


def _faces_or_error(img: Image.Image, side: str, lang: str = "en"):
    width, height = _detection_size(img)
    faces = embed_faces(img, allow_crop_fallback=True)
    if not faces:
        raise HTTPException(422, _msg(lang, "no_face", side=side))
    return faces, width, height


def _selected_face_or_error(img: Image.Image, side: str, index: int = 0, lang: str = "en"):
    faces, width, height = _faces_or_error(img, side, lang)
    if index < 0 or index >= len(faces):
        raise HTTPException(400, _msg(lang, "bad_face", side=side, index=index + 1))
    emb, _, _ = faces[index]
    payload = _face_payload(faces[index], width, height, index)
    return {
        "embedding": emb,
        **payload,
        "faces_found": len(faces),
        "selected_index": index,
    }


@app.get("/api/health")
def health():
    return {"ok": True, "model": "InsightFace ArcFace", "threshold": scoring.THRESHOLD}


@app.post("/api/detect")
async def detect(file: Annotated[UploadFile, File(...)], lang: Annotated[str, Form()] = "en"):
    lang = _lang(lang)
    img = await _read_image(file, lang)
    faces, width, height = _faces_or_error(img, _msg(lang, "image"), lang)
    payloads = [_face_payload(face, width, height, index) for index, face in enumerate(faces)]
    first = payloads[0]
    return {
        "faces_found": len(faces),
        "det_score": first["det_score"],
        "box": first["box"],
        "image_size": first["image_size"],
        "object_position": first["object_position"],
        "selected_index": 0,
        "faces": payloads,
        "preview_data_url": _preview_data_url(img),
    }


@app.post("/api/compare")
async def compare(
    left: Annotated[UploadFile, File(...)],
    right: Annotated[UploadFile, File(...)],
    left_index: Annotated[int, Form()] = 0,
    right_index: Annotated[int, Form()] = 0,
    lang: Annotated[str, Form()] = "en",
):
    lang = _lang(lang)
    started = time.perf_counter()
    left_img, right_img = await _read_image(left, lang), await _read_image(right, lang)
    left_face = _selected_face_or_error(left_img, _msg(lang, "first"), left_index, lang)
    right_face = _selected_face_or_error(right_img, _msg(lang, "second"), right_index, lang)

    similarity = float(np.dot(left_face["embedding"], right_face["embedding"]))
    confidence = scoring.confidence(similarity)
    tone = scoring.tone(confidence, lang)
    verdict = scoring.verdict(confidence)

    return {
        "verdict": verdict,
        "tone": tone["name"],
        "label": tone["label"],
        "detail": tone["detail"],
        "same_person": verdict == "same",
        "needs_review": verdict == "review",
        "confidence": confidence,
        "similarity": round(similarity, 4),
        "threshold": scoring.THRESHOLD,
        "faces": {
            "left": {k: v for k, v in left_face.items() if k != "embedding"},
            "right": {k: v for k, v in right_face.items() if k != "embedding"},
        },
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")


