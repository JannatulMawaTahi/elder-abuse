"""
Tests for backend/app/vector_store.py

Run from backend/ folder:
    python -m pytest tests/test_vector_store.py -v

NOTE: First run downloads the embedding model (~120 MB) and builds the store —
this can take 1-2 minutes. Subsequent runs are fast (cached).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import vector_store


@pytest.fixture(scope="module")
def store():
    """Build the store once for all tests in this module."""
    info = vector_store.build_store()
    assert info["count"] == 16   # 9 PMA + 7 BPC sections
    return info


# ════════════════════════════════════════════════════════════════════════════════
# BUILD
# ════════════════════════════════════════════════════════════════════════════════
class TestBuild:

    def test_store_builds_with_16_sections(self, store):
        assert store["count"]      == 16
        assert store["collection"] == "legal_sections"
        assert store["status"]     in ("built", "loaded")

    def test_rebuild_is_idempotent(self, store):
        """Building again should not duplicate sections."""
        info = vector_store.build_store()
        assert info["count"] == 16


# ════════════════════════════════════════════════════════════════════════════════
# SEMANTIC SEARCH — the whole point of Phase 3
# ════════════════════════════════════════════════════════════════════════════════
class TestSemanticSearch:

    def test_returns_top_k_results(self, store):
        results = vector_store.search("ছেলে মারধর করেছে", top_k=3)
        assert len(results) == 3
        for r in results:
            assert "id"         in r
            assert "section"    in r
            assert "similarity" in r

    def test_empty_query_returns_empty(self, store):
        assert vector_store.search("") == []
        assert vector_store.search("   ") == []

    def test_physical_abuse_matches_bpc_323(self, store):
        """Physical hurt query should surface BPC 323 (voluntarily causing hurt)."""
        results = vector_store.search("ছেলে বাবাকে মারধর করে আঘাত করেছে", top_k=5)
        ids = [r["id"] for r in results]
        assert "bpc_323" in ids

    def test_whisper_typo_still_matches_physical(self, store):
        """KEY TEST: Whisper typo 'মার্ধুর' should STILL match physical-abuse law.

        This is the core reason Phase 3 exists — keyword matching failed on this
        in Phase 2, but semantic embeddings handle the misspelling.
        """
        results = vector_store.search("ছেলে আমাকে মার্ধুর করেছে", top_k=5)
        ids = [r["id"] for r in results]
        # Should retrieve a physical-hurt related section near the top
        physical_ids = {"bpc_323", "bpc_324", "pma_sec3"}
        assert physical_ids & set(ids), \
            f"Whisper typo did not match any physical law. Got: {ids}"

    def test_abandonment_matches_pma(self, store):
        """Abandonment query should surface PMA maintenance/abandonment sections."""
        results = vector_store.search(
            "ছেলে আমাকে বাড়ি থেকে বের করে রাস্তায় ফেলে দিয়েছে", top_k=5
        )
        ids = [r["id"] for r in results]
        pma_abandonment = {"pma_sec3", "pma_sec4"}
        assert pma_abandonment & set(ids)

    def test_financial_matches_bpc(self, store):
        """Property fraud query should surface BPC 406/420."""
        results = vector_store.search(
            "জোর করে জমির দলিল লিখিয়ে সম্পত্তি আত্মসাৎ করেছে", top_k=5
        )
        ids = [r["id"] for r in results]
        financial_ids = {"bpc_406", "bpc_420"}
        assert financial_ids & set(ids)

    def test_english_query_works(self, store):
        """Multilingual model: English query should also match correctly."""
        results = vector_store.search(
            "son murdered his elderly father", top_k=5
        )
        ids = [r["id"] for r in results]
        murder_ids = {"bpc_302", "bpc_304"}
        assert murder_ids & set(ids)

    def test_similarity_score_in_range(self, store):
        results = vector_store.search("ছেলে মারধর করেছে", top_k=3)
        for r in results:
            assert -1.0 <= r["similarity"] <= 1.0

    def test_results_sorted_by_similarity(self, store):
        results = vector_store.search("ছেলে মারধর করেছে", top_k=5)
        sims = [r["similarity"] for r in results]
        assert sims == sorted(sims, reverse=True)


# ════════════════════════════════════════════════════════════════════════════════
# METADATA
# ════════════════════════════════════════════════════════════════════════════════
class TestMetadata:

    def test_applicable_for_is_list(self, store):
        results = vector_store.search("মারধর", top_k=1)
        assert isinstance(results[0]["applicable_for"], list)

    def test_law_field_present(self, store):
        results = vector_store.search("হত্যা", top_k=3)
        for r in results:
            assert r["law"] in ("PMA", "BPC")
