"""
PDF Generator — Bangla complaint letter (দরখাস্ত) to the UNO under PMA 2013.

Takes the assembled case data (transcript + RAG legal analysis + entities)
and produces a clean, print-ready complaint letter as PDF bytes.

Design notes (all verified):
- uharfbuzz + set_text_shaping(True)  → correct Bengali যুক্তাক্ষর rendering
- list items joined into ONE multi_cell → avoids fpdf2 shaping+multi_cell bug
- The PDF is a CLEAN letter: NO AI banner / disclaimer / submission guidance
  inside the document (those are shown on screen in Phase 4). Only সূত্র নং
  + তারিখ at top and a discreet page number at the bottom.
- Three reporter modes: self | third_party | anonymous
- Unknown fields → "অজ্ঞাত / ____" placeholders (filled by hand or Phase-4 form)
"""

import secrets
from datetime import date
from pathlib import Path
from typing import Any

from fpdf import FPDF

FONT_DIR = Path(__file__).parent.parent / "fonts"

# Bangla digit conversion for display
_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")
PLACEHOLDER = "অজ্ঞাত / ____________"

# English abuse-type → Bangla (Gemini returns English; show Bangla in the letter)
ABUSE_TYPE_BN = {
    "physical abuse":          "শারীরিক নির্যাতন",
    "physical":                "শারীরিক নির্যাতন",
    "abandonment":             "পরিত্যাগ",
    "neglect":                 "অবহেলা",
    "financial exploitation":  "আর্থিক নির্যাতন",
    "financial":               "আর্থিক নির্যাতন",
    "verbal abuse":            "মৌখিক নির্যাতন",
    "verbal":                  "মৌখিক নির্যাতন",
    "murder":                  "হত্যা",
    "sexual abuse":            "যৌন নির্যাতন",
    "psychological abuse":     "মানসিক নির্যাতন",
    "emotional abuse":         "মানসিক নির্যাতন",
}


def _abuse_type_bn(abuse_type: str) -> str:
    """Translate an English (possibly comma-joined) abuse type to Bangla."""
    if not abuse_type:
        return ""
    parts = [p.strip() for p in abuse_type.split(",") if p.strip()]
    bn = [ABUSE_TYPE_BN.get(p.lower(), p) for p in parts]
    bn_str = " ও ".join(bn)
    # Keep the English in parentheses for the officer's reference
    return f"{bn_str} ({abuse_type})"


def _bn(text: str) -> str:
    """Convert ASCII digits in a string to Bangla digits."""
    return str(text).translate(_BN_DIGITS)


def generate_case_ref() -> str:
    """Generate a unique case reference like EA-2026-0601-A7F3."""
    today = date.today()
    token = secrets.token_hex(2).upper()
    return f"EA-{today.year}-{today.strftime('%m%d')}-{token}"


def _val(entities: dict, key: str, placeholder: str = PLACEHOLDER) -> str:
    """Return entity value or a placeholder if missing."""
    v = entities.get(key)
    if v is None or str(v).strip() == "":
        return placeholder
    return str(v)


class _ComplaintPDF(FPDF):
    def footer(self):
        # Clean letter — only a discreet page number
        self.set_y(-12)
        self.set_font("Bengali", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"পৃষ্ঠা {_bn(self.page_no())}", align="C")
        self.set_text_color(0, 0, 0)


