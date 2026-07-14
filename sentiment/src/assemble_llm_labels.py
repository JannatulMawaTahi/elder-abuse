# -*- coding: utf-8 -*-
"""
Assemble all LLM label batch files into annotated/llm_labels.csv.

Batch files live in sentiment/data/annotated/llm_codes/*.csv with rows:
    comment_id,pol_code,emo_code
codes:
    polarity  Neg=Negative  Neu=Neutral  Pos=Positive
    emotion   ANG=Anger/Condemnation  GRF=Grief/Sympathy  PRY=Prayer/Religious
              BLM=Victim-blaming       OTH=Neutral-Other

Validates: every cleaned comment_id is covered exactly once, all codes valid.
Output: annotated/llm_labels.csv  (comment_id, Comment, polarity, emotion, + context cols)
"""
import sys, io
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
CLEANED = ROOT / "data" / "interim" / "cleaned.csv"
CODES = ROOT / "data" / "annotated" / "llm_codes"
OUT = ROOT / "data" / "annotated" / "llm_labels.csv"

POL = {"Neg": "Negative", "Neu": "Neutral", "Pos": "Positive"}
EMO = {"ANG": "Anger/Condemnation", "GRF": "Grief/Sympathy", "PRY": "Prayer/Religious",
       "BLM": "Victim-blaming", "OTH": "Neutral-Other"}


def main() -> None:
    clean = pd.read_csv(CLEANED, dtype=str, keep_default_na=False)
    files = sorted(CODES.glob("*.csv"))
    if not files:
        sys.exit(f"No batch files in {CODES}")

    parts = []
    for f in files:
        d = pd.read_csv(f, dtype=str, keep_default_na=False,
                        names=["comment_id", "pol", "emo"], header=None)
        d = d[d["comment_id"].str.startswith("C")]   # skip any stray header/comment lines
        parts.append(d)
    codes = pd.concat(parts, ignore_index=True)

    # validation
    bad_pol = sorted(set(codes["pol"]) - set(POL))
    bad_emo = sorted(set(codes["emo"]) - set(EMO))
    if bad_pol or bad_emo:
        sys.exit(f"Invalid codes -> pol:{bad_pol} emo:{bad_emo}")
    dups = codes["comment_id"][codes["comment_id"].duplicated()].tolist()
    if dups:
        sys.exit(f"Duplicate comment_ids in batches: {dups[:10]} ...({len(dups)})")

    missing = sorted(set(clean["comment_id"]) - set(codes["comment_id"]))
    extra = sorted(set(codes["comment_id"]) - set(clean["comment_id"]))
    print(f"labelled: {len(codes)} / {len(clean)}  | missing: {len(missing)} | extra: {len(extra)}")
    if extra:
        print("  extra ids (not in cleaned):", extra[:10])
    if missing:
        print("  first missing ids:", missing[:10])

    codes["polarity"] = codes["pol"].map(POL)
    codes["emotion"] = codes["emo"].map(EMO)
    out = clean.merge(codes[["comment_id", "polarity", "emotion"]], on="comment_id", how="left")
    out.to_csv(OUT, index=False, encoding="utf-8")
    print(f"\nWrote {OUT} ({len(out)} rows, {out['polarity'].notna().sum()} labelled)")
    if not missing:
        print("\n=== polarity ==="); print(out["polarity"].value_counts().to_string())
        print("\n=== emotion ==="); print(out["emotion"].value_counts().to_string())


if __name__ == "__main__":
    main()
