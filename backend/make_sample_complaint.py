"""
Sample draft complaint letter (দরখাস্ত) — Option A format preview.

Generates a Bangladeshi citizen application to the UNO under PMA 2013,
following the standard দরখাস্ত structure (NO government letterhead — that
belongs only on govt-issued documents). This is a DRAFT/aid, clearly marked.

Saves to: C:\\Users\\ACER\\OneDrive\\Documents\\legal.pdf
"""

from datetime import date
from pathlib import Path
from fpdf import FPDF

FONT_DIR = Path(__file__).parent / "fonts"
OUT_PATH = r"C:\Users\ACER\OneDrive\Documents\legal.pdf"

# ── Sample case data (Rabeya Begum — physical + abandonment) ───────────────────
case = {
    "case_ref":        "EA-2026-0531-A7F3",
    "date":            date.today().strftime("%d/%m/%Y"),
    # complainant (here: the victim herself = self report)
    "reporter_type":   "self",
    "victim_name":     "রাবেয়া বেগম",
    "victim_age":      "৭৫",
    "victim_gender":   "মহিলা",
    "guardian":        "মৃত আব্দুল করিম (স্বামী)",
    "address":         "গ্রাম: চরপাড়া, ডাকঘর: ময়মনসিংহ সদর, উপজেলা: ময়মনসিংহ সদর, জেলা: ময়মনসিংহ",
    "mobile":          "০১৭XXXXXXXX",
    "uno_upazila":     "ময়মনসিংহ সদর",
    "uno_district":    "ময়মনসিংহ",
    # accused
    "abuser_name":     "মোঃ করিম মিয়া",
    "abuser_relation": "ছেলে",
    # incident
    "incident":        ("আমি একজন অসহায় বৃদ্ধা। আমার ছেলে মোঃ করিম মিয়া সম্প্রতি আমাকে "
                        "শারীরিকভাবে মারধর করিয়াছে এবং বসতবাড়ির জমি তাহার নামে লিখিয়া না "
                        "দেওয়ায় আমাকে বাড়ি হইতে বাহির করিয়া দিয়াছে। বর্তমানে আমি অন্যের "
                        "আশ্রয়ে মানবেতর জীবনযাপন করিতেছি এবং আমার ভরণ-পোষণের কোনো ব্যবস্থা নাই।"),
    "abuse_type":      "শারীরিক নির্যাতন ও পরিত্যাগ (Physical Abuse & Abandonment)",
    "sections": [
        "পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ — ধারা ৩ (সন্তানের ভরণ-পোষণের বাধ্যবাধকতা)",
        "পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ — ধারা ৪ (পরিত্যাগ ও চিকিৎসা অবহেলা নিষিদ্ধ)",
        "দণ্ডবিধি ১৮৬০ — ধারা ৩২৩ (স্বেচ্ছায় আঘাত)",
    ],
    "prayer": ("অতএব, মহোদয়ের নিকট আকুল আবেদন এই যে, পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ "
               "অনুযায়ী আমার ছেলের বিরুদ্ধে প্রয়োজনীয় আইনানুগ ব্যবস্থা গ্রহণপূর্বক আমার "
               "নিয়মিত ভরণ-পোষণ ও নিরাপদ বাসস্থান নিশ্চিত করিতে মর্জি হয়।"),
    "submit_to": [
        "এই অভিযোগ উপজেলা নির্বাহী অফিসার (UNO) অফিসে জমা দিন — ভরণ-পোষণ ও পরিত্যাগের জন্য (PMA 2013)।",
        "শারীরিক নির্যাতনের জন্য নিকটস্থ থানায় এজাহার (FIR) দায়ের করুন।",
        "বিনামূল্যে আইনি সহায়তার জন্য NLASO হেল্পলাইন ১৬৪৩০-এ যোগাযোগ করুন।",
    ],
}