def generate_complaint_pdf(case_data: dict[str, Any],
                           anonymous: bool = False) -> bytes:
    """
    Build the complaint-letter PDF.

    Args:
        case_data : {
            "transcript":                 str,   # the complaint (possibly edited)
            "abuse_type":                 str,
            "applicable_sections":        list[str],
            "recommended_action_bangla":  str,   # used as the prayer (Option A)
            "legal_advice_bangla":        str,   # optional, included as basis note
            "reporter_type":              "self"|"third_party"|"unknown",
            "entities": {
                "victim_name", "victim_age", "victim_gender", "location",
                "abuser_name", "abuser_relation", "incident_date"
            },
            # optional manual/Phase-4 form fields:
            "uno_upazila":  str,
            "uno_district": str,
            "case_ref":     str,   # auto-generated if absent
        }
        anonymous : if True, hide victim's name/identity in the letter.

    Returns:
        PDF file as bytes (ready to download / print).
    """
    ent      = case_data.get("entities", {}) or {}
    reporter = case_data.get("reporter_type", "unknown")
    case_ref = case_data.get("case_ref") or generate_case_ref()

    # UNO address: prefer explicit fields, fall back to entity location
    uno_upazila  = case_data.get("uno_upazila")  or ent.get("location") or "____________"
    uno_district = case_data.get("uno_district") or "____________"

    # ── PDF setup ─────────────────────────────────────────────────────────────
    pdf = _ComplaintPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 15, 20)
    pdf.add_font("Bengali",   fname=str(FONT_DIR / "NotoSansBengali-Regular.ttf"))
    pdf.add_font("Bengali", style="B", fname=str(FONT_DIR / "NotoSansBengali-Bold.ttf"))
    pdf.add_font("Latin",     fname=str(FONT_DIR / "NotoSans-Regular.ttf"))
    pdf.set_fallback_fonts(["Latin"], exact_match=False)
    pdf.set_text_shaping(True)
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    def label_value(label: str, value: str):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Bengali", size=10.5)
        pdf.cell(30, 6, label, new_x="RIGHT", new_y="TOP")
        pdf.cell(4, 6, ":", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(W - 34, 6, value)

    def heading(text: str):
        pdf.set_font("Bengali", style="B", size=10.5)
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Bengali", size=10.5)

    # ── Reference no. + date ──────────────────────────────────────────────────
    pdf.set_font("Bengali", size=10)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, f"সূত্র নং: {case_ref}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, f"তারিখ: {_bn(date.today().strftime('%d/%m/%Y'))} খ্রি.",
             align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── To (বরাবর) ────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, "বরাবর,", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", style="B", size=11)
    pdf.cell(0, 6, "উপজেলা নির্বাহী অফিসার (UNO)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, f"{uno_upazila}, {uno_district}।", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Subject ───────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=11)
    pdf.multi_cell(W, 6,
        "বিষয়: পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ অনুযায়ী একজন প্রবীণ ব্যক্তির প্রতি "
        "নির্যাতনের বিষয়ে অভিযোগ।")
    pdf.ln(2)

    # ── Salutation ────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, "জনাব,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # ── Complainant identity ──────────────────────────────────────────────────
    heading("অভিযোগকারীর পরিচয়:")
    if anonymous:
        pdf.multi_cell(W, 6, "অভিযোগকারী পরিচয় গোপন রাখিতে ইচ্ছুক।")
    else:
        label_value("নাম", _val(ent, "victim_name"))
        age = ent.get("victim_age")
        label_value("বয়স", f"{_bn(age)} বছর" if age else PLACEHOLDER)
        label_value("ঠিকানা", _val(ent, "location"))
    pdf.ln(2)

    # ── Accused identity ──────────────────────────────────────────────────────
    heading("অভিযুক্তের পরিচয়:")
    label_value("নাম", _val(ent, "abuser_name"))
    label_value("সম্পর্ক", _val(ent, "abuser_relation"))
    pdf.ln(2)

    # ── Incident ──────────────────────────────────────────────────────────────
    heading("ঘটনার বিবরণ:")
    intro = ("সবিনয় নিবেদন এই যে, "
             if reporter == "self"
             else "সবিনয় নিবেদন এই যে, নিম্নলিখিত ঘটনাটি আপনার সদয় অবগতির জন্য জানাইতেছি — ")
    pdf.multi_cell(W, 6, intro + case_data.get("transcript", "").strip())
    pdf.ln(1)
    abuse_type = case_data.get("abuse_type", "")
    if abuse_type:
        pdf.set_text_color(70, 70, 70)
        pdf.set_font("Bengali", size=10)
        pdf.multi_cell(W, 5.5, f"নির্যাতনের ধরন: {_abuse_type_bn(abuse_type)}")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Bengali", size=10.5)
    pdf.ln(2)

    # ── Applicable law (single multi_cell — bug workaround) ───────────────────
    sections = case_data.get("applicable_sections", []) or []
    if sections:
        heading("প্রযোজ্য আইন:")
        pdf.multi_cell(W, 6, "\n".join(f"•  {s}" for s in sections))
        pdf.ln(2)

    # ── Prayer (from recommended_action — Option A) ───────────────────────────
    heading("প্রার্থনা:")
    prayer = case_data.get("recommended_action_bangla", "").strip()
    if not prayer:
        prayer = ("মহোদয়ের নিকট আকুল আবেদন এই যে, বিষয়টি তদন্তপূর্বক প্রয়োজনীয় "
                  "আইনানুগ ও প্রশাসনিক ব্যবস্থা গ্রহণ করিতে মর্জি হয়।")
    pdf.multi_cell(W, 6, "অতএব, " + prayer)
    pdf.ln(6)

    # ── Closing + signature ───────────────────────────────────────────────────
    pdf.set_font("Bengali", size=10.5)
    pdf.cell(0, 6, "ধন্যবাদান্তে,", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "বিনীত নিবেদক,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.cell(0, 6, "স্বাক্ষর: ____________________", new_x="LMARGIN", new_y="NEXT")
    if not anonymous:
        pdf.cell(0, 6, f"নাম: {_val(ent, 'victim_name')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"ঠিকানা: {_val(ent, 'location')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, "মোবাইল: ____________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"তারিখ: {_bn(date.today().strftime('%d/%m/%Y'))} খ্রি.",
             new_x="LMARGIN", new_y="NEXT")

    # ── Anonymity note ────────────────────────────────────────────────────────
    if anonymous:
        pdf.ln(4)
        pdf.set_font("Bengali", size=10)
        pdf.multi_cell(W, 5.5,
            "বি:দ্র: প্রয়োজনে আমি আমার পরিচয় গোপন রাখিতে ইচ্ছুক।")

    return bytes(pdf.output())


# ── Convenience: assemble case_data from rag_engine output ─────────────────────
def from_analysis(transcript: str, analysis: dict[str, Any], *,
                  uno_upazila: str | None = None,
                  uno_district: str | None = None,
                  case_ref: str | None = None) -> dict[str, Any]:
    """
    Build a case_data dict from a transcript + rag_engine.analyze() output.
    Used by the API layer (Step 15) to keep the endpoint thin.
    """
    return {
        "transcript":                transcript,
        "abuse_type":                analysis.get("abuse_type", ""),
        "applicable_sections":       analysis.get("applicable_sections", []),
        "severity":                  analysis.get("severity"),
        "civil_or_criminal":         analysis.get("civil_or_criminal", ""),
        "legal_advice_bangla":       analysis.get("legal_advice_bangla", ""),
        "recommended_action_bangla": analysis.get("recommended_action_bangla", ""),
        "reporter_type":             analysis.get("reporter_type", "unknown"),
        "entities":                  analysis.get("entities", {}),
        "uno_upazila":               uno_upazila,
        "uno_district":              uno_district,
        "case_ref":                  case_ref,
    }


# ── CLI quick test ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample = {
        "transcript": "আমার ছেলে করিম আমাকে মারধর করেছে এবং বাড়ি থেকে বের করে দিয়েছে।",
        "abuse_type": "Physical Abuse, Abandonment",
        "applicable_sections": [
            "পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ — ধারা ৩",
            "পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ — ধারা ৪",
            "দণ্ডবিধি ১৮৬০ — ধারা ৩২৩",
        ],
        "recommended_action_bangla":
            "মহোদয়ের নিকট আবেদন, আমার নিয়মিত ভরণ-পোষণ ও নিরাপদ বাসস্থান নিশ্চিত করিতে "
            "প্রয়োজনীয় ব্যবস্থা গ্রহণ করিবেন।",
        "reporter_type": "self",
        "entities": {
            "victim_name": "রাবেয়া বেগম", "victim_age": 75, "location": "ময়মনসিংহ সদর",
            "abuser_name": "করিম", "abuser_relation": "ছেলে",
        },
        "uno_upazila": "ময়মনসিংহ সদর", "uno_district": "ময়মনসিংহ",
    }
    Path("sample_self.pdf").write_bytes(generate_complaint_pdf(sample, anonymous=False))
    Path("sample_anon.pdf").write_bytes(generate_complaint_pdf(sample, anonymous=True))
    print("Generated sample_self.pdf and sample_anon.pdf")
