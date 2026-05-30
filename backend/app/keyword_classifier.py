"""
Keyword Classifier — Text → Abuse Category + Severity + Legal Section

Uses keyword_dictionary.json (Phase 1 Step 3) to do fast offline classification
before the RAG engine kicks in (Phase 3).

Multilingual: handles Bangla, English, and Mixed (Banglish) text.
"""

import json
import re
from pathlib import Path
from typing import Any


# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_DICT_PATH = Path(__file__).parent.parent / "phase1_outputs" / "keyword_dictionary.json"

SEVERITY_MAP = {
    "murder":      5,
    "physical":    4,
    "abandonment": 3,
    "neglect":     2,
    "financial":   2,
    "verbal":      1,
}

LEGAL_SECTIONS = {
    "murder":      ["BPC §302", "BPC §304"],
    "physical":    ["PMA 2013 §3", "BPC §323", "BPC §324"],
    "abandonment": ["PMA 2013 §3", "PMA 2013 §4"],
    "neglect":     ["PMA 2013 §4"],
    "financial":   ["BPC §406", "BPC §420"],
    "verbal":      ["BPC §506"],
    "unknown":     [],
}

CIVIL_OR_CRIMINAL = {
    "murder":      "Criminal",
    "physical":    "Criminal",
    "abandonment": "Civil",
    "neglect":     "Civil",
    "financial":   "Both",
    "verbal":      "Criminal",
    "unknown":     "Unknown",
}

RECOMMENDED_ACTIONS = {
    5: "জরুরি! এখনই 999 এ কল করুন এবং পুলিশ স্টেশনে FIR করুন।",
    4: "নিকটতম পুলিশ স্টেশনে FIR দাখিল করুন এবং UNO অফিসে অভিযোগ জানান।",
    3: "UNO অফিসে অভিযোগ দাখিল করুন (PMA 2013 ধারা ৫ অনুযায়ী)।",
    2: "UNO অফিসে অভিযোগ এবং NLASO (16430) থেকে বিনামূল্যে আইনি সহায়তা নিন।",
    1: "ইউনিয়ন পরিষদ চেয়ারম্যানের কাছে আপোষ মীমাংসা চেষ্টা করুন; NLASO পরামর্শ নিন।",
}


