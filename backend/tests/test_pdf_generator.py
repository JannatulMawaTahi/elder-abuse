"""
Tests for backend/app/pdf_generator.py

Run from backend/ folder:
    python -m pytest tests/test_pdf_generator.py -v

Note: the PDF text layer is garbled by HarfBuzz shaping (visual is correct),
so tests assert on structure/robustness, not extracted text. Visual review of
generated PDFs is done separately by reading the PDF.
"""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_generator import (
    generate_complaint_pdf,
    generate_case_ref,
    from_analysis,
    PLACEHOLDER,
)


def _full_case(**overrides):
    base = {
        "transcript": "আমার ছেলে করিম আমাকে মারধর করেছে এবং বাড়ি থেকে বের করে দিয়েছে।",
        "abuse_type": "Physical Abuse, Abandonment",
        "applicable_sections": [
            "পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ — ধারা ৩",
            "দণ্ডবিধি ১৮৬০ — ধারা ৩২৩",
        ],
        "recommended_action_bangla": "প্রয়োজনীয় ব্যবস্থা গ্রহণ করিবেন।",
        "reporter_type": "self",
        "entities": {
            "victim_name": "রাবেয়া বেগম", "victim_age": 75,
            "location": "ময়মনসিংহ সদর",
            "abuser_name": "করিম", "abuser_relation": "ছেলে",
        },
        "uno_upazila": "ময়মনসিংহ সদর", "uno_district": "ময়মনসিংহ",
    }
    base.update(overrides)
    return base


# ════════════════════════════════════════════════════════════════════════════════
# CASE REFERENCE
# ════════════════════════════════════════════════════════════════════════════════
class TestCaseRef:

    def test_format(self):
        ref = generate_case_ref()
        assert re.match(r"^EA-\d{4}-\d{4}-[0-9A-F]{4}$", ref), ref

    def test_unique(self):
        assert generate_case_ref() != generate_case_ref()


# ════════════════════════════════════════════════════════════════════════════════
# PDF OUTPUT — structure & robustness
# ════════════════════════════════════════════════════════════════════════════════
class TestPdfOutput:

    def test_returns_valid_pdf_bytes(self):
        out = generate_complaint_pdf(_full_case())
        assert isinstance(out, (bytes, bytearray))
        assert out[:5] == b"%PDF-"
        assert len(out) > 2000   # a real letter, not empty

    def test_self_mode(self):
        out = generate_complaint_pdf(_full_case(), anonymous=False)
        assert out[:5] == b"%PDF-"

    def test_anonymous_mode(self):
        out = generate_complaint_pdf(_full_case(), anonymous=True)
        assert out[:5] == b"%PDF-"

    def test_anonymous_differs_from_named(self):
        named = generate_complaint_pdf(_full_case(), anonymous=False)
        anon  = generate_complaint_pdf(_full_case(), anonymous=True)
        assert named != anon   # different content (name hidden vs shown)

    def test_third_party_mode(self):
        case = _full_case(reporter_type="third_party")
        out = generate_complaint_pdf(case)
        assert out[:5] == b"%PDF-"


# ════════════════════════════════════════════════════════════════════════════════
# MISSING DATA — must not crash, uses placeholders
# ════════════════════════════════════════════════════════════════════════════════
class TestMissingData:

    def test_no_entities(self):
        case = {
            "transcript": "ছেলে মারধর করেছে",
            "abuse_type": "Physical Abuse",
            "applicable_sections": ["দণ্ডবিধি ১৮৬০ — ধারা ৩২৩"],
            "recommended_action_bangla": "ব্যবস্থা নিন।",
            "reporter_type": "unknown",
            "entities": {},
        }
        out = generate_complaint_pdf(case)
        assert out[:5] == b"%PDF-"

    def test_partial_entities(self):
        case = _full_case(entities={"abuser_relation": "ছেলে"})
        out = generate_complaint_pdf(case)
        assert out[:5] == b"%PDF-"

    def test_empty_sections(self):
        case = _full_case(applicable_sections=[])
        out = generate_complaint_pdf(case)
        assert out[:5] == b"%PDF-"

    def test_empty_recommended_action_uses_default_prayer(self):
        case = _full_case(recommended_action_bangla="")
        out = generate_complaint_pdf(case)
        assert out[:5] == b"%PDF-"

    def test_minimal_case(self):
        out = generate_complaint_pdf({"transcript": "ছেলে মারধর করেছে"})
        assert out[:5] == b"%PDF-"


# ════════════════════════════════════════════════════════════════════════════════
# from_analysis() assembler
# ════════════════════════════════════════════════════════════════════════════════
class TestFromAnalysis:

    def test_assembles_case_data(self):
        analysis = {
            "abuse_type": "Neglect",
            "applicable_sections": ["PMA 2013 Section 4"],
            "severity": 2,
            "civil_or_criminal": "Civil",
            "legal_advice_bangla": "পরামর্শ",
            "recommended_action_bangla": "UNO তে যান",
            "reporter_type": "self",
            "entities": {"victim_name": "করিম"},
        }
        cd = from_analysis("ছেলে যত্ন নেয় না", analysis,
                           uno_upazila="সদর", uno_district="ঢাকা")
        assert cd["transcript"]                 == "ছেলে যত্ন নেয় না"
        assert cd["abuse_type"]                 == "Neglect"
        assert cd["recommended_action_bangla"]  == "UNO তে যান"
        assert cd["uno_upazila"]                == "সদর"
        assert cd["entities"]["victim_name"]    == "করিম"

    def test_from_analysis_output_generates_pdf(self):
        analysis = {
            "abuse_type": "Physical Abuse",
            "applicable_sections": ["দণ্ডবিধি ১৮৬০ — ধারা ৩২৩"],
            "recommended_action_bangla": "থানায় FIR করুন।",
            "reporter_type": "self",
            "entities": {"abuser_relation": "ছেলে"},
        }
        cd = from_analysis("ছেলে মারধর করেছে", analysis)
        out = generate_complaint_pdf(cd)
        assert out[:5] == b"%PDF-"
