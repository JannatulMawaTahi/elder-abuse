"""
Tests for backend/app/question_engine.py — the guided Bangla yes/no flow.

This is the heart of the system: it decides which question comes next, how risky
the situation is, and what leaves the device. Everything here runs offline.

Run from backend/ folder:
    python -m pytest tests/test_question_engine.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.question_engine import QuestionEngine


@pytest.fixture(scope="module")
def qe():
    return QuestionEngine()


def answer_key(screen: dict) -> str:
    """The key the client stores this screen's answer under."""
    return screen.get("field") or screen["id"]


def walk(qe: QuestionEngine, script: dict, max_steps: int = 40) -> dict:
    """Drive the flow to completion using `script`, exactly as the client does."""
    answers: dict = {}
    for _ in range(max_steps):
        screen = qe.next_screen(answers)
        if screen is None:
            return answers
        key = answer_key(screen)
        assert key in script, f"script has no answer for screen {screen['id']} (key={key})"
        answers[key] = script[key]
    pytest.fail("flow did not finish — the engine is looping")


# Baseline: an elder reporting physical abuse by her son, still ongoing.
BASE_SCRIPT = {
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


# ════════════════════════════════════════════════════════════════════════════════
# Screen sequencing — the client must never get stuck
# ════════════════════════════════════════════════════════════════════════════════
class TestFlow:
    def test_answering_a_screen_always_advances(self, qe):
        """
        The no-infinite-loop invariant: the key the client derives from a screen
        (`field` or, failing that, `id`) must be the same key the engine checks.
        The welcome screen once used a third name internally, so answering it
        changed nothing and the app was stuck on screen 1 forever.
        """
        answers: dict = {}
        for _ in range(40):
            screen = qe.next_screen(answers)
            if screen is None:
                return
            answers[answer_key(screen)] = BASE_SCRIPT.get(answer_key(screen), True)
            assert qe.next_screen(answers) != screen, \
                f"answering {screen['id']} did not advance the flow"
        pytest.fail("flow never finished")

    def test_flow_completes(self, qe):
        answers = walk(qe, BASE_SCRIPT)
        assert qe.next_screen(answers) is None

    def test_welcome_comes_first(self, qe):
        first = qe.next_screen({})
        assert first["type"] == "welcome"
        assert answer_key(first) == "started"

    def test_answering_welcome_advances(self, qe):
        """The exact bug that caused an infinite loop on screen 1."""
        after = qe.next_screen({"started": True})
        assert after["id"] != "welcome"

    def test_only_selected_categories_are_asked(self, qe):
        answers = walk(qe, {**BASE_SCRIPT, "selected_categories": ["financial"],
                            "F1": True, "F2": False})
        assert "F1" in answers and "F2" in answers
        assert "P1" not in answers, "physical follow-ups asked but not selected"

    def test_multiple_categories_ask_all_their_followups(self, qe):
        answers = walk(qe, {**BASE_SCRIPT,
                            "selected_categories": ["physical", "financial"],
                            "F1": True, "F2": True})
        assert {"P1", "P2", "F1", "F2"} <= set(answers)

    def test_relation_screen_skipped_when_abuser_is_not_family(self, qe):
        """AB2a (family relation) must not appear if the abuser isn't family."""
        ids = [s["id"] for s in qe.screen_sequence(
            {**BASE_SCRIPT, "abuser_is_family": False})]
        assert "AB2a" not in ids
        assert "AB2b" in ids

    def test_relation_screen_shown_when_abuser_is_family(self, qe):
        ids = [s["id"] for s in qe.screen_sequence(BASE_SCRIPT)]
        assert "AB2a" in ids
        assert "AB2b" not in ids


# ════════════════════════════════════════════════════════════════════════════════
# Category options
# ════════════════════════════════════════════════════════════════════════════════
class TestCategories:
    def test_murder_hidden_from_self_reporters(self, qe):
        """A dead person cannot file their own report."""
        keys = [o["key"] for o in qe.category_options("self")]
        assert "murder" not in keys

    def test_murder_shown_to_third_party(self, qe):
        keys = [o["key"] for o in qe.category_options("third_party")]
        assert "murder" in keys

    def test_every_option_has_icon_and_bangla_label(self, qe):
        for o in qe.category_options("third_party"):
            assert o["icon"] and o["label_bn"]


# ════════════════════════════════════════════════════════════════════════════════
# Location
# ════════════════════════════════════════════════════════════════════════════════
class TestLocation:
    def test_eight_divisions(self, qe):
        assert len(qe.divisions) == 8

    def test_sixty_four_districts_total(self, qe):
        total = sum(len(d) for d in qe.divisions.values())
        assert total == 64

    def test_unknown_division_returns_empty(self, qe):
        assert qe.districts_for("Atlantis") == []


# ════════════════════════════════════════════════════════════════════════════════
# Progress bar
# ════════════════════════════════════════════════════════════════════════════════
class TestProgress:
    def test_starts_at_zero(self, qe):
        assert qe.progress({})["current"] == 0

    def test_reaches_full_when_done(self, qe):
        answers = walk(qe, BASE_SCRIPT)
        p = qe.progress(answers)
        assert p["current"] == p["total"]
        assert p["percent"] == 100

    def test_bar_is_ten_blocks(self, qe):
        assert len(qe.progress(BASE_SCRIPT)["bar"]) == 10


# ════════════════════════════════════════════════════════════════════════════════
# Risk — the number that decides whether an emergency action is shown
# ════════════════════════════════════════════════════════════════════════════════
class TestRisk:
    def test_no_abuse_confirmed_is_lowest_risk(self, qe):
        a = qe.assess({**BASE_SCRIPT, "P1": False, "P2": False})
        assert a["risk_level"] == 1
        assert a["confirmed_categories"] == []

    def test_needing_safety_now_is_an_emergency(self, qe):
        a = qe.assess({**BASE_SCRIPT, "needs_safe_place": True})
        assert a["emergency"] is True
        assert a["risk_level"] == 5
        assert a["emergency_actions_bn"], "risk 5 must carry an emergency action"

    def test_serious_abuse_without_emergency_caps_at_four(self, qe):
        """
        Level 5 says 'জরুরি' and comes with a call-999 action. Serious-but-not-
        immediate cases must not claim that, or the label loses its meaning.
        """
        a = qe.assess(BASE_SCRIPT)
        assert a["emergency"] is False
        assert a["risk_level"] == 4
        assert a["risk_label_bn"] != "জরুরি"

    def test_escalating_followup_raises_risk(self, qe):
        """
        F2 = land/property signed away without consent → riskier than F1 alone.

        Uses financial (base severity 2) rather than physical (4): physical is
        already at the non-emergency ceiling, so the +1 would be swallowed by the
        cap and the test would pass for the wrong reason.
        """
        base = {**BASE_SCRIPT, "selected_categories": ["financial"],
                "F1": True, "ongoing": False}
        mild   = qe.assess({**base, "F2": False})
        severe = qe.assess({**base, "F2": True})
        assert severe["risk_level"] > mild["risk_level"]

    def test_ongoing_abuse_raises_risk(self, qe):
        base = {**BASE_SCRIPT, "selected_categories": ["financial"],
                "F1": True, "F2": False}
        past    = qe.assess({**base, "ongoing": False})
        current = qe.assess({**base, "ongoing": True})
        assert current["risk_level"] > past["risk_level"]


# ════════════════════════════════════════════════════════════════════════════════
# Confidence
# ════════════════════════════════════════════════════════════════════════════════
class TestConfidence:
    def test_all_yes_is_high_confidence(self, qe):
        assert qe.assess(BASE_SCRIPT)["confidence_percent"] >= 80

    def test_all_no_is_low_confidence(self, qe):
        a = qe.assess({**BASE_SCRIPT, "P1": False, "P2": False})
        assert a["confidence_percent"] <= 40

    def test_never_claims_certainty(self, qe):
        """An AI screening tool must not report 100%."""
        assert qe.assess(BASE_SCRIPT)["confidence_percent"] < 100


# ════════════════════════════════════════════════════════════════════════════════
# Bangla summary → fed to Gemini
# ════════════════════════════════════════════════════════════════════════════════
class TestSummary:
    def test_mentions_the_abuser(self, qe):
        assert "ছেলে" in qe.build_summary(BASE_SCRIPT)

    def test_is_bangla(self, qe):
        summary = qe.build_summary(BASE_SCRIPT)
        bengali = sum("ঀ" <= ch <= "৿" for ch in summary)
        assert bengali > len(summary) * 0.4


# ════════════════════════════════════════════════════════════════════════════════
# Anonymisation — what is allowed to leave the device
# ════════════════════════════════════════════════════════════════════════════════
class TestDashboardRecord:
    def test_carries_the_analytics_fields(self, qe):
        rec = qe.dashboard_record(BASE_SCRIPT, qe.assess(BASE_SCRIPT))
        assert rec["abuse_types"] == ["physical"]
        assert rec["district"] == "গাজীপুর"
        assert rec["gender"] == "female"
        assert rec["abuser_relation"] == "son"

    def test_carries_no_identity(self, qe):
        """Nothing that could name or locate a person precisely."""
        answers = {**BASE_SCRIPT, "extra_detail": "আমার ছেলে রাসেল মারধর করেছে"}
        rec = qe.dashboard_record(answers, qe.assess(answers))
        for banned in ("extra_detail", "victim_name", "name", "phone", "address"):
            assert banned not in rec
