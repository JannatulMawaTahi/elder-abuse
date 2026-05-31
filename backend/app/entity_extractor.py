"""
Entity Extractor — pull structured info from an elder-abuse complaint.

Extracts (when present in the complaint):
    reporter_type, victim_name, victim_age, victim_gender, location,
    abuser_name, abuser_relation, incident_date

Powered by Gemini (handles Bangla, English, Mixed, and Whisper typos).
Anything not stated in the complaint comes back as null — the frontend form
(Phase 4) lets the user fill in what they know.

Two ways to use:
    1. Standalone: entity_extractor.extract(text)  → its own Gemini call
    2. Shared:     rag_engine reuses normalize_entities() + ENTITY_FIELDS so the
       main pipeline gets entities from ONE combined Gemini call (saves quota).
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


# ── Constants ─────────────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"

REPORTER_TYPES = {"self", "third_party", "unknown"}

ENTITY_FIELDS = (
    "reporter_type",
    "victim_name",
    "victim_age",
    "victim_gender",
    "location",
    "abuser_name",
    "abuser_relation",
    "incident_date",
)


# ── Exceptions ────────────────────────────────────────────────────────────────
class EntityExtractorError(Exception):
    pass


class EntityKeyMissingError(EntityExtractorError):
    pass


class EntityAPIError(EntityExtractorError):
    pass


# ── Shared helpers (also used by rag_engine) ──────────────────────────────────
def empty_entities() -> dict[str, Any]:
    """A fully-null entity record with reporter_type='unknown'."""
    out = {f: None for f in ENTITY_FIELDS}
    out["reporter_type"] = "unknown"
    return out


def normalize_entities(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Coerce a raw extracted dict into the canonical entity shape.
    Unknown / missing / invalid values become null.
    """
    out = empty_entities()
    if not isinstance(raw, dict):
        return out

    # reporter_type
    rt = str(raw.get("reporter_type", "")).strip().lower()
    out["reporter_type"] = rt if rt in REPORTER_TYPES else "unknown"

    # age → int in plausible elder range, else null
    age_raw = raw.get("victim_age")
    if age_raw is not None:
        try:
            age = int(str(age_raw).strip())
            if 30 <= age <= 120:
                out["victim_age"] = age
        except (ValueError, TypeError):
            pass

    # gender → Male / Female / null
    g = str(raw.get("victim_gender", "")).strip().lower()
    if g in ("male", "m", "পুরুষ"):
        out["victim_gender"] = "Male"
    elif g in ("female", "f", "মহিলা", "নারী"):
        out["victim_gender"] = "Female"

    # free-text string fields: strip, blank/"unknown"/"null" → null
    for field in ("victim_name", "location", "abuser_name",
                  "abuser_relation", "incident_date"):
        val = raw.get(field)
        if val is None:
            continue
        s = str(val).strip()
        if s and s.lower() not in ("unknown", "null", "none", "n/a",
                                   "অজ্ঞাত", "নেই", "জানা নেই"):
            out[field] = s

    return out


def build_entity_prompt(text: str) -> str:
    """Focused entity-only extraction prompt (used by standalone extract())."""
    return f"""তুমি একটি তথ্য-নিষ্কাশক (information extractor)। নিচের অভিযোগ থেকে
তথ্য বের করো। এটি voice-to-text থেকে এসেছে, তাই বানান ভুল থাকতে পারে — অর্থ বুঝে নাও।

নিয়ম:
- যা অভিযোগে স্পষ্টভাবে নেই, তা null দাও। অনুমান করবে না।
- reporter_type নির্ধারণ করো:
  "self"        → ভুক্তভোগী নিজে বলছে ("আমাকে", "আমার ছেলে আমাকে")
  "third_party" → অন্য কেউ বলছে ("পাশের বাড়ির বৃদ্ধাকে", "এক বৃদ্ধকে তার ছেলে")
  "unknown"     → বোঝা যাচ্ছে না

অভিযোগ: {text}

শুধু এই JSON দাও:
{{
  "reporter_type": "self | third_party | unknown",
  "victim_name": "ভুক্তভোগীর নাম বা null",
  "victim_age": "বয়স সংখ্যায় বা null",
  "victim_gender": "Male | Female | null",
  "location": "এলাকা/জেলা/ঠিকানা বা null",
  "abuser_name": "নির্যাতনকারীর নাম বা null",
  "abuser_relation": "সম্পর্ক যেমন ছেলে/মেয়ে/পুত্রবধূ বা null",
  "incident_date": "তারিখ বা null"
}}"""


def parse_json(raw: str) -> dict[str, Any]:
    """Parse Gemini JSON output with a regex fallback."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", raw or "", re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return {}


# ── Standalone extractor ──────────────────────────────────────────────────────
class EntityExtractor:
    """Standalone Gemini-based entity extraction (its own API call)."""

    def __init__(self, model_name: str = GEMINI_MODEL):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key.startswith("your_"):
            raise EntityKeyMissingError(
                "GOOGLE_API_KEY not set. Add it to backend/.env"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
        )

    def extract(self, text: str) -> dict[str, Any]:
        if not text or not text.strip():
            return empty_entities()
        prompt = build_entity_prompt(text)
        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise EntityAPIError(f"Gemini API call failed: {e}") from e
        return normalize_entities(parse_json(response.text))


# ── Module-level singleton + shortcut ─────────────────────────────────────────
_extractor: EntityExtractor | None = None


def get_extractor() -> EntityExtractor:
    global _extractor
    if _extractor is None:
        _extractor = EntityExtractor()
    return _extractor


def extract(text: str) -> dict[str, Any]:
    """Module-level shortcut for standalone entity extraction."""
    return get_extractor().extract(text)


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    samples = sys.argv[1:] or [
        "আমি রাবেয়া বেগম, ৭৫ বছর, ময়মনসিংহ থেকে। আমার ছেলে করিম আমাকে মারধর করেছে।",
        "পাশের বাড়ির এক বৃদ্ধাকে তার ছেলে প্রতিদিন মারধর করে, কেউ কিছু বলে না।",
    ]
    for s in samples:
        print(f"\nComplaint: {s}")
        for k, v in extract(s).items():
            print(f"   {k:<18}: {v}")
