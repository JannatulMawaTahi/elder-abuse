# -*- coding: utf-8 -*-
"""
Phase 0 — Data cleaning for the elder-abuse sentiment dataset.

Reads the raw scraped CSV, removes junk rows (exact duplicates, emoji/punct-only,
ultra-short, and clear spam), tags language, and writes:
    - sentiment/data/interim/cleaned.csv   (rows kept for annotation/modeling)
    - sentiment/data/interim/removed.csv   (every dropped row + remove_reason, auditable)
    - sentiment/results/phase0_cleaning_report.md

Design choices (see docs/sentiment-flow.md):
    * raw/ is never modified.
    * Emoji & punctuation are KEPT in kept rows (they carry emotion); we only drop rows
      that are *nothing but* emoji/punct.
    * Every removal is logged with a reason so the step is reversible and reviewable.
"""
from __future__ import annotations
import re
import sys
import io
from pathlib import Path
import pandas as pd

# Force UTF-8 stdout so Bangla prints cleanly on Windows consoles.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]            # .../sentiment
RAW = ROOT / "data" / "raw" / "all_comments_merged.csv"
INTERIM = ROOT / "data" / "interim"
RESULTS = ROOT / "results"

# ── language tagging ──────────────────────────────────────────────────────────
BENGALI = r"ঀ-৿"
ARABIC = r"؀-ۿ"
LETTER = re.compile(rf"[A-Za-z{BENGALI}{ARABIC}]")


def tag_language(text: str) -> str:
    s = str(text)
    has_bn = bool(re.search(rf"[{BENGALI}]", s))
    has_ar = bool(re.search(rf"[{ARABIC}]", s))
    has_lat = bool(re.search(r"[A-Za-z]", s))
    if has_ar and not has_bn:
        return "arabic"
    if has_bn and has_lat:
        return "bn+en"
    if has_bn:
        return "bengali"
    if has_lat:
        return "latin"          # English or romanized Banglish
    return "emoji/other"


# ── spam detection (conservative; long heartfelt comments are NOT spam) ───────
SPAM_PATTERNS = [
    r"fair use",                       # repeated copyright-notice spam
    r"t\.me/",                         # telegram promo links
    r"\bPremium\b.*\b(?:account|subscription|offer)\b",
    r"[\U0001D400-\U0001D7FF]{4,}",    # mathematical-bold promo text (𝗚𝗼𝗼𝗴𝗹𝗲 …)
    r"https?://\S+\.(?:php|com/photo)",  # pasted FB photo/link-only comments
]
SPAM_RE = re.compile("|".join(SPAM_PATTERNS), flags=re.IGNORECASE)


def is_textless(text: str) -> bool:
    """True if the comment has no actual word characters (emoji/punct/symbols only)."""
    return not bool(LETTER.search(str(text)))


def main() -> None:
    df = pd.read_csv(RAW, dtype=str, keep_default_na=False)
    n_raw = len(df)

    df["Comment"] = df["Comment"].fillna("")
    stripped = df["Comment"].str.strip()
    char_len = stripped.str.len()

    # ── build removal reason (priority: spam > textless > too_short > duplicate) ──
    reason = pd.Series([""] * n_raw, index=df.index)

    is_spam = stripped.str.contains(SPAM_RE, na=False)
    reason[(reason == "") & is_spam] = "spam"

    textless = stripped.apply(is_textless)
    reason[(reason == "") & textless] = "textless(emoji/punct only)"

    too_short = char_len <= 2
    reason[(reason == "") & too_short] = "too_short(<=2 chars)"

    # exact duplicate of an EARLIER kept comment (keep first occurrence)
    dup = stripped.duplicated(keep="first")
    reason[(reason == "") & dup] = "exact_duplicate"

    removed_mask = reason != ""
    kept = df.loc[~removed_mask].copy()
    removed = df.loc[removed_mask].copy()
    removed.insert(0, "remove_reason", reason[removed_mask].values)

    # ── enrich kept rows ──
    kept = kept.reset_index(drop=True)
    kept.insert(0, "comment_id", [f"C{i:05d}" for i in range(1, len(kept) + 1)])
    kept["char_len"] = kept["Comment"].str.strip().str.len()
    kept["lang"] = kept["Comment"].apply(tag_language)

    INTERIM.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(parents=True, exist_ok=True)
    kept.to_csv(INTERIM / "cleaned.csv", index=False, encoding="utf-8")
    removed.to_csv(INTERIM / "removed.csv", index=False, encoding="utf-8")

    # ── report ──
    reason_counts = reason[removed_mask].value_counts()
    lang_counts = kept["lang"].value_counts()
    abuse_counts = kept["abuse_type"].value_counts()
    plat_counts = kept["platform"].value_counts()

    lines = []
    lines.append("# Phase 0 — Cleaning Report\n")
    lines.append(f"- Raw rows: **{n_raw}**")
    lines.append(f"- Removed: **{int(removed_mask.sum())}**")
    lines.append(f"- Kept (cleaned.csv): **{len(kept)}**\n")
    lines.append("## Removed by reason")
    for r, c in reason_counts.items():
        lines.append(f"- {r}: {c}")
    lines.append("\n## Kept — language distribution")
    for k, c in lang_counts.items():
        lines.append(f"- {k}: {c}")
    lines.append("\n## Kept — platform")
    for k, c in plat_counts.items():
        lines.append(f"- {k}: {c}")
    lines.append("\n## Kept — abuse_type (video-level context label)")
    for k, c in abuse_counts.items():
        lines.append(f"- {k}: {c}")
    lines.append(
        "\n## Kept — comment length (chars)"
        f"\n- mean {kept['char_len'].mean():.0f} · median {kept['char_len'].median():.0f}"
        f" · p90 {kept['char_len'].quantile(.9):.0f} · max {kept['char_len'].max()}"
    )
    report = "\n".join(lines) + "\n"
    (RESULTS / "phase0_cleaning_report.md").write_text(report, encoding="utf-8")

    print(report)
    print(f"Wrote: {INTERIM/'cleaned.csv'}  ({len(kept)} rows)")
    print(f"Wrote: {INTERIM/'removed.csv'}  ({len(removed)} rows)")
    print(f"Wrote: {RESULTS/'phase0_cleaning_report.md'}")


if __name__ == "__main__":
    main()
