"""
RAG Engine — Retrieval-Augmented legal advice (Option C: keyword retrieval + Gemini)

Pipeline:
    complaint text
        → KeywordClassifier (fast category guess, Phase 2)
        → retrieve relevant legal sections by category (from act_knowledge_base.json)
        → Gemini reads complaint + retrieved sections
        → structured legal advice (Bangla + English)

Why keyword retrieval (not vector/ChromaDB):
    - Knowledge base is small (16 short sections) — fits in Gemini context
    - Bangla embedding models showed weak discrimination (tested)
    - No 1GB model to deploy → runs on free-tier hosting
    - Gemini itself handles Whisper typos ("মার্ধুর" → understands "মারধর")

Gemini handles spelling variations / typos / paraphrases that exact keyword
matching cannot — this is what solves the Phase 2 "unknown" problem.
"""

import json
import os
import re
from pathlib import Path
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv

from .keyword_classifier import KeywordClassifier
from .whisper_service import detect_language_mode
from .entity_extractor import normalize_entities, empty_entities

load_dotenv(Path(__file__).parent.parent / ".env")


# ── Constants ─────────────────────────────────────────────────────────────────
KB_PATH      = Path(__file__).parent.parent / "phase1_outputs" / "act_knowledge_base.json"
GEMINI_MODEL = "gemini-2.5-flash"

# Procedural sections (applicable_for == ['all']) that are always useful context
# for advice — complaint procedure + penalty + emergency. Definitions/short-title
# are skipped to keep the prompt focused.
ALWAYS_INCLUDE = {"pma_sec5", "pma_sec7", "pma_sec8"}

# Shown on every result screen — never overstate the AI's certainty.
DISCLAIMER_BN = (
    "এই ফলাফলটি আপনার দেওয়া উত্তরের ভিত্তিতে AI বিশ্লেষণ করে তৈরি করা হয়েছে। "
    "এটি চূড়ান্ত আইনি সিদ্ধান্ত নয়।"
)


# ── Exceptions ────────────────────────────────────────────────────────────────
class RagEngineError(Exception):
    """Base error for RAG engine."""


class GeminiKeyMissingError(RagEngineError):
    """GOOGLE_API_KEY not set in environment."""


class GeminiAPIError(RagEngineError):
    """Gemini API call failed."""


