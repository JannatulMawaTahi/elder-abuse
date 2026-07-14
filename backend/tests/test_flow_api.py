"""
Tests for the guided-assessment endpoints in backend/app/main.py.

Gemini, Firestore and edge-tts are all mocked, so the suite runs offline, fast,
and without burning API quota. What is tested here is the API contract the React
app depends on — not the AI's wording.

Run from backend/ folder:
    python -m pytest tests/test_flow_api.py -v
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import main, storage

ADMIN_PW = "test-password"


@pytest.fixture(scope="module")
def client():
    with patch.object(main, "ADMIN_PASSWORD", ADMIN_PW):
        with TestClient(main.app) as c:
            yield c


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "LOCAL_STORE", tmp_path / "reports.json")
    monkeypatch.setattr(storage, "_backend", "local")
    monkeypatch.setattr(storage, "_db", None)
    return storage


COMPLETE_ANSWERS = {
    "started": True,
    "reporter_type": "self",
    "is_elder": True,
    "gender": "female",
    "location": {"division": "ঢাকা", "district": "গাজীপুর"},
    "selected_categories": ["physical"],
    "P1": True, "P2": True,
    "abuser_is_family": True, "abuser_relation": "son",
    "ongoing": True, "needs_safe_place": False,
    "extra_detail": None,
}

FAKE_GEMINI_RESULT = {
    "abuse_types": ["physical"],
    "abuse_type_bn": "শারীরিক নির্যাতন",
    "severity": 4, "risk_level": 4, "risk_label_bn": "খুব উচ্চ",
    "confidence_percent": 89, "emergency": False, "emergency_actions_bn": [],
    "applicable_sections": ["PMA 2013 — Section 3: Maintenance Obligation"],
    "explanation_bn": "আপনি বলেছেন...", "possible_causes_bn": [],
    "recommendations_bn": ["উপজেলা নির্বাহী অফিসারের কাছে অভিযোগ করুন।"],
    "disclaimer_bn": "এটি চূড়ান্ত আইনি সিদ্ধান্ত নয়।",
}


# ════════════════════════════════════════════════════════════════════════════════
# /flow/next
# ════════════════════════════════════════════════════════════════════════════════
class TestFlowNext:
    def test_empty_answers_returns_the_welcome_screen(self, client):
        r = client.post("/flow/next", json={"answers": {}})
        assert r.status_code == 200
        body = r.json()
        assert body["done"] is False
        assert body["screen"]["type"] == "welcome"

    def test_complete_answers_end_the_flow(self, client):
        body = client.post("/flow/next",
                           json={"answers": COMPLETE_ANSWERS}).json()
        assert body["done"] is True
        assert body["screen"] is None

    def test_progress_is_returned_with_every_screen(self, client):
        p = client.post("/flow/next", json={"answers": {"started": True}}).json()["progress"]
        assert {"current", "total", "percent", "bar"} <= set(p)
        assert len(p["bar"]) == 10

    def test_the_client_can_walk_the_whole_flow(self, client):
        """The exact loop the React app runs — it must terminate."""
        answers: dict = {}
        for _ in range(40):
            body = client.post("/flow/next", json={"answers": answers}).json()
            if body["done"]:
                assert answers, "flow ended before asking anything"
                return
            screen = body["screen"]
            key = screen.get("field") or screen["id"]
            answers[key] = COMPLETE_ANSWERS.get(key, True)
        pytest.fail("flow never finished — the API is looping")


# ════════════════════════════════════════════════════════════════════════════════
# /flow/categories, /flow/divisions, /flow/districts
# ════════════════════════════════════════════════════════════════════════════════
class TestFlowOptions:
    def test_murder_is_hidden_from_self_reporters(self, client):
        opts = client.get("/flow/categories",
                          params={"reporter_type": "self"}).json()["options"]
        assert "murder" not in [o["key"] for o in opts]

    def test_murder_is_offered_to_third_parties(self, client):
        opts = client.get("/flow/categories",
                          params={"reporter_type": "third_party"}).json()["options"]
        assert "murder" in [o["key"] for o in opts]

    def test_eight_divisions(self, client):
        assert len(client.get("/flow/divisions").json()["divisions"]) == 8

    def test_districts_of_a_division(self, client):
        body = client.get("/flow/districts", params={"division": "সিলেট"}).json()
        assert "মৌলভীবাজার" in body["districts"]

    def test_unknown_division_is_404(self, client):
        assert client.get("/flow/districts",
                          params={"division": "Atlantis"}).status_code == 404


# ════════════════════════════════════════════════════════════════════════════════
# /analyze
# ════════════════════════════════════════════════════════════════════════════════
class TestAnalyze:
    def test_returns_everything_the_result_screen_needs(self, client):
        with patch("app.main.get_rag_engine") as rag:
            rag.return_value.analyze_assessment.return_value = dict(FAKE_GEMINI_RESULT)
            body = client.post("/analyze", json={"answers": COMPLETE_ANSWERS}).json()

        for field in ("abuse_type_bn", "risk_level", "risk_label_bn",
                      "confidence_percent", "applicable_sections",
                      "explanation_bn", "recommendations_bn", "disclaimer_bn"):
            assert field in body, f"result screen would be missing {field}"

    def test_the_summary_sent_to_gemini_is_built_from_the_answers(self, client):
        with patch("app.main.get_rag_engine") as rag:
            rag.return_value.analyze_assessment.return_value = dict(FAKE_GEMINI_RESULT)
            client.post("/analyze", json={"answers": COMPLETE_ANSWERS})
            summary = rag.return_value.analyze_assessment.call_args[0][0]
        assert "ছেলে" in summary

    def test_gemini_failure_still_returns_risk_and_law(self, client):
        """
        If Gemini is down the elder must still learn how serious this is — the
        rule engine already decided that. Only the prose is lost.
        """
        from app.rag_engine import GeminiAPIError

        with patch("app.main.get_rag_engine") as rag:
            rag.return_value.analyze_assessment.side_effect = GeminiAPIError("down")
            r = client.post("/analyze", json={"answers": COMPLETE_ANSWERS})

        assert r.status_code == 200
        body = r.json()
        assert body["degraded"] is True
        assert body["risk_level"] == 4
        assert body["disclaimer_bn"]

    def test_never_reports_full_certainty(self, client):
        with patch("app.main.get_rag_engine") as rag:
            rag.return_value.analyze_assessment.return_value = dict(FAKE_GEMINI_RESULT)
            body = client.post("/analyze", json={"answers": COMPLETE_ANSWERS}).json()
        assert body["confidence_percent"] < 100


# ════════════════════════════════════════════════════════════════════════════════
# /tts
# ════════════════════════════════════════════════════════════════════════════════
class TestTTS:
    def test_returns_mp3(self, client):
        async def fake_synth(text, voice=None, **kw):
            return b"ID3fake-mp3-bytes"

        with patch("app.tts_service.synthesize", side_effect=fake_synth):
            r = client.get("/tts", params={"text": "আপনি কি নিরাপদ আছেন?"})

        assert r.status_code == 200
        assert r.headers["content-type"] == "audio/mpeg"
        assert r.content

    def test_empty_text_is_rejected(self, client):
        assert client.get("/tts", params={"text": ""}).status_code == 422


# ════════════════════════════════════════════════════════════════════════════════
# /save-report
# ════════════════════════════════════════════════════════════════════════════════
class TestSaveReport:
    def test_without_consent_nothing_is_saved(self, client, local_store):
        body = client.post("/save-report", json={
            "answers": COMPLETE_ANSWERS, "consent": False}).json()
        assert body["saved"] is False
        assert local_store.fetch_all() == []

    def test_with_consent_an_anonymised_record_is_saved(self, client, local_store):
        body = client.post("/save-report", json={
            "answers": COMPLETE_ANSWERS, "consent": True}).json()
        assert body["saved"] is True

        stored = local_store.fetch_all()[0]
        assert stored["abuse_types"] == ["physical"]
        assert stored["district"] == "গাজীপুর"

    def test_a_client_cannot_smuggle_identity_into_the_database(self, client, local_store):
        """
        The record is rebuilt server-side from the answers, so extra fields a
        (malicious or buggy) client sends are simply never looked at.
        """
        client.post("/save-report", json={
            "answers": {**COMPLETE_ANSWERS,
                        "victim_name": "রাবেয়া বেগম",
                        "phone": "01712345678",
                        "extra_detail": "আমার ছেলে রাসেল মারধর করেছে"},
            "consent": True,
        })
        stored = local_store.fetch_all()[0]
        for banned in ("victim_name", "phone", "extra_detail"):
            assert banned not in stored


# ════════════════════════════════════════════════════════════════════════════════
# Admin dashboard
# ════════════════════════════════════════════════════════════════════════════════
class TestDashboard:
    def test_wrong_password_is_rejected(self, client):
        assert client.post("/dashboard/login",
                           json={"password": "guess"}).status_code == 401

    def test_right_password_is_accepted(self, client):
        assert client.post("/dashboard/login",
                           json={"password": ADMIN_PW}).status_code == 200

    def test_stats_need_the_password(self, client):
        assert client.get("/dashboard/stats").status_code == 401

    def test_stats_serve_every_chart(self, client, local_store):
        client.post("/save-report",
                    json={"answers": COMPLETE_ANSWERS, "consent": True})
        body = client.get("/dashboard/stats",
                          headers={"X-Admin-Password": ADMIN_PW}).json()

        for chart in ("abuse_type", "gender", "district", "risk_level",
                      "family_vs_non", "monthly_trend"):
            assert chart in body, f"dashboard chart '{chart}' has no data"
        assert body["total_assessments"] == 1


# ════════════════════════════════════════════════════════════════════════════════
# Meta
# ════════════════════════════════════════════════════════════════════════════════
class TestHealth:
    def test_health_reports_the_storage_backend(self, client):
        body = client.get("/health").json()
        assert body["status"] == "ok"
        assert body["storage"] in ("firestore", "local")
