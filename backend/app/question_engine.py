"""
Question Engine — drives the guided Bangla yes/no assessment flow.

Stateless: the frontend holds the answers dict and asks the engine
"given these answers, what comes next?". That keeps the API simple and
means no server-side session storage.

Responsibilities
  1. next_screen(answers)  → the next screen to show (branch/skip logic applied)
  2. progress(answers)     → graphical progress bar data
  3. build_summary(answers)→ Bangla text summary → fed to rag_engine (Gemini)
  4. assess(answers)       → rule-based severity, risk level, confidence,
                             emergency flag  (deterministic → thesis metrics)

Flow:
    welcome → reporter → age → gender → division/district
      → category multi-select
      → follow-ups (ONLY for selected categories)
      → abuser (family? → relation)
      → risk (ongoing? safe place?)
      → optional free voice
      → [analysis + result]  → consent to save
"""

import json
from pathlib import Path
from typing import Any

BANK_PATH = Path(__file__).parent.parent / "phase1_outputs" / "question_bank.json"

RISK_LABEL_BN = {1: "কম", 2: "মাঝারি", 3: "উচ্চ", 4: "খুব উচ্চ", 5: "জরুরি"}


class QuestionEngineError(Exception):
    pass


class QuestionEngine:
    def __init__(self, bank_path: str | Path = BANK_PATH):
        p = Path(bank_path)
        if not p.exists():
            raise FileNotFoundError(f"question_bank.json not found: {p}")
        with open(p, encoding="utf-8") as f:
            self.bank: dict[str, Any] = json.load(f)

        self.categories     = self.bank["categories"]
        self.intro_screens  = self.bank["intro_screens"]
        self.category_sel   = self.bank["category_select"]
        self.followups      = self.bank["followups"]
        self.closing        = self.bank["closing_screens"]
        self.consent        = self.bank["consent_screen"]
        self.result_spec    = self.bank["result_spec"]
        self.ui_spec        = self.bank["ui_spec"]
        self.divisions      = self.bank["divisions"]

    # ── Public: category selector (with third-party filtering) ────────────────
    def category_options(self, reporter_type: str | None) -> list[dict[str, Any]]:
        """Category buttons; 'মৃত্যুর ঘটনা' only shown for third-party reports."""
        out = []
        for key, cat in self.categories.items():
            if cat.get("third_party_only") and reporter_type != "third_party":
                continue
            out.append({
                "key":      key,
                "label_bn": cat["label_bn"],
                "icon":     cat["icon"],
            })
        return out

    def districts_for(self, division: str) -> list[str]:
        return self.divisions.get(division, [])

    # ── The dynamic screen sequence for a given set of answers ────────────────
    def screen_sequence(self, answers: dict[str, Any]) -> list[dict[str, Any]]:
        """Full ordered list of screens implied by the current answers."""
        seq: list[dict[str, Any]] = list(self.intro_screens)

        # Category selector — options depend on reporter type
        sel = dict(self.category_sel)
        sel["options"] = self.category_options(answers.get("reporter_type"))
        seq.append(sel)

        # Follow-ups only for selected categories (bank order = stable order)
        selected = answers.get("selected_categories") or []
        for cat_key in self.categories:
            if cat_key in selected:
                for q in self.followups.get(cat_key, []):
                    scr = dict(q)
                    scr["category"] = cat_key
                    seq.append(scr)

        # Closing screens with show_if conditions
        for scr in self.closing:
            cond = scr.get("show_if")
            if cond:
                val = answers.get(cond["field"])
                if val is None or val != cond["equals"]:
                    continue
            seq.append(scr)

        return seq

    def _answer_key(self, screen: dict[str, Any]) -> str:
        """
        Which key in `answers` stores this screen's response.

        Every screen — welcome included — declares its own `field` in the bank,
        so the client can always derive the key from the screen it was handed.
        A screen that only had an `id` would loop forever: the client would store
        the answer under the id while the engine looked for it elsewhere.
        """
        return screen.get("field") or screen["id"]

    def next_screen(self, answers: dict[str, Any]) -> dict[str, Any] | None:
        """
        The next screen the user should see.
        Returns None when the question flow is complete (→ run analysis).
        """
        for screen in self.screen_sequence(answers):
            key = self._answer_key(screen)
            if key not in answers:
                return screen
        return None   # flow complete

    # ── Progress bar ──────────────────────────────────────────────────────────
    def progress(self, answers: dict[str, Any]) -> dict[str, Any]:
        seq = [s for s in self.screen_sequence(answers) if s["type"] != "welcome"]
        total = len(seq)
        done  = sum(1 for s in seq if self._answer_key(s) in answers)
        pct   = int(round(done / total * 100)) if total else 0
        filled = round(pct / 10)
        return {
            "current": done,
            "total":   total,
            "percent": pct,
            "bar":     "█" * filled + "░" * (10 - filled),
        }

    # ── Bangla summary → fed to rag_engine (Gemini) ───────────────────────────
    def build_summary(self, answers: dict[str, Any]) -> str:
        yn = lambda v: "হ্যাঁ" if v else "না"
        lines: list[str] = []

        reporter = answers.get("reporter_type")
        lines.append(
            "রিপোর্টকারী: " +
            ("ভুক্তভোগী নিজে" if reporter == "self"
             else "অন্য একজন (প্রতিবেশী/সাহায্যকারী)" if reporter == "third_party"
             else "অজানা")
        )
        if answers.get("is_elder") is not None:
            lines.append(f"বয়স প্রায় ৬০ বা তার বেশি: {yn(answers['is_elder'])}")

        gender_bn = {"male": "পুরুষ", "female": "মহিলা", "undisclosed": "বলতে চাননি"}
        if answers.get("gender"):
            lines.append(f"ভুক্তভোগী: {gender_bn.get(answers['gender'], 'অজানা')}")

        loc = answers.get("location") or {}
        if loc.get("district"):
            lines.append(f"এলাকা: {loc.get('district')}, {loc.get('division', '')}".strip(", "))

        selected = answers.get("selected_categories") or []
        if selected:
            names = [self.categories[c]["label_bn"] for c in selected if c in self.categories]
            lines.append("")
            lines.append("যে সমস্যাগুলো বেছে নেওয়া হয়েছে: " + ", ".join(names))

        # Per-category answers
        for cat_key in self.categories:
            if cat_key not in selected:
                continue
            qs = self.followups.get(cat_key, [])
            answered = [(q, answers.get(q["id"])) for q in qs if q["id"] in answers]
            if not answered:
                continue
            lines.append("")
            lines.append(f"{self.categories[cat_key]['label_bn']}:")
            for q, val in answered:
                lines.append(f"  - {q['text_bn']} → {yn(val)}")

        # Abuser
        lines.append("")
        if answers.get("abuser_is_family") is not None:
            fam = "পরিবারের সদস্য" if answers["abuser_is_family"] else "পরিবারের বাইরের কেউ"
            rel = answers.get("abuser_relation")
            rel_bn = self._relation_bn(rel)
            lines.append(f"নির্যাতনকারী: {fam}" + (f" — {rel_bn}" if rel_bn else ""))

        # Risk
        if answers.get("ongoing") is not None:
            lines.append(f"নির্যাতন এখনো চলছে: {yn(answers['ongoing'])}")
        if answers.get("needs_safe_place") is not None:
            lines.append(f"এখনই নিরাপদ জায়গায় যাওয়ার প্রয়োজন: {yn(answers['needs_safe_place'])}")

        extra = (answers.get("extra_detail") or "").strip()
        if extra:
            lines.append("")
            lines.append(f"ভুক্তভোগীর নিজের ভাষায় অতিরিক্ত বিবরণ: {extra}")

        return "\n".join(lines)

    def _relation_bn(self, rel: str | None) -> str:
        if not rel:
            return ""
        for scr in self.closing:
            for opt in scr.get("options", []):
                if opt["value"] == rel:
                    return opt["label_bn"]
        return rel

    # ── Rule-based assessment (deterministic → thesis metrics) ────────────────
    def assess(self, answers: dict[str, Any]) -> dict[str, Any]:
        """
        Rule-based severity / risk / confidence from the yes-no answers.
        Gemini (rag_engine) adds legal reasoning on top of this.
        """
        selected = answers.get("selected_categories") or []

        confirmed: list[str] = []       # categories with at least one 'yes'
        escalated = False               # hospital / property taken / medical denied
        emergency = False
        emergency_reasons: list[str] = []

        yes_count = 0
        asked_count = 0

        for cat_key in self.categories:
            if cat_key not in selected:
                continue
            has_yes = False
            for q in self.followups.get(cat_key, []):
                if q["id"] not in answers:
                    continue
                asked_count += 1
                if answers[q["id"]]:
                    yes_count += 1
                    has_yes = True
                    if q.get("escalates_severity"):
                        escalated = True
                    if q.get("emergency"):
                        emergency = True
                        emergency_reasons.append(q.get("emergency_action_bn", ""))
            if has_yes:
                confirmed.append(cat_key)

        # Base severity = highest severity among confirmed categories
        severity = max((self.categories[c]["severity"] for c in confirmed), default=0)

        risk = severity
        if escalated:
            risk += 1
        if answers.get("ongoing"):
            risk += 1

        if answers.get("needs_safe_place"):
            emergency = True
            emergency_reasons.append("জরুরি: এখনই ৯৯৯ নম্বরে কল করুন।")

        # Level 5 ("জরুরি") is reserved for a REAL emergency (death reported, or the
        # victim needs to reach safety now). Otherwise cap at 4 ("খুব উচ্চ") so the
        # label never says "জরুরি" without an emergency action attached.
        if not confirmed:
            risk = 1
        elif emergency:
            risk = 5
        else:
            risk = max(1, min(risk, 4))

        # Confidence: how clear the signal is (share of 'yes' among asked follow-ups)
        if asked_count == 0:
            confidence = 0.0
        else:
            ratio = yes_count / asked_count
            confidence = 0.55 + 0.45 * ratio if yes_count else 0.30
        confidence = round(min(confidence, 0.98), 2)

        laws: list[str] = []
        for c in confirmed:
            for law in self.categories[c]["laws"]:
                if law not in laws:
                    laws.append(law)

        return {
            "confirmed_categories": confirmed,
            "category_labels_bn":   [self.categories[c]["label_bn"] for c in confirmed],
            "severity":             severity,
            "risk_level":           risk,
            "risk_label_bn":        RISK_LABEL_BN.get(risk, "কম"),
            "confidence":           confidence,
            "confidence_percent":   int(round(confidence * 100)),
            "emergency":            emergency,
            "emergency_actions_bn": [r for r in emergency_reasons if r],
            "laws":                 laws,
            "trust_blind_spot":     bool(answers.get("abuser_is_family")),
        }

    # ── Anonymized record for Firestore (only if user consents) ───────────────
    def dashboard_record(self, answers: dict[str, Any],
                         assessment: dict[str, Any]) -> dict[str, Any]:
        """NO name / identity — only aggregate analytics fields."""
        loc = answers.get("location") or {}
        return {
            "abuse_types":     assessment["confirmed_categories"],
            "risk_level":      assessment["risk_level"],
            "severity":        assessment["severity"],
            "district":        loc.get("district"),
            "division":        loc.get("division"),
            "gender":          answers.get("gender"),
            "reporter_type":   answers.get("reporter_type"),
            "abuser_relation": answers.get("abuser_relation"),
            "abuser_is_family": answers.get("abuser_is_family"),
            "ongoing":         answers.get("ongoing"),
        }