class ComplaintPDF(FPDF):
    def footer(self):
        # Clean letter — only a discreet page number (no helplines/AI text)
        self.set_y(-12)
        self.set_font("Bengali", size=8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f"পৃষ্ঠা {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)


def hr(pdf, gap=2):
    pdf.set_draw_color(180, 180, 180)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(gap)


def build():
    pdf = ComplaintPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(20, 15, 20)
    pdf.add_font("Bengali", fname=str(FONT_DIR / "NotoSansBengali-Regular.ttf"))
    pdf.add_font("Bengali", style="B", fname=str(FONT_DIR / "NotoSansBengali-Bold.ttf"))
    pdf.add_font("Latin", fname=str(FONT_DIR / "NotoSans-Regular.ttf"))
    pdf.set_fallback_fonts(["Latin"], exact_match=False)
    pdf.set_text_shaping(True)   # HarfBuzz: proper Bengali conjunct/vowel shaping
    pdf.add_page()
    W = pdf.w - pdf.l_margin - pdf.r_margin

    # ── Reference no. + Date (top) ────────────────────────────────────────────
    pdf.set_font("Bengali", size=10)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 5, f"সূত্র নং: {case['case_ref']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, f"তারিখ: {case['date']}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── To (বরাবর) ────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, "বরাবর,", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", style="B", size=11)
    pdf.cell(0, 6, "উপজেলা নির্বাহী অফিসার (UNO)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, f"{case['uno_upazila']}, {case['uno_district']}।", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Subject (বিষয়) ───────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=11)
    pdf.multi_cell(W, 6,
        "বিষয়: পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩ অনুযায়ী সন্তানের বিরুদ্ধে ভরণ-পোষণ ও "
        "নিরাপত্তা সংক্রান্ত অভিযোগ।")
    pdf.ln(2)

    # ── Salutation ────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 6, "জনাব,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    # ── Complainant info ──────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=10.5)
    pdf.cell(0, 6, "অভিযোগকারীর পরিচয়:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10.5)
    for label, val in [
        ("নাম", case["victim_name"]),
        ("বয়স", f"{case['victim_age']} বছর"),
        ("পিতা/স্বামী", case["guardian"]),
        ("ঠিকানা", case["address"]),
        ("মোবাইল", case["mobile"]),
    ]:
        pdf.set_x(pdf.l_margin)
        pdf.cell(28, 6, f"{label}", new_x="RIGHT", new_y="TOP")
        pdf.cell(4, 6, ":", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(W - 32, 6, val)
    pdf.ln(2)

    # ── Accused info ──────────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=10.5)
    pdf.cell(0, 6, "অভিযুক্তের পরিচয়:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10.5)
    for label, val in [
        ("নাম", case["abuser_name"]),
        ("সম্পর্ক", case["abuser_relation"]),
    ]:
        pdf.set_x(pdf.l_margin)
        pdf.cell(28, 6, f"{label}", new_x="RIGHT", new_y="TOP")
        pdf.cell(4, 6, ":", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(W - 32, 6, val)
    pdf.ln(2)

    # ── Incident ──────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=10.5)
    pdf.cell(0, 6, "ঘটনার বিবরণ:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10.5)
    pdf.multi_cell(W, 6, "সবিনয় নিবেদন এই যে, " + case["incident"])
    pdf.ln(1)
    pdf.set_font("Bengali", size=10)
    pdf.set_text_color(70, 70, 70)
    pdf.multi_cell(W, 5.5, f"নির্যাতনের ধরন: {case['abuse_type']}")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # ── Applicable law ────────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=10.5)
    pdf.cell(0, 6, "প্রযোজ্য আইন:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10.5)
    # NOTE: join into ONE multi_cell — repeated multi_cell + text_shaping drops glyphs
    pdf.multi_cell(W, 6, "\n".join(f"•  {s}" for s in case["sections"]))
    pdf.ln(2)

    # ── Prayer ────────────────────────────────────────────────────────────────
    pdf.set_font("Bengali", style="B", size=10.5)
    pdf.cell(0, 6, "প্রার্থনা:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10.5)
    pdf.multi_cell(W, 6, case["prayer"])
    pdf.ln(6)

    # ── Signature block ───────────────────────────────────────────────────────
    pdf.set_font("Bengali", size=10.5)
    pdf.cell(0, 6, "বিনীত নিবেদক,", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.cell(70, 6, "স্বাক্ষর: ____________________", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(70, 6, f"নাম: {case['victim_name']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(70, 6, "তারিখ: ____________________", new_x="LMARGIN", new_y="NEXT")
    # NOTE: submission guidance + disclaimer are shown ON SCREEN after generation,
    # NOT in the PDF — the PDF must be a clean letter ready to print & submit.

    pdf.output(OUT_PATH)
    print(f"Saved: {OUT_PATH}")
    print(f"Size : {Path(OUT_PATH).stat().st_size/1024:.1f} KB")


if __name__ == "__main__":
    build()
