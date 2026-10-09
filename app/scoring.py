"""Map ArcFace cosine similarity into Janus verdict tones."""
import math
import os

THRESHOLD = float(os.environ.get("JANUS_MATCH_THRESHOLD", "0.5"))
STEEPNESS = float(os.environ.get("JANUS_SCORE_STEEPNESS", "18.0"))


def confidence(similarity: float) -> int:
    return round(100 / (1 + math.exp(-STEEPNESS * (similarity - THRESHOLD))))


TONE_BANDS = [
    (100, "same_person"),
    (85, "very_high_similarity"),
    (65, "high_similarity"),
    (50, "leans_same"),
    (35, "leans_different"),
    (15, "low_similarity"),
    (1, "very_low_similarity"),
    (0, "different_people"),
]

TONE_TEXT = {
    "en": {
        "same_person": ("Very high similarity", "Janus says it's the same person."),
        "very_high_similarity": ("Very high similarity", "Janus confidently thinks it's the same person."),
        "high_similarity": ("High similarity", "Janus thinks it's the same person."),
        "leans_same": ("Leans toward same person", "Janus leans toward the same person."),
        "leans_different": ("Leans toward different people", "Janus leans toward different people."),
        "low_similarity": ("Low similarity", "Janus thinks they're different people."),
        "very_low_similarity": ("Very low similarity", "Janus confidently thinks they're different people."),
        "different_people": ("Very low similarity", "Janus says they're different people."),
    },
    "tr": {
        "same_person": ("Çok yüksek benzerlik", "Janus aynı kişi olduğunu söylüyor."),
        "very_high_similarity": ("Çok yüksek benzerlik", "Janus aynı kişi olduğundan oldukça emin."),
        "high_similarity": ("Yüksek benzerlik", "Janus aynı kişi olduğunu düşünüyor."),
        "leans_same": ("Aynı kişiye yakın", "Janus aynı kişi olma ihtimaline yakın görüyor."),
        "leans_different": ("Farklı kişilere yakın", "Janus farklı kişiler olma ihtimaline yakın görüyor."),
        "low_similarity": ("Düşük benzerlik", "Janus farklı kişiler olduğunu düşünüyor."),
        "very_low_similarity": ("Çok düşük benzerlik", "Janus farklı kişiler olduğundan oldukça emin."),
        "different_people": ("Çok düşük benzerlik", "Janus farklı kişiler olduğunu söylüyor."),
    },
}


def tone(score: int, lang: str = "en") -> dict:
    """Return a human tone for the 0-100 same-person score."""
    text = TONE_TEXT.get(lang, TONE_TEXT["en"])
    for minimum, name in TONE_BANDS:
        if score >= minimum:
            label, detail = text[name]
            return {"name": name, "label": label, "detail": detail}
    label, detail = text["very_low_similarity"]
    return {"name": "very_low_similarity", "label": label, "detail": detail}


def verdict(score: int) -> str:
    return "same" if score >= 50 else "different"