# ── Module-level singleton ────────────────────────────────────────────────────
_engine: QuestionEngine | None = None


def get_engine() -> QuestionEngine:
    global _engine
    if _engine is None:
        _engine = QuestionEngine()
    return _engine


# ── CLI: simulate a full flow ─────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console: print Bangla

    e = get_engine()
    answers: dict[str, Any] = {
        "started": True,
        "reporter_type": "self",
        "is_elder": True,
        "gender": "female",
        "location": {"division": "ময়মনসিংহ", "district": "ময়মনসিংহ"},
        "selected_categories": ["physical", "neglect"],
        "P1": True, "P2": True,
        "N1": True, "N2": False,
        "abuser_is_family": True,
        "abuser_relation": "son",
        "ongoing": True,
        "needs_safe_place": False,
    }

    print("=== NEXT SCREEN ===")
    nxt = e.next_screen(answers)
    print(nxt["id"] if nxt else "FLOW COMPLETE")

    print("\n=== PROGRESS ===")
    print(e.progress(answers))

    print("\n=== BANGLA SUMMARY (→ Gemini) ===")
    print(e.build_summary(answers))

    print("\n=== RULE-BASED ASSESSMENT ===")
    a = e.assess(answers)
    for k, v in a.items():
        print(f"  {k:<22}: {v}")
