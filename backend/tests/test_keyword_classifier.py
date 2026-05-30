"""
Tests for backend/app/keyword_classifier.py

Run from backend/ folder:
    python -m pytest tests/test_keyword_classifier.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.keyword_classifier import (
    KeywordClassifier,
    classify,
    SEVERITY_MAP,
    LEGAL_SECTIONS,
)


@pytest.fixture(scope="module")
def clf():
    """Single classifier instance shared across tests."""
    return KeywordClassifier()


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY DETECTION — Pure Bangla
# ════════════════════════════════════════════════════════════════════════════════
class TestBanglaClassification:

    def test_physical_abuse_bangla(self, clf):
        text = "ছেলে আমাকে মারধর করেছে এবং আঘাত পেয়েছি"
        result = clf.classify(text)
        assert result['category'] == 'physical'
        assert result['severity'] == 4
        assert 'মারধর' in result['matched_keywords']

    def test_abandonment_bangla(self, clf):
        text = "ছেলে আমাকে বাড়ি থেকে বের করে দিয়েছে এবং রাস্তায় ফেলে গেছে"
        result = clf.classify(text)
        assert result['category'] == 'abandonment'
        assert result['severity'] == 3

    def test_neglect_bangla(self, clf):
        text = "তারা আমাকে খাবার দেয় না এবং ওষুধ দেয় না, যত্ন নেয় না"
        result = clf.classify(text)
        assert result['category'] == 'neglect'
        assert result['severity'] == 2

    def test_financial_bangla(self, clf):
        text = "ছেলে জোর করে জমির দলিল লিখিয়ে নিয়েছে এবং সম্পত্তি দখল করেছে"
        result = clf.classify(text)
        assert result['category'] == 'financial'
        assert result['severity'] == 2

    def test_verbal_bangla(self, clf):
        text = "ছেলে আমাকে গালি দেয় এবং অপমান করে, হুমকি দেয়"
        result = clf.classify(text)
        assert result['category'] == 'verbal'
        assert result['severity'] == 1

    def test_murder_bangla(self, clf):
        text = "ছেলে বাবাকে হত্যা করেছে এবং লাশ পুঁতে রেখেছে"
        result = clf.classify(text)
        assert result['category'] == 'murder'
        assert result['severity'] == 5


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY DETECTION — Pure English
# ════════════════════════════════════════════════════════════════════════════════
class TestEnglishClassification:

    def test_physical_abuse_english(self, clf):
        text = "Son beats his elderly father and causes injury hospital"
        result = clf.classify(text)
        assert result['category'] == 'physical'

    def test_abandonment_english(self, clf):
        text = "Mother was abandoned on the street by her children evicted"
        result = clf.classify(text)
        assert result['category'] == 'abandonment'

    def test_financial_english(self, clf):
        text = "Forced father to transfer property and land deed fraud"
        result = clf.classify(text)
        assert result['category'] == 'financial'

    def test_murder_english(self, clf):
        text = "Son murdered his father and buried the body"
        result = clf.classify(text)
        assert result['category'] == 'murder'


# ════════════════════════════════════════════════════════════════════════════════
# CATEGORY DETECTION — Mixed Banglish
# ════════════════════════════════════════════════════════════════════════════════
class TestMixedClassification:

    def test_mixed_physical(self, clf):
        text = "ছেলে আমাকে beat করেছে এবং hospital এ ভর্তি হতে হয়েছে"
        result = clf.classify(text)
        assert result['category'] == 'physical'

    def test_mixed_abandonment(self, clf):
        text = "Son আমাকে evict করে দিয়েছে এবং রাস্তায় থাকতে হচ্ছে"
        result = clf.classify(text)
        assert result['category'] == 'abandonment'


# ════════════════════════════════════════════════════════════════════════════════
# EDGE CASES
# ════════════════════════════════════════════════════════════════════════════════
class TestEdgeCases:

    def test_empty_text(self, clf):
        result = clf.classify("")
        assert result['category']   == 'unknown'
        assert result['severity']   == 0
        assert result['confidence'] == 0.0

    def test_whitespace_only(self, clf):
        result = clf.classify("    \n\t   ")
        assert result['category'] == 'unknown'

    def test_no_matching_keywords(self, clf):
        result = clf.classify("আজকে আকাশ মেঘলা এবং বৃষ্টি হচ্ছে")
        assert result['category'] == 'unknown'

    def test_multi_category_picks_top(self, clf):
        # Both physical and financial keywords present, but physical has more
        text = ("ছেলে আমাকে মারধর করেছে এবং চড় দিয়েছে, আঘাত করেছে, "
                "এছাড়াও সম্পত্তি নিয়েছে")
        result = clf.classify(text)
        assert result['category'] == 'physical'
        assert len(result['all_categories']) >= 2  # both detected

    def test_confidence_value_range(self, clf):
        text = "ছেলে আমাকে মারধর করেছে"
        result = clf.classify(text)
        assert 0.0 <= result['confidence'] <= 1.0


# ════════════════════════════════════════════════════════════════════════════════
# LEGAL SECTION + ACTION MAPPING
# ════════════════════════════════════════════════════════════════════════════════
class TestLegalMapping:

    def test_physical_has_correct_legal_sections(self, clf):
        result = clf.classify("ছেলে মারধর করেছে আঘাত")
        assert "PMA 2013 §3"  in result['legal_sections']
        assert "BPC §323"     in result['legal_sections']

    def test_murder_is_criminal(self, clf):
        result = clf.classify("ছেলে বাবাকে হত্যা করেছে")
        assert result['civil_or_criminal'] == 'Criminal'

    def test_neglect_is_civil(self, clf):
        result = clf.classify("খাবার দেয় না ওষুধ দেয় না অবহেলা")
        assert result['civil_or_criminal'] == 'Civil'

    def test_recommended_action_for_high_severity(self, clf):
        result = clf.classify("ছেলে বাবাকে হত্যা করেছে")
        assert "999" in result['recommended_action']

    def test_recommended_action_for_low_severity(self, clf):
        result = clf.classify("ছেলে গালি দেয় অপমান করে হুমকি")
        # Should mention NLASO or ইউনিয়ন পরিষদ for verbal
        action = result['recommended_action']
        assert "NLASO" in action or "ইউনিয়ন" in action


# ════════════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTION
# ════════════════════════════════════════════════════════════════════════════════
class TestEntityExtraction:

    def test_extracts_age_bangla(self, clf):
        text = "৭৫ বছরের বৃদ্ধ ছেলের মারধরের শিকার"
        result = clf.classify(text)
        assert result['entities']['age'] == 75

    def test_extracts_age_english(self, clf):
        text = "75 year old elderly father was beaten by son"
        result = clf.classify(text)
        assert result['entities']['age'] == 75

    def test_extracts_victim_relation(self, clf):
        text = "বাবাকে ছেলে মারধর করেছে"
        result = clf.classify(text)
        assert result['entities']['victim_relation'] == 'father'

    def test_extracts_abuser_relation(self, clf):
        text = "ছেলে বাবাকে মারধর করেছে"
        result = clf.classify(text)
        assert result['entities']['abuser_relation'] == 'son'

    def test_no_false_positive_mother_in_amake(self, clf):
        """'মা' inside 'আমাকে' should NOT match as mother (boundary check)."""
        text = "ছেলে আমাকে মারধর করেছে"   # speaker = self, no explicit mother
        result = clf.classify(text)
        assert result['entities']['victim_relation'] != 'mother'

    def test_ma_as_standalone_word_matches_mother(self, clf):
        """Real-world: people say 'মা' not 'মাতা'."""
        text = "ছেলে মাকে মারধর করেছে"
        result = clf.classify(text)
        assert result['entities']['victim_relation'] == 'mother'

    def test_mayer_genitive_matches_mother(self, clf):
        text = "মায়ের যত্ন নেয় না"
        result = clf.classify(text)
        assert result['entities']['victim_relation'] == 'mother'

    def test_mata_formal_matches_mother(self, clf):
        text = "ছেলে মাতাকে মারধর করেছে"
        result = clf.classify(text)
        assert result['entities']['victim_relation'] == 'mother'

    def test_no_false_match_inside_marodhor(self, clf):
        """মারধর starts with 'মা' but should NOT match mother."""
        text = "ছেলে আমাকে মারধর করেছে"
        result = clf.classify(text)
        assert result['entities']['victim_relation'] != 'mother'


# ════════════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL FUNCTION
# ════════════════════════════════════════════════════════════════════════════════
class TestModuleLevelClassify:

    def test_module_classify_works(self):
        """Module-level classify() function works without instance"""
        result = classify("ছেলে মারধর করেছে")
        assert result['category'] == 'physical'

    def test_severity_map_matches_all_categories(self):
        """SEVERITY_MAP has entries for all 6 main categories"""
        for cat in ['physical', 'abandonment', 'neglect', 'financial', 'verbal', 'murder']:
            assert cat in SEVERITY_MAP
            assert 1 <= SEVERITY_MAP[cat] <= 5

    def test_legal_sections_for_all_categories(self):
        """LEGAL_SECTIONS has entries for all categories"""
        for cat in ['physical', 'abandonment', 'neglect', 'financial', 'verbal', 'murder']:
            assert cat in LEGAL_SECTIONS
            assert len(LEGAL_SECTIONS[cat]) > 0
