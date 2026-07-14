"""
Tests for backend/app/storage.py — consent and anonymisation.

These are the privacy guarantees the thesis claims, so they are tested as hard
rules, not as behaviour that happens to hold today. Everything runs against the
local backend — no Firestore, no network.

Run from backend/ folder:
    python -m pytest tests/test_storage.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import storage


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    """Force the local backend and point it at a throwaway file."""
    monkeypatch.setattr(storage, "LOCAL_STORE", tmp_path / "reports.json")
    monkeypatch.setattr(storage, "_backend", "local")
    monkeypatch.setattr(storage, "_db", None)
    return storage


CLEAN_RECORD = {
    "abuse_types": ["physical", "neglect"],
    "risk_level": 4,
    "severity": 4,
    "district": "গাজীপুর",
    "division": "ঢাকা",
    "gender": "female",
    "reporter_type": "self",
    "abuser_relation": "son",
    "abuser_is_family": True,
    "ongoing": True,
}


# ════════════════════════════════════════════════════════════════════════════════
# Consent
# ════════════════════════════════════════════════════════════════════════════════
class TestConsent:
    def test_without_consent_nothing_is_written(self, local_store):
        with pytest.raises(storage.ConsentRequiredError):
            local_store.save_assessment(CLEAN_RECORD, consent=False)
        assert local_store.fetch_all() == []

    def test_with_consent_it_is_written(self, local_store):
        res = local_store.save_assessment(CLEAN_RECORD, consent=True)
        assert res["saved"] is True
        assert len(local_store.fetch_all()) == 1


# ════════════════════════════════════════════════════════════════════════════════
# Anonymisation — a whitelist, so a new field cannot leak by accident
# ════════════════════════════════════════════════════════════════════════════════
class TestAnonymisation:
    def test_identifying_fields_are_dropped(self, local_store):
        dirty = {
            **CLEAN_RECORD,
            "victim_name":  "রাবেয়া বেগম",
            "phone":        "01712345678",
            "address":      "৩ নং ওয়ার্ড, শ্রীপুর",
            "extra_detail": "আমার ছেলে রাসেল মারধর করেছে",
        }
        local_store.save_assessment(dirty, consent=True)
        stored = local_store.fetch_all()[0]

        for banned in ("victim_name", "phone", "address", "extra_detail"):
            assert banned not in stored

    def test_analytics_fields_survive(self, local_store):
        local_store.save_assessment(CLEAN_RECORD, consent=True)
        stored = local_store.fetch_all()[0]
        for field in CLEAN_RECORD:
            assert stored[field] == CLEAN_RECORD[field]

    def test_an_unknown_field_is_refused_by_default(self, local_store):
        """
        The whitelist must fail closed: a field nobody thought about — say, a GPS
        fix added later — must not reach the database just because it exists.
        """
        local_store.save_assessment(
            {**CLEAN_RECORD, "gps_coords": "23.99,90.42"}, consent=True)
        assert "gps_coords" not in local_store.fetch_all()[0]

    def test_sanitize_is_pure(self):
        """sanitize() must not mutate the caller's dict."""
        original = dict(CLEAN_RECORD, phone="01712345678")
        storage.sanitize(original)
        assert "phone" in original


# ════════════════════════════════════════════════════════════════════════════════
# Dashboard aggregation
# ════════════════════════════════════════════════════════════════════════════════
class TestDashboardStats:
    def test_empty_store_gives_zeroes(self, local_store):
        s = local_store.dashboard_stats()
        assert s["total_assessments"] == 0
        assert s["abuse_type"] == {}

    def test_counts_across_records(self, local_store):
        local_store.save_assessment(CLEAN_RECORD, consent=True)
        local_store.save_assessment(
            {**CLEAN_RECORD, "abuse_types": ["physical"], "gender": "male",
             "district": "সিলেট", "risk_level": 5, "abuser_is_family": False},
            consent=True)

        s = local_store.dashboard_stats()
        assert s["total_assessments"] == 2
        assert s["abuse_type"] == {"physical": 2, "neglect": 1}
        assert s["gender"] == {"female": 1, "male": 1}
        assert s["district"] == {"গাজীপুর": 1, "সিলেট": 1}
        assert s["risk_level"] == {"4": 1, "5": 1}
        assert s["family_vs_non"] == {"family": 1, "non_family": 1}

    def test_every_record_is_timestamped(self, local_store):
        local_store.save_assessment(CLEAN_RECORD, consent=True)
        assert local_store.fetch_all()[0]["created_at"]

    def test_monthly_trend_is_chronological(self, local_store):
        local_store.save_assessment(CLEAN_RECORD, consent=True)
        months = list(local_store.dashboard_stats()["monthly_trend"])
        assert months == sorted(months)


# ════════════════════════════════════════════════════════════════════════════════
# Local store robustness
# ════════════════════════════════════════════════════════════════════════════════
class TestLocalStore:
    def test_missing_file_reads_as_empty(self, local_store):
        assert local_store.fetch_all() == []

    def test_corrupt_file_does_not_crash_the_dashboard(self, local_store):
        local_store.LOCAL_STORE.write_text("{ not json", encoding="utf-8")
        assert local_store.fetch_all() == []

    def test_bangla_survives_the_round_trip(self, local_store):
        local_store.save_assessment(CLEAN_RECORD, consent=True)
        assert local_store.fetch_all()[0]["district"] == "গাজীপুর"