# ── Engine ────────────────────────────────────────────────────────────────────
class RagEngine:
    """Loads knowledge base + classifier once; analyzes complaints via Gemini."""

    def __init__(self, model_name: str = GEMINI_MODEL):
        if not KB_PATH.exists():
            raise FileNotFoundError(f"Knowledge base not found: {KB_PATH}")
        with open(KB_PATH, encoding="utf-8") as f:
            self.kb: dict[str, Any] = json.load(f)

        self.classifier = KeywordClassifier()

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key.startswith("your_"):
            raise GeminiKeyMissingError(
                "GOOGLE_API_KEY not set. Add it to backend/.env"
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name,
            generation_config={"response_mime_type": "application/json"},
        )

    # ── Retrieval (keyword/category based) ────────────────────────────────────
    def _retrieve(self, category: str) -> list[dict[str, Any]]:
        """
        Select relevant legal sections for a category.

        - Known category → substantive sections for that category + key procedural
        - Unknown        → all sections (let Gemini decide)
        """
        selected: list[dict[str, Any]] = []
        for key, val in self.kb.items():
            applicable = val.get("applicable_for", [])
            is_substantive_match = category != "unknown" and category in applicable
            is_always = key in ALWAYS_INCLUDE
            is_unknown_include = category == "unknown" and "all" not in applicable

            if is_substantive_match or is_always or is_unknown_include:
                selected.append({
                    "id":      key,
                    "section": val.get("section", ""),
                    "text":    val.get("text", ""),
                    "text_en": val.get("text_english", ""),
                })

        # Fallback: if nothing matched (shouldn't happen), include everything
        if not selected:
            for key, val in self.kb.items():
                selected.append({
                    "id":      key,
                    "section": val.get("section", ""),
                    "text":    val.get("text", ""),
                    "text_en": val.get("text_english", ""),
                })
        return selected

    # ── Prompt building ───────────────────────────────────────────────────────
    @staticmethod
    def _build_prompt(text: str, category_hint: str, language_mode: str,
                      sections: list[dict[str, Any]]) -> str:
        context = "\n\n".join(
            f"[{s['id']}] {s['section']}\n"
            f"বাংলা: {s['text']}\n"
            f"English: {s['text_en']}"
            for s in sections
        )

        if language_mode == "english":
            lang_rule = "Write legal_advice and recommended_action primarily in English."
        elif language_mode == "bangla":
            lang_rule = "legal_advice ও recommended_action প্রধানত বাংলায় লেখো।"
        else:
            lang_rule = "Provide both Bangla and English in the respective fields."

        return f"""তুমি বাংলাদেশের একজন আইনি সহায়তা AI, যে বৃদ্ধ নির্যাতন (elder abuse) নিয়ে কাজ করে।

গুরুত্বপূর্ণ নির্দেশনা:
- নিচের complaint টি voice-to-text থেকে এসেছে, তাই বানান ভুল থাকতে পারে
  (যেমন "মার্ধুর" = "মারধর", "বারি" = "বাড়ি")। অর্থ বুঝে নাও।
- শুধুমাত্র নিচে দেওয়া আইনি ধারাগুলোর ভিত্তিতে উত্তর দাও। কোনো ধারা বানিয়ো না।
- যদি complaint এ একাধিক ধরনের নির্যাতন থাকে, সবগুলো উল্লেখ করো।
- {lang_rule}

কে রিপোর্ট করছে (reporter_type) নির্ধারণ করো এবং সেই অনুযায়ী পরামর্শ দাও:
  "self"        → ভুক্তভোগী নিজে। PMA 2013 ও BPC দুইটাই প্রযোজ্য।
  "third_party" → অন্য কেউ (প্রতিবেশী/NGO/নাগরিক)। গুরুত্বপূর্ণ:
       • শারীরিক নির্যাতন/হত্যা (criminal, cognizable) → যে কেউ সরাসরি
         থানায় FIR বা 999 এ কল করতে পারে — এটা পরামর্শে বলো।
       • ভরণপোষণ/পরিত্যাগ (PMA, civil) → আইন অনুযায়ী শুধু পিতা-মাতা নিজে
         UNO তে অভিযোগ করতে পারেন। তাই reporter কে বলো ভুক্তভোগীকে অভিযোগ
         দাখিলে সাহায্য করতে, অথবা NLASO (16430)/NGO কে জানাতে যারা হস্তক্ষেপ করতে পারে।
  "unknown"     → বোঝা না গেলে।
- ভুক্তভোগীর নাম/বয়স/ঠিকানা অভিযোগে না থাকলে null দাও, অনুমান করবে না।

প্রাথমিক keyword-ভিত্তিক অনুমান (hint মাত্র, ভুল হতে পারে): {category_hint}

=== প্রযোজ্য আইনি ধারাসমূহ ===
{context}

=== অভিযোগ (Complaint) ===
{text}

নিচের JSON format-এ উত্তর দাও (শুধু JSON, অন্য কিছু নয়):
{{
  "abuse_type": "শনাক্তকৃত নির্যাতনের ধরন (যেমন: Physical Abuse, Financial Exploitation, Abandonment, Neglect, Verbal Abuse, Murder, বা একাধিক)",
  "applicable_sections": ["প্রযোজ্য ধারার তালিকা, যেমন PMA 2013 Section 3, BPC Section 323"],
  "severity": "1 থেকে 5 (1=verbal, 2=financial/neglect, 3=abandonment, 4=physical, 5=murder)",
  "legal_advice_bangla": "বাংলায় বিস্তারিত আইনি পরামর্শ",
  "legal_advice_english": "Legal advice in English",
  "recommended_action_bangla": "করণীয় পদক্ষেপ বাংলায় (reporter_type অনুযায়ী)",
  "recommended_action_english": "Recommended steps in English",
  "civil_or_criminal": "Civil, Criminal, বা Both",
  "urgency": "1 থেকে 5",
  "reporter_type": "self | third_party | unknown",
  "victim_name": "ভুক্তভোগীর নাম বা null",
  "victim_age": "বয়স সংখ্যায় বা null",
  "victim_gender": "Male | Female | null",
  "location": "এলাকা/জেলা/ঠিকানা বা null",
  "abuser_name": "নির্যাতনকারীর নাম বা null",
  "abuser_relation": "সম্পর্ক যেমন ছেলে/মেয়ে/পুত্রবধূ বা null",
  "incident_date": "তারিখ বা null"
}}"""

    # ── Public API ────────────────────────────────────────────────────────────
    def analyze(self, text: str, language_mode: str | None = None) -> dict[str, Any]:
        """
        Full RAG analysis of a complaint.

        Returns:
            {
              "keyword_category": "physical",     # fast first-pass
              "language_mode":    "bangla",
              "retrieved_ids":    ["bpc_323", ...],
              "abuse_type":       "Physical Abuse",
              "applicable_sections": [...],
              "severity":         4,
              "legal_advice_bangla":  "...",
              "legal_advice_english": "...",
              "recommended_action_bangla":  "...",
              "recommended_action_english": "...",
              "civil_or_criminal": "Criminal",
              "urgency":           4
            }
        """
        if not text or not text.strip():
            raise RagEngineError("Empty complaint text")

        if language_mode is None:
            language_mode = detect_language_mode(text)

        classification = self.classifier.classify(text)
        category = classification["category"]
        sections = self._retrieve(category)

        prompt = self._build_prompt(text, category, language_mode, sections)

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise GeminiAPIError(f"Gemini API call failed: {e}") from e

        parsed = self._parse_json(response.text)

        # Normalize severity/urgency to int
        def _to_int(v, default):
            try:
                return int(str(v).strip())
            except (ValueError, TypeError):
                return default

        # Entities + reporter_type come from the SAME Gemini call (Option B)
        entities = normalize_entities(parsed)

        return {
            "keyword_category":          category,
            "language_mode":             language_mode,
            "retrieved_ids":             [s["id"] for s in sections],
            "abuse_type":                parsed.get("abuse_type", "Unknown"),
            "applicable_sections":       parsed.get("applicable_sections", []),
            "severity":                  _to_int(parsed.get("severity"),
                                                 classification.get("severity", 1)),
            "legal_advice_bangla":       parsed.get("legal_advice_bangla", ""),
            "legal_advice_english":      parsed.get("legal_advice_english", ""),
            "recommended_action_bangla": parsed.get("recommended_action_bangla", ""),
            "recommended_action_english":parsed.get("recommended_action_english", ""),
            "civil_or_criminal":         parsed.get("civil_or_criminal", "Unknown"),
            "urgency":                   _to_int(parsed.get("urgency"),
                                                 classification.get("severity", 1)),
            "reporter_type":             entities["reporter_type"],
            "entities":                  entities,
        }

    # ── Guided-assessment analysis (the main path in the new Q&A flow) ────────
    def analyze_assessment(self, summary_bn: str,
                           assessment: dict[str, Any]) -> dict[str, Any]:
        """
        Analyse a guided yes/no assessment.

        Args:
            summary_bn : Bangla summary of the user's answers
                         (from question_engine.build_summary)
            assessment : rule-based result from question_engine.assess()
                         (confirmed categories, severity, risk, confidence, laws)

        Gemini adds on top of the deterministic rules:
            - legal reasoning grounded ONLY in the retrieved sections
            - an explanation that quotes the user's OWN answers
            - সম্ভাব্য কারণ (likely underlying causes)
            - concrete next steps

        Returns a dict ready for the result screen.
        """
        if not summary_bn or not summary_bn.strip():
            raise RagEngineError("Empty assessment summary")

        confirmed = assessment.get("confirmed_categories") or []

        # Retrieve legal sections for every confirmed category (+ procedural ones)
        sections: list[dict[str, Any]] = []
        seen: set[str] = set()
        for cat in (confirmed or ["unknown"]):
            for s in self._retrieve(cat):
                if s["id"] not in seen:
                    seen.add(s["id"])
                    sections.append(s)

        prompt = self._build_assessment_prompt(summary_bn, assessment, sections)

        try:
            response = self.model.generate_content(prompt)
        except Exception as e:
            raise GeminiAPIError(f"Gemini API call failed: {e}") from e

        parsed = self._parse_json(response.text)

        return {
            # deterministic (from the rule engine) — used for metrics
            "abuse_types":          confirmed,
            "abuse_type_bn":        parsed.get("abuse_type_bn")
                                    or " ও ".join(assessment.get("category_labels_bn", []))
                                    or "নির্ধারণ করা যায়নি",
            "severity":             assessment.get("severity", 0),
            "risk_level":           assessment.get("risk_level", 1),
            "risk_label_bn":        assessment.get("risk_label_bn", "কম"),
            "confidence_percent":   assessment.get("confidence_percent", 0),
            "emergency":            assessment.get("emergency", False),
            "emergency_actions_bn": assessment.get("emergency_actions_bn", []),
            "trust_blind_spot":     assessment.get("trust_blind_spot", False),
            # from Gemini
            "applicable_sections":  self._readable_sections(
                                        parsed.get("applicable_sections")
                                        or assessment.get("laws", [])),
            "explanation_bn":       parsed.get("explanation_bn", ""),
            "possible_causes_bn":   parsed.get("possible_causes_bn", []),
            "recommendations_bn":   parsed.get("recommendations_bn", []),
            "civil_or_criminal":    parsed.get("civil_or_criminal", "Unknown"),
            "disclaimer_bn":        DISCLAIMER_BN,
            "retrieved_ids":        [s["id"] for s in sections],
        }

    def _readable_sections(self, sections: list[str]) -> list[str]:
        """
        Turn any knowledge-base id into its human title.

        The result screen is read aloud to an elder, so "pma_sec3" must never
        reach it. Ids can arrive either from Gemini or from the rule engine's
        fallback list, so both paths go through here. Anything that isn't a known
        id is already a title and passes through unchanged.
        """
        out: list[str] = []
        for s in sections:
            entry = self.kb.get(s)
            title = entry.get("section") if entry else s
            if title and title not in out:
                out.append(title)
        return out

    @staticmethod
    def _build_assessment_prompt(summary_bn: str, assessment: dict[str, Any],
                                 sections: list[dict[str, Any]]) -> str:
        context = "\n\n".join(
            f"[{s['id']}] {s['section']}\nবাংলা: {s['text']}\nEnglish: {s['text_en']}"
            for s in sections
        )
        cats = ", ".join(assessment.get("category_labels_bn", [])) or "কিছু শনাক্ত হয়নি"

        return f"""তুমি বাংলাদেশের একজন আইনি সহায়তা AI, যে বৃদ্ধ নির্যাতন (elder abuse) নিয়ে কাজ করে।

ব্যবহারকারী কিছু সহজ হ্যাঁ/না প্রশ্নের উত্তর দিয়েছেন। নিচে তার উত্তরের সারাংশ দেওয়া হলো।

গুরুত্বপূর্ণ নির্দেশনা:
- শুধুমাত্র নিচে দেওয়া আইনি ধারাগুলোর ভিত্তিতে উত্তর দাও। কোনো ধারা বানিয়ো না।
- ব্যাখ্যায় ব্যবহারকারীর **নিজের উত্তর উদ্ধৃত করো** ("আপনি বলেছেন ...")।
- সব উত্তর **সহজ বাংলায়** দাও — বৃদ্ধ মানুষ যেন বোঝেন।
- "সম্ভাব্য কারণ" — এই ধরনের নির্যাতনের পেছনে সাধারণত যে কারণ থাকে
  (যেমন: পারিবারিক দ্বন্দ্ব, সম্পত্তি বিরোধ, আর্থিক নির্ভরশীলতা, মাদকাসক্তি)।
  অনুমান হিসেবে দাও, নিশ্চিত দাবি নয়।
- "applicable_sections" — শুধুমাত্র সেই ধারাগুলো দাও যেগুলো **লঙ্ঘিত হয়েছে**
  (যেমন ভরণ-পোষণের বাধ্যবাধকতা, পরিত্যাগ নিষেধ, আঘাত)। অভিযোগ **পদ্ধতি**
  (§5), **শাস্তি** (§7) বা **জরুরি সহায়তা** (§8) সংক্রান্ত ধারা এখানে দিয়ো না —
  সেগুলো করণীয় অংশে উল্লেখ করো।
- "recommendations_bn" — সর্বোচ্চ ৪টি, প্রতিটি ছোট ও সহজ বাক্যে (বৃদ্ধ শুনে
  বুঝবেন)। নম্বর দিয়ো না — শুধু বাক্য।

=== নিয়ম-ভিত্তিক প্রাথমিক বিশ্লেষণ (deterministic) ===
শনাক্তকৃত ধরন : {cats}
ঝুঁকির মাত্রা  : {assessment.get('risk_label_bn')} ({assessment.get('risk_level')}/5)
জরুরি অবস্থা   : {"হ্যাঁ" if assessment.get('emergency') else "না"}

=== প্রযোজ্য আইনি ধারাসমূহ ===
{context}

=== ব্যবহারকারীর উত্তরের সারাংশ ===
{summary_bn}

নিচের JSON format-এ উত্তর দাও (শুধু JSON):
{{
  "abuse_type_bn": "শনাক্তকৃত নির্যাতনের ধরন বাংলায় (যেমন: শারীরিক নির্যাতন ও অবহেলা)",
  "applicable_sections": ["প্রযোজ্য ধারার তালিকা, যেমন PMA 2013 §3, দণ্ডবিধি §323"],
  "explanation_bn": "কেন এই সিদ্ধান্ত — ব্যবহারকারীর উত্তর উদ্ধৃত করে ২-৪ বাক্যে",
  "possible_causes_bn": ["সম্ভাব্য কারণ ১", "সম্ভাব্য কারণ ২", "সম্ভাব্য কারণ ৩"],
  "recommendations_bn": ["করণীয় ১", "করণীয় ২", "করণীয় ৩"],
  "civil_or_criminal": "Civil | Criminal | Both"
}}"""

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        """Parse Gemini JSON output, with a regex fallback."""
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


# ── Module-level singleton ────────────────────────────────────────────────────
_engine: RagEngine | None = None


def get_engine() -> RagEngine:
    global _engine
    if _engine is None:
        _engine = RagEngine()
    return _engine


def analyze(text: str, language_mode: str | None = None) -> dict[str, Any]:
    """Module-level shortcut."""
    return get_engine().analyze(text, language_mode)


# ── CLI for manual test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "ছেলে আমাকে মার্ধুর করেছে এবং বারি থেকে বের করে দিয়েছে"

    print(f"Complaint: {q}\n")
    result = analyze(q)
    print(f"Keyword category : {result['keyword_category']}")
    print(f"Language mode    : {result['language_mode']}")
    print(f"Retrieved        : {result['retrieved_ids']}")
    print(f"Abuse type       : {result['abuse_type']}")
    print(f"Sections         : {result['applicable_sections']}")
    print(f"Severity         : {result['severity']}")
    print(f"Civil/Criminal   : {result['civil_or_criminal']}")
    print(f"\nAdvice (Bangla)  : {result['legal_advice_bangla']}")
    print(f"\nAction (Bangla)  : {result['recommended_action_bangla']}")
