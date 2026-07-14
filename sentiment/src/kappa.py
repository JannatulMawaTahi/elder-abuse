# -*- coding: utf-8 -*-
"""
Phase 1 (post-annotation) — Inter-annotator agreement.

RUN THIS AFTER both annotators have filled annotator_A.xlsx / annotator_B.xlsx.

It matches the two sheets on `comment_id`, takes the rows BOTH labelled (the overlap set),
and reports Cohen's Kappa + percent agreement for polarity and emotion.

Outputs:
    - sentiment/results/kappa.json
    - prints a short report

Target: Cohen's Kappa >= 0.70 (substantial). If lower, refine the guideline and re-label.
"""
from __future__ import annotations
import sys
import io
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotated"
RESULTS = ROOT / "results"

POLARITY = ["Negative", "Neutral", "Positive"]
EMOTION = ["Anger/Condemnation", "Grief/Sympathy", "Prayer/Religious",
           "Victim-blaming", "Neutral-Other"]


def load(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Annotate", dtype=str)
    df = df.fillna("")
    for c in ("polarity", "emotion"):
        df[c] = df[c].str.strip()
    return df[["comment_id", "polarity", "emotion"]]


def agreement(a: pd.Series, b: pd.Series, labels: list[str], field: str) -> dict:
    valid = a.isin(labels) & b.isin(labels)
    n_drop = int((~valid).sum())
    a, b = a[valid], b[valid]
    k = float(cohen_kappa_score(a, b, labels=labels))
    pct = float((a.values == b.values).mean())
    cm = confusion_matrix(a, b, labels=labels).tolist()
    return {
        "field": field, "n_compared": int(valid.sum()), "n_dropped_unlabeled_or_invalid": n_drop,
        "cohen_kappa": round(k, 4), "percent_agreement": round(pct, 4),
        "labels": labels, "confusion_matrix_AxB": cm,
        "verdict": "OK (>=0.70)" if k >= 0.70 else "LOW — refine guideline & re-label",
    }


def main() -> None:
    a_path, b_path = ANN / "annotator_A.xlsx", ANN / "annotator_B.xlsx"
    if not a_path.exists() or not b_path.exists():
        sys.exit("Annotator files not found — fill them first.")

    A, B = load(a_path), load(b_path)
    merged = A.merge(B, on="comment_id", suffixes=("_A", "_B"))
    # only the overlap rows where BOTH gave a label
    both = merged[(merged["polarity_A"] != "") & (merged["polarity_B"] != "")]

    if len(both) == 0:
        sys.exit("No overlapping labelled rows yet — annotate the shared set first.")

    out = {
        "n_overlap_matched": int(len(merged)),
        "n_both_labelled": int(len(both)),
        "polarity": agreement(both["polarity_A"], both["polarity_B"], POLARITY, "polarity"),
        "emotion": agreement(both["emotion_A"], both["emotion_B"], EMOTION, "emotion"),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "kappa.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Inter-annotator agreement (overlap set) ===")
    print(f"matched overlap rows: {out['n_overlap_matched']} | both labelled: {out['n_both_labelled']}\n")
    for f in ("polarity", "emotion"):
        r = out[f]
        print(f"[{f}] compared={r['n_compared']}  kappa={r['cohen_kappa']}  "
              f"agreement={r['percent_agreement']:.1%}  -> {r['verdict']}")
    print(f"\nWrote {RESULTS/'kappa.json'}")


if __name__ == "__main__":
    main()
