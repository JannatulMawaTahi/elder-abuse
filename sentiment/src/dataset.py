# -*- coding: utf-8 -*-
"""
Phase 2 — Dataset construction for the SENTIMENT (polarity) task.

Emotion is set aside for now. The `emotion` column is preserved in every split
file, so emotion can be activated later on these SAME splits (keeping the locked
test set intact) without re-splitting. Active target = polarity.

Pipeline:
  1. Load llm_labels.csv (labelled comments).
  2. Final dedup on normalised comment text  -> prevents train/test leakage.
  3. Stratified 70/15/15 split by polarity (SEED=42).
  4. Write data/splits/{train,val,test}.csv  (all columns kept).
  5. Lock the test set -> data/splits/test_lock.json (ids + sha256 + counts).
  6. Class-distribution report -> results/phase2_split.json + .md
"""
from __future__ import annotations
import sys, io, json, hashlib
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "annotated" / "llm_labels.csv"
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"
SPLITS.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET = "polarity"
POL_ORDER = ["Negative", "Neutral", "Positive"]


def norm_text(s: str) -> str:
    return " ".join(str(s).split()).strip().lower()


def dist(part: pd.DataFrame) -> dict:
    vc = part[TARGET].value_counts().reindex(POL_ORDER).fillna(0).astype(int)
    return {k: int(v) for k, v in vc.items()}


def main() -> None:
    df = pd.read_csv(LABELS, dtype=str, keep_default_na=False)
    n0 = len(df)

    # 1. final dedup on normalised comment text (keep first occurrence)
    df["_norm"] = df["Comment"].map(norm_text)
    dup_mask = df["_norm"].duplicated(keep="first")
    n_dup = int(dup_mask.sum())
    df = df[~dup_mask].drop(columns="_norm").reset_index(drop=True)
    n1 = len(df)

    # 2. stratified 70/15/15 split by polarity
    train, temp = train_test_split(
        df, test_size=0.30, stratify=df[TARGET], random_state=SEED)
    val, test = train_test_split(
        temp, test_size=0.50, stratify=temp[TARGET], random_state=SEED)

    for name, part in [("train", train), ("val", val), ("test", test)]:
        (part.sort_values("comment_id")
             .to_csv(SPLITS / f"{name}.csv", index=False, encoding="utf-8"))

    # 3. lock the test set (ids + hash so any later tampering is detectable)
    test_ids = sorted(test["comment_id"].tolist())
    h = hashlib.sha256("\n".join(test_ids).encode()).hexdigest()
    lock = {
        "n_test": len(test_ids),
        "sha256_ids": h,
        "seed": SEED,
        "target": TARGET,
        "note": "Locked test set. DO NOT inspect or tune on it until final evaluation.",
        "comment_ids": test_ids,
    }
    (SPLITS / "test_lock.json").write_text(json.dumps(lock, indent=2), encoding="utf-8")

    # 4. distribution report (json)
    report = {
        "raw_labelled": n0,
        "removed_duplicate_text": n_dup,
        "after_dedup": n1,
        "seed": SEED,
        "target": TARGET,
        "split_ratio": "70/15/15",
        "split_sizes": {"train": len(train), "val": len(val), "test": len(test)},
        "polarity_distribution": {
            "overall": dist(df), "train": dist(train), "val": dist(val), "test": dist(test),
        },
        "emotion_status": "preserved as a column (deferred; not the active target)",
    }
    (RES / "phase2_split.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # 5. markdown report with a clean distribution table
    def row(label, part):
        d = dist(part)
        tot = sum(d.values())
        cells = " | ".join(
            f"{d[k]} ({100*d[k]/tot:.1f}%)" if tot else "0" for k in POL_ORDER)
        return f"| {label} | {tot} | {cells} |"

    md = [
        "# Phase 2 — Dataset Split Report (sentiment / polarity)",
        "",
        f"- Labelled comments loaded: **{n0}**",
        f"- Removed as duplicate text (final dedup): **{n_dup}**",
        f"- After dedup: **{n1}**",
        f"- Split: **70/15/15**, stratified by polarity, SEED={SEED}",
        f"- Test set **locked** (`data/splits/test_lock.json`, sha256 `{h[:16]}…`).",
        "- `emotion` column preserved in every split (deferred target).",
        "",
        "## Polarity distribution per split",
        "",
        "| Split | N | Negative | Neutral | Positive |",
        "|---|---|---|---|---|",
        row("Overall", df),
        row("Train", train),
        row("Val", val),
        row("Test", test),
        "",
        "Stratification keeps the polarity ratios near-identical across splits, so the "
        "locked test set is representative and there is no class-balance leakage.",
        "",
        "## Files",
        "- `data/splits/train.csv` · `val.csv` · `test.csv` (all original columns kept)",
        "- `data/splits/test_lock.json` (id list + hash)",
        "- `results/phase2_split.json` (machine-readable numbers)",
    ]
    (RES / "phase2_split_report.md").write_text("\n".join(md), encoding="utf-8")

    print("Phase 2 done.")
    print(f"  raw {n0} -> dedup removed {n_dup} -> {n1}")
    print(f"  train {len(train)} | val {len(val)} | test {len(test)}")
    print("  polarity per split:")
    for nm, pt in [("overall", df), ("train", train), ("val", val), ("test", test)]:
        print(f"    {nm:8s} {dist(pt)}")


if __name__ == "__main__":
    main()
