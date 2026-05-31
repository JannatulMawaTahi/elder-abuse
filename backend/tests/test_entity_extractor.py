"""
Tests for backend/app/entity_extractor.py

Run from backend/ folder:
    python -m pytest tests/test_entity_extractor.py -v

Unit tests (normalization, prompt) run offline.
Real Gemini integration tests are SKIPPED unless GOOGLE_API_KEY is set.
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.entity_extractor import (
    normalize_entities,
    empty_entities,
    build_entity_prompt,
    parse_json,
    ENTITY_FIELDS,
    REPORTER_TYPES,
)


# ════════════════════════════════════════════════════════════════════════════════
# NORMALIZATION — pure logic, no API
# ════════════════════════════════════════════════════════════════════════════════
class TestNormalize:

    def test_empty_record_has_all_fields(self):
        e = empty_entities()
        for f in ENTITY_FIELDS:
            assert f in e
        assert e["reporter_type"] == "unknown"

    def test_normalize_none_returns_empty(self):
        assert normalize_entities(None)["reporter_type"] == "unknown"

    def test_valid_age_kept(self):
        e = normalize_entities({"victim_age": "75"})
        assert e["victim_age"] == 75

    def test_implausible_age_dropped(self):
        assert normalize_entities({"victim_age": "5"})["victim_age"] is None
        assert normalize_entities({"victim_age": "200"})["victim_age"] is None

    def test_non_numeric_age_dropped(self):
        assert normalize_entities({"victim_age": "অজ্ঞাত"})["victim_age"] is None

    def test_gender_normalized(self):
        assert normalize_entities({"victim_gender": "female"})["victim_gender"] == "Female"
        assert normalize_entities({"victim_gender": "মহিলা"})["victim_gender"] == "Female"
        assert normalize_entities({"victim_gender": "Male"})["victim_gender"] == "Male"

    def test_reporter_type_validated(self):
        assert normalize_entities({"reporter_type": "self"})["reporter_type"] == "self"
        assert normalize_entities({"reporter_type": "third_party"})["reporter_type"] == "third_party"
        assert normalize_entities({"reporter_type": "garbage"})["reporter_type"] == "unknown"

    def test_placeholder_strings_become_null(self):
        e = normalize_entities({
            "victim_name": "অজ্ঞাত",
            "location": "unknown",
            "abuser_name": "null",
        })
        assert e["victim_name"]  is None
        assert e["location"]     is None
        assert e["abuser_name"]  is None

    def test_real_values_kept(self):
        e = normalize_entities({
            "victim_name": "রাবেয়া বেগম",
            "location": "ময়মনসিংহ",
            "abuser_relation": "ছেলে",
        })
        assert e["victim_name"]      == "রাবেয়া বেগম"
        assert e["location"]         == "ময়মনসিংহ"
        assert e["abuser_relation"]  == "ছেলে"


# ════════════════════════════════════════════════════════════════════════════════
# PROMPT + PARSING
# ════════════════════════════════════════════════════════════════════════════════
class TestPromptAndParse:

    def test_prompt_contains_text(self):
        p = build_entity_prompt("ছেলে মারধর করেছে")
        assert "ছেলে মারধর করেছে" in p

    def test_prompt_explains_reporter_types(self):
        p = build_entity_prompt("test")
        assert "self" in p and "third_party" in p

    def test_parse_clean_json(self):
        assert parse_json('{"victim_name": "করিম"}')["victim_name"] == "করিম"

    def test_parse_garbage_returns_empty(self):
        assert parse_json("not json") == {}


# ════════════════════════════════════════════════════════════════════════════════
# REAL GEMINI — skipped if no key
# ════════════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY", "").startswith("your_"),
    reason="GOOGLE_API_KEY not set",
)
class TestRealGemini:

    @pytest.fixture(scope="class")
    def ex(self):
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        from app.entity_extractor import EntityExtractor
        return EntityExtractor()

    def test_self_report_with_details(self, ex):
        """Victim reporting with name + age + location."""
        text = "আমি রাবেয়া বেগম, ৭৫ বছর, ময়মনসিংহ থেকে। আমার ছেলে করিম আমাকে মারধর করেছে।"
        e = ex.extract(text)
        assert e["reporter_type"]   == "self"
        assert e["victim_age"]      == 75
        assert e["abuser_relation"] is not None
        print(f"\n  self-report: {e}")

    def test_third_party_unknown_victim(self, ex):
        """THE KEY CASE: neighbor reports, doesn't know victim's name/age."""
        text = "পাশের বাড়ির এক বৃদ্ধাকে তার ছেলে প্রতিদিন মারধর করে, কেউ কিছু বলে না।"
        e = ex.extract(text)
        assert e["reporter_type"] == "third_party"
        # Name/age unknown → must be null, NOT hallucinated
        assert e["victim_name"] is None
        assert e["victim_age"]  is None
        print(f"\n  third-party: {e}")

    def test_empty_text_returns_empty(self, ex):
        e = ex.extract("")
        assert e["reporter_type"] == "unknown"
        assert e["victim_name"]   is None
