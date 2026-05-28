"""
Generate PDF from implementation-plan.md with Bangla font support.
Output: implementation-plan.pdf at project root.
"""
import re
import sys
from pathlib import Path
from fpdf import FPDF

FONT_PATH        = r"C:\Users\ACER\AppData\Local\Temp\NotoSansBengali-Regular.ttf"
FONT_LATIN_PATH  = r"C:\Users\ACER\AppData\Local\Temp\NotoSans-Regular.ttf"
MD_FILE   = r"d:\499 CAPSTONE\elder-abuse\docs\implementation-plan.md"
OUT_FILE  = r"d:\499 CAPSTONE\elder-abuse\implementation-plan.pdf"

# ─── PDF class ────────────────────────────────────────────────────────────────
class PlanPDF(FPDF):
    def header(self):
        self.set_font("Bengali", size=9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "Elder Abuse AI — Complete Implementation Plan  |  CSE 499A NSU Spring 2026", align="C")
        self.ln(2)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-12)
        self.set_font("Bengali", size=8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"Page {self.page_no()}", align="C")
        self.set_text_color(0, 0, 0)


def strip_inline_code(text):
    """Remove backtick inline code markers but keep the text."""
    return re.sub(r"`([^`]+)`", r"\1", text)


def clean_line(text):
    """Strip markdown bold/italic markers."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*",   r"\1", text)
    text = re.sub(r"__(.+?)__",   r"\1", text)
    text = re.sub(r"_(.+?)_",     r"\1", text)
    text = strip_inline_code(text)
    # Remove link syntax [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.strip()


def render(pdf: PlanPDF, lines: list[str]):
    in_code   = False
    code_buf: list[str] = []

    def flush_code():
        if not code_buf:
            return
        pdf.set_font("Bengali", size=8)
        pdf.set_fill_color(245, 245, 250)
        # measure block height to avoid page split mid-block (best effort)
        block_h = len(code_buf) * 4.5 + 4
        if pdf.get_y() + block_h > pdf.h - 20:
            pdf.add_page()
        pdf.set_x(12)
        pdf.cell(186, 3, "", border=0)
        pdf.ln(1)
        for cline in code_buf:
            safe = cline.replace("\t", "    ")
            pdf.set_x(14)
            pdf.set_fill_color(245, 245, 250)
            pdf.cell(184, 4.5, safe, border=0, fill=True)
            pdf.ln(0)
        pdf.ln(3)
        code_buf.clear()

    for raw in lines:
        line = raw.rstrip()

        # ── code fence toggle ──────────────────────────────────────────────
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        # ── skip horizontal rules ─────────────────────────────────────────
        if re.match(r"^[-*_]{3,}$", line.strip()):
            pdf.set_draw_color(180, 180, 180)
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(4)
            continue

        # ── headings ──────────────────────────────────────────────────────
        if line.startswith("#### "):
            pdf.set_x(12)
            pdf.set_font("Bengali", size=10.5)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(186, 6, clean_line(line[5:]))
            pdf.ln(1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Bengali", size=10)
            continue

        if line.startswith("### "):
            text = clean_line(line[4:])
            pdf.set_x(12)
            pdf.set_font("Bengali", size=12)
            pdf.set_text_color(30, 90, 160)
            pdf.multi_cell(186, 7, text)
            pdf.ln(1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Bengali", size=10)
            continue

        if line.startswith("## "):
            text = clean_line(line[3:])
            pdf.set_x(12)
            pdf.set_font("Bengali", size=14)
            pdf.set_text_color(20, 60, 130)
            if pdf.get_y() > pdf.h - 40:
                pdf.add_page()
            pdf.ln(3)
            pdf.multi_cell(186, 8, text)
            pdf.set_draw_color(20, 60, 130)
            pdf.line(12, pdf.get_y(), 198, pdf.get_y())
            pdf.ln(4)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Bengali", size=10)
            continue

        if line.startswith("# "):
            text = clean_line(line[2:])
            pdf.set_x(12)
            pdf.set_font("Bengali", size=18)
            pdf.set_text_color(10, 40, 100)
            pdf.ln(4)
            pdf.multi_cell(186, 10, text)
            pdf.ln(4)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Bengali", size=10)
            continue

        # ── blockquote ────────────────────────────────────────────────────
        if line.startswith("> "):
            text = clean_line(line[2:])
            pdf.set_font("Bengali", size=9.5)
            pdf.set_text_color(80, 80, 80)
            pdf.set_fill_color(240, 244, 255)
            pdf.multi_cell(186, 5.5, text, fill=True)
            pdf.ln(1)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Bengali", size=10)
            continue

        # ── bullet list ───────────────────────────────────────────────────
        m = re.match(r"^(\s*)([-*+])\s+(.*)", line)
        if m:
            indent = len(m.group(1))
            text   = clean_line(m.group(3))
            x_off  = 14 + indent * 3
            w      = max(186 - x_off, 60)
            pdf.set_font("Bengali", size=10)
            pdf.set_x(x_off)
            pdf.cell(5, 5.5, "•")
            pdf.set_x(x_off + 5)
            pdf.multi_cell(w - 5, 5.5, text)
            continue

        # ── numbered list ─────────────────────────────────────────────────
        m2 = re.match(r"^(\s*)\d+[.)]\s+(.*)", line)
        if m2:
            indent = len(m2.group(1))
            text   = clean_line(m2.group(2))
            x_off  = 14 + indent * 3
            w      = max(186 - x_off, 60)
            num_match = re.match(r"^(\s*)(\d+)[.)]\s+(.*)", line)
            num    = num_match.group(2) if num_match else "•"
            pdf.set_x(x_off)
            pdf.cell(7, 5.5, f"{num}.")
            pdf.set_x(x_off + 7)
            pdf.multi_cell(w - 7, 5.5, text)
            continue

        # ── table row (pipe-separated) ────────────────────────────────────
        if line.startswith("|") and "|" in line[1:]:
            if re.match(r"^\|[-| :]+\|$", line.strip()):
                continue  # skip separator row
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells:
                continue
            col_w = min(186 // max(len(cells), 1), 60)
            pdf.set_font("Bengali", size=8.5)
            pdf.set_x(12)
            for ci, cell in enumerate(cells):
                text = clean_line(cell)
                pdf.cell(col_w, 5.5, text[:45], border=1)
            pdf.ln()
            pdf.set_font("Bengali", size=10)
            continue

        # ── blank line ────────────────────────────────────────────────────
        if not line.strip():
            pdf.ln(3)
            continue

        # ── regular paragraph ─────────────────────────────────────────────
        text = clean_line(line)
        if text:
            pdf.set_x(12)
            pdf.set_font("Bengali", size=10)
            pdf.multi_cell(186, 5.5, text)

    flush_code()  # trailing code block if any


def main():
    md_path = Path(MD_FILE)
    if not md_path.exists():
        print(f"ERROR: {MD_FILE} not found")
        sys.exit(1)

    lines = md_path.read_text(encoding="utf-8").splitlines()
    print(f"Read {len(lines)} lines from {md_path.name}")

    pdf = PlanPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(12, 18, 12)

    # Register Bengali font with Latin fallback
    font_path = Path(FONT_PATH)
    if not font_path.exists():
        print(f"ERROR: Font not found at {FONT_PATH}")
        sys.exit(1)
    pdf.add_font("Bengali", fname=str(font_path))

    latin_path = Path(FONT_LATIN_PATH)
    if latin_path.exists():
        pdf.add_font("Latin", fname=str(latin_path))
        pdf.set_fallback_fonts(["Latin"], exact_match=False)

    pdf.add_page()
    pdf.set_font("Bengali", size=10)

    render(pdf, lines)

    out = Path(OUT_FILE)
    pdf.output(str(out))
    print(f"PDF saved: {out}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