# ── Classifier Class ──────────────────────────────────────────────────────────
class KeywordClassifier:
    """Loads keyword_dictionary.json once and classifies input text."""

    def __init__(self, dict_path: str | Path = DEFAULT_DICT_PATH):
        self.dict_path = Path(dict_path)
        if not self.dict_path.exists():
            raise FileNotFoundError(
                f"keyword_dictionary.json not found at: {self.dict_path}"
            )
        with open(self.dict_path, encoding="utf-8") as f:
            self.keywords: dict[str, dict[str, list[str]]] = json.load(f)

    # ── Public API ────────────────────────────────────────────────────────────
    def classify(self, text: str) -> dict[str, Any]:
        """
        Classify text into abuse category with severity + legal mapping.

        Returns:
            {
                "category":           "physical",
                "all_categories":     {"physical": 3, "abandonment": 1},
                "severity":           4,
                "confidence":         0.75,
                "matched_keywords":   ["মারধর", "আঘাত"],
                "legal_sections":     ["PMA 2013 §3", "BPC §323"],
                "civil_or_criminal":  "Criminal",
                "recommended_action": "নিকটতম পুলিশ স্টেশনে FIR...",
                "entities":           {"age": 70, "relation": "ছেলে"}
            }
        """
        if not text or not text.strip():
            return self._empty_result()

        text_lower = text.lower()

        # Score each category
        scores:  dict[str, int]       = {}
        matched: dict[str, list[str]] = {}

        for category, kw_group in self.keywords.items():
            all_kw = (
                kw_group.get("bangla",      []) +
                kw_group.get("english",     []) +
                kw_group.get("mixed_forms", [])
            )
            hits = [kw for kw in all_kw if kw.lower() in text_lower]
            if hits:
                scores[category]  = len(hits)
                matched[category] = hits

        if not scores:
            return self._unknown_result(text)

        # Top category — if tie, pick the one with higher severity
        top_category = max(
            scores.keys(),
            key=lambda c: (scores[c], SEVERITY_MAP.get(c, 0))
        )
        total      = sum(scores.values())
        confidence = round(scores[top_category] / total, 2)

        severity = SEVERITY_MAP.get(top_category, 1)

        return {
            "category":           top_category,
            "all_categories":     scores,
            "severity":           severity,
            "confidence":         confidence,
            "matched_keywords":   matched[top_category],
            "legal_sections":     LEGAL_SECTIONS.get(top_category, []),
            "civil_or_criminal":  CIVIL_OR_CRIMINAL.get(top_category, "Unknown"),
            "recommended_action": RECOMMENDED_ACTIONS.get(severity, ""),
            "entities":           self._extract_entities(text),
        }

    # ── Private helpers ───────────────────────────────────────────────────────
    def _empty_result(self) -> dict[str, Any]:
        return {
            "category":           "unknown",
            "all_categories":     {},
            "severity":           0,
            "confidence":         0.0,
            "matched_keywords":   [],
            "legal_sections":     [],
            "civil_or_criminal":  "Unknown",
            "recommended_action": "টেক্সট খালি — আবার চেষ্টা করুন।",
            "entities":           {},
        }

    def _unknown_result(self, text: str) -> dict[str, Any]:
        return {
            "category":           "unknown",
            "all_categories":     {},
            "severity":           0,
            "confidence":         0.0,
            "matched_keywords":   [],
            "legal_sections":     [],
            "civil_or_criminal":  "Unknown",
            "recommended_action": "নির্যাতনের ধরন স্পষ্ট নয়। NLASO (16430) এ কল করুন পরামর্শের জন্য।",
            "entities":           self._extract_entities(text),
        }

    def _extract_entities(self, text: str) -> dict[str, Any]:
        """Basic entity extraction using regex. RAG (Phase 3) will improve this."""
        entities: dict[str, Any] = {
            "age":               None,
            "victim_relation":   None,
            "abuser_relation":   None,
        }

        # ── Age: look for digits near বছর/years/age ─────────────────────────
        bn_digit_map = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
        text_for_age = text.translate(bn_digit_map)
        age_match = re.search(
            r"(\d{2,3})\s*(?:বছর|years?\s*old|years?|age)",
            text_for_age,
            re.IGNORECASE,
        )
        if age_match:
            age = int(age_match.group(1))
            if 30 <= age <= 120:
                entities["age"] = age

        # ── Victim relation (the elderly person) ────────────────────────────
        # English terms use \b (word boundary), Bangla terms use plain substring
        # because \b in Python's re doesn't work for non-ASCII characters.
        # Bangla terms = exact word forms (including common case suffixes).
        # We use token-based matching so "মা" matches the WORD "মা" but NOT
        # the substring inside "আমাকে" / "মারধর" / "মানুষ".
        victim_patterns = {
            "grandfather":  ([r"\b(grandfather|grandpa)\b"],
                             {"দাদা", "দাদাকে", "দাদার", "দাদু", "নানা", "নানাকে", "নানার"}),
            "grandmother":  ([r"\b(grandmother|grandma)\b"],
                             {"দাদি", "দাদিকে", "দাদির", "দিদা", "নানি", "নানিকে", "নানির"}),
            "father":       ([r"\bfather\b"],
                             {"বাবা", "বাবাকে", "বাবার", "পিতা", "পিতাকে", "পিতার", "আব্বা", "আব্বাকে"}),
            "mother":       ([r"\bmother\b"],
                             {"মা", "মাকে", "মার", "মায়", "মায়ের", "মাতা", "মাতাকে", "মাতার", "আম্মা", "আম্মাকে"}),
            "elderly":      ([r"\b(elderly|old)\b"],
                             {"বৃদ্ধ", "বৃদ্ধা", "বৃদ্ধার", "বৃদ্ধাকে", "বৃদ্ধকে", "বৃদ্ধের", "বুড়ো", "বুড়ি"}),
        }
        for rel, (en_patterns, bn_word_set) in victim_patterns.items():
            if self._match_any(text, en_patterns, bn_word_set):
                entities["victim_relation"] = rel
                break

        # ── Abuser relation ─────────────────────────────────────────────────
        abuser_patterns = {
            "daughter-in-law":  ([r"\bdaughter-in-law\b"],
                                 {"পুত্রবধূ", "পুত্রবধূকে", "পুত্রবধূর", "বউমা", "বউমাকে"}),
            "son-in-law":       ([r"\bson-in-law\b"],
                                 {"জামাই", "জামাইকে", "জামাইয়ের"}),
            "daughter":         ([r"\bdaughter\b"],
                                 {"মেয়ে", "মেয়েকে", "মেয়ের", "মেয়েটি", "মেয়েটা", "কন্যা", "কন্যাকে"}),
            "son":              ([r"\bson\b"],
                                 {"ছেলে", "ছেলেকে", "ছেলের", "ছেলেটি", "ছেলেটা", "পুত্র", "পুত্রকে"}),
            "spouse":           ([r"\b(husband|wife)\b"],
                                 {"স্বামী", "স্বামীকে", "স্বামীর", "স্ত্রী", "স্ত্রীকে", "স্ত্রীর"}),
            "neighbor":         ([r"\bneighbor\b"],
                                 {"প্রতিবেশী", "প্রতিবেশীকে", "প্রতিবেশীর"}),
            "relative":         ([r"\brelative\b"],
                                 {"আত্মীয়", "আত্মীয়কে", "আত্মীয়ের", "আত্মীয়স্বজন"}),
        }
        for rel, (en_patterns, bn_word_set) in abuser_patterns.items():
            if self._match_any(text, en_patterns, bn_word_set):
                entities["abuser_relation"] = rel
                break

        return entities

    @staticmethod
    def _match_any(text: str, en_regex_patterns: list[str], bn_word_set: set[str]) -> bool:
        """True if text matches any English regex OR contains any Bangla word as a token."""
        # English: regex with \b word boundaries
        for pat in en_regex_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        # Bangla: tokenize by whitespace + strip punctuation, then exact match.
        # This avoids "মা" inside "আমাকে" / "মারধর" matching falsely.
        tokens = re.split(r"\s+", text)
        bangla_punct = "।,.;:!?\"'()[]{}—–-"
        for tok in tokens:
            cleaned = tok.strip(bangla_punct)
            if cleaned in bn_word_set:
                return True
        return False


# ── Module-level convenience function ─────────────────────────────────────────
_default_classifier: KeywordClassifier | None = None


def classify(text: str) -> dict[str, Any]:
    """Module-level shortcut using default keyword_dictionary.json"""
    global _default_classifier
    if _default_classifier is None:
        _default_classifier = KeywordClassifier()
    return _default_classifier.classify(text)


# ── CLI for quick test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "ছেলে আমাকে মারধর করেছে এবং বাড়ি থেকে বের করে দিয়েছে"

    result = classify(text)
    print(f"\nInput: {text}\n")
    print(f"Category   : {result['category']}  (severity {result['severity']})")
    print(f"Confidence : {result['confidence']:.0%}")
    print(f"Matched    : {result['matched_keywords']}")
    print(f"Legal      : {', '.join(result['legal_sections'])}")
    print(f"Type       : {result['civil_or_criminal']}")
    print(f"Action     : {result['recommended_action']}")
    if any(result['entities'].values()):
        print(f"Entities   : {result['entities']}")
