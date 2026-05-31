"""
Tests for backend/app/rag_engine.py

Run from backend/ folder:
    python -m pytest tests/test_rag_engine.py -v

Unit tests (retrieval, prompt, parsing) run offline with mocks.
The real Gemini integration test is SKIPPED unless GOOGLE_API_KEY is set.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag_engine import (
    RagEngine,
    RagEngineError,
    GeminiAPIError,
)


# ── A RagEngine with Gemini mocked (no real API, no key needed) ────────────────
@pytest.fixture
def mock_engine():
    """RagEngine where genai is fully mocked — tests logic without API calls."""
    with patch("app.rag_engine.genai") as mock_genai, \
         patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key_xxx"}):
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        engine = RagEngine()
        engine._mock_model = mock_model  # expose for per-test config
        yield engine


def _gemini_reply(payload: dict):
    resp = MagicMock()
    resp.text = json.dumps(payload, ensure_ascii=False)
    return resp


# ════════════════════════════════════════════════════════════════════════════════
# RETRIEVAL (keyword/category-based) — pure logic, no API
# ════════════════════════════════════════════════════════════════════════════════
class TestRetrieval:

    def test_physical_retrieves_bpc_323(self, mock_engine):
        sections = mock_engine._retrieve("physical")
        ids = [s["id"] for s in sections]
        assert "bpc_323" in ids

    def test_financial_retrieves_bpc_420(self, mock_engine):
        sections = mock_engine._retrieve("financial")
        ids = [s["id"] for s in sections]
        assert "bpc_420" in ids or "bpc_406" in ids

    def test_murder_retrieves_bpc_302(self, mock_engine):
        sections = mock_engine._retrieve("murder")
        ids = [s["id"] for s in sections]
        assert "bpc_302" in ids

    def test_always_include_procedural(self, mock_engine):
        """Complaint procedure + penalty should always be retrieved."""
        sections = mock_engine._retrieve("physical")
        ids = [s["id"] for s in sections]
        assert "pma_sec5" in ids   # complaint procedure
        assert "pma_sec7" in ids   # penalty

    def test_unknown_retrieves_substantive_sections(self, mock_engine):
        """Unknown category → all substantive (non-'all') sections included."""
        sections = mock_engine._retrieve("unknown")
        ids = [s["id"] for s in sections]
        # Should include substantive sections from multiple categories
        assert "bpc_323" in ids
        assert "bpc_420" in ids

    def test_retrieval_never_empty(self, mock_engine):
        for cat in ["physical", "financial", "neglect", "verbal",
                    "abandonment", "murder", "unknown"]:
            assert len(mock_engine._retrieve(cat)) > 0


# ════════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ════════════════════════════════════════════════════════════════════════════════
class TestPromptBuilding:

    def test_prompt_contains_complaint(self, mock_engine):
        sections = mock_engine._retrieve("physical")
        prompt = mock_engine._build_prompt("ছেলে মারধর করেছে", "physical",
                                           "bangla", sections)
        assert "ছেলে মারধর করেছে" in prompt

    def test_prompt_contains_sections(self, mock_engine):
        sections = mock_engine._retrieve("physical")
        prompt = mock_engine._build_prompt("test", "physical", "bangla", sections)
        assert "BPC Section 323" in prompt

    def test_prompt_mentions_typo_handling(self, mock_engine):
        sections = mock_engine._retrieve("physical")
        prompt = mock_engine._build_prompt("test", "physical", "bangla", sections)
        # Prompt instructs Gemini to handle voice-to-text spelling errors
        assert "মার্ধুর" in prompt or "বানান ভুল" in prompt


# ════════════════════════════════════════════════════════════════════════════════
# JSON PARSING
# ════════════════════════════════════════════════════════════════════════════════
class TestJsonParsing:

    def test_parses_clean_json(self):
        raw = '{"abuse_type": "Physical Abuse", "severity": "4"}'
        parsed = RagEngine._parse_json(raw)
        assert parsed["abuse_type"] == "Physical Abuse"

    def test_parses_json_with_surrounding_text(self):
        raw = 'Here is the result:\n{"abuse_type": "Neglect"}\nDone.'
        parsed = RagEngine._parse_json(raw)
        assert parsed["abuse_type"] == "Neglect"

    def test_returns_empty_on_garbage(self):
        assert RagEngine._parse_json("not json at all") == {}


# ════════════════════════════════════════════════════════════════════════════════
# ANALYZE (mocked Gemini) — full pipeline logic
# ════════════════════════════════════════════════════════════════════════════════
class TestAnalyzeMocked:

    def test_empty_text_raises(self, mock_engine):
        with pytest.raises(RagEngineError):
            mock_engine.analyze("")

    def test_analyze_merges_gemini_output(self, mock_engine):
        mock_engine._mock_model.generate_content.return_value = _gemini_reply({
            "abuse_type": "Physical Abuse",
            "applicable_sections": ["BPC Section 323"],
            "severity": "4",
            "legal_advice_bangla": "থানায় যান",
            "legal_advice_english": "Go to police",
            "recommended_action_bangla": "FIR করুন",
            "recommended_action_english": "File FIR",
            "civil_or_criminal": "Criminal",
            "urgency": "4",
        })
        result = mock_engine.analyze("ছেলে মারধর করেছে")

        assert result["abuse_type"]        == "Physical Abuse"
        assert result["severity"]          == 4
        assert result["civil_or_criminal"] == "Criminal"
        assert result["language_mode"]     == "bangla"
        assert "keyword_category"          in result
        assert "retrieved_ids"             in result

    def test_severity_falls_back_on_bad_value(self, mock_engine):
        mock_engine._mock_model.generate_content.return_value = _gemini_reply({
            "abuse_type": "Physical Abuse",
            "severity": "not-a-number",
        })
        result = mock_engine.analyze("ছেলে মারধর করেছে")
        # Falls back to keyword classifier severity (physical = 4)
        assert isinstance(result["severity"], int)

    def test_gemini_failure_raises_api_error(self, mock_engine):
        mock_engine._mock_model.generate_content.side_effect = RuntimeError("boom")
        with pytest.raises(GeminiAPIError):
            mock_engine.analyze("ছেলে মারধর করেছে")


# ════════════════════════════════════════════════════════════════════════════════
# REAL GEMINI INTEGRATION — skipped if no key
# ════════════════════════════════════════════════════════════════════════════════
@pytest.mark.skipif(
    not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY", "").startswith("your_"),
    reason="GOOGLE_API_KEY not set",
)
class TestRealGemini:

    @pytest.fixture(scope="class")
    def engine(self):
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent / ".env")
        return RagEngine()

    def test_whisper_typo_complaint_classified_correctly(self, engine):
        """THE KEY TEST: Phase 2 returned 'unknown' for this typo-laden complaint.

        Gemini RAG should now correctly identify it as physical abuse despite
        Whisper misspellings (মার্ধুর = মারধর, বারি = বাড়ি).
        """
        q = "আমার ছেলে আমাকে মার্ধুর করেছে এবং বারি থে কে বের করে দিয়াছে"
        result = engine.analyze(q)

        # Keyword classifier failed (unknown), but Gemini should succeed
        assert result["abuse_type"].lower() != "unknown"
        assert result["severity"] >= 3
        assert len(result["applicable_sections"]) > 0
        assert len(result["legal_advice_bangla"]) > 20
        print(f"\n  Abuse type: {result['abuse_type']}")
        print(f"  Sections  : {result['applicable_sections']}")

    def test_english_complaint(self, engine):
        result = engine.analyze("My son abandoned me and took all my property")
        assert result["abuse_type"].lower() != "unknown"
        assert len(result["legal_advice_english"]) > 20
