# -*- coding: utf-8 -*-
"""
Phase 1 (Option 3) — Fleiss' Kappa for FOUR annotators + assemble the gold labels.

RUN AFTER all four annotator_{A,B,C,D}.xlsx are filled.

  - Fleiss' Kappa (+ % agreement) on the 450 shared overlap, for polarity & emotion.
  - Assembles the final HUMAN gold labels:
        overlap (4 labels)  -> majority vote (ties broken by the AI silver label, flagged)
        unique  (1 label)   -> that annotator's label
    -> data/annotated/human_labels.csv  (full human-annotated dataset)

    python sentiment/src/kappa4.py

Outputs: results/kappa.json (+ printed report), data/annotated/human_labels.csv
Target: Fleiss' Kappa >= 0.60 (substantial). If lower, refine the guideline & re-label.
"""
from __future__ import annotations
import sys, io, json
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
ANN = ROOT / "data" / "annotated"
RES = ROOT / "results"
CODES = ["A", "B", "C", "D"]
POLARITY = ["Negative", "Neutral", "Positive"]
EMOTION = ["Anger/Condemnation", "Grief/Sympathy", "Prayer/Religious",
           "Victim-blaming", "Neutral-Other"]


def load(code):
    df = pd.read_excel(ANN / f"annotator_{code}.xlsx", sheet_name="Annotate", dtype=str)
    df = df.fillna("")
    return df[["comment_id", "polarity", "emotion"]]


def fleiss_kappa(rows, categories):
    """rows: list of n-length label lists (fixed n raters). Returns (kappa, per_cat_p)."""
    cidx = {c: i for i, c in enumerate(categories)}
    N = len(rows); n = len(rows[0]); k = len(categories)
    M = np.zeros((N, k))
    for i, item in enumerate(rows):
        for lab in item:
            M[i, cidx[lab]] += 1
    p_j = M.sum(0) / (N * n)
    P_i = ((M ** 2).sum(1) - n) / (n * (n - 1))
    P_bar = P_i.mean()
    P_e = (p_j ** 2).sum()
    kappa = (P_bar - P_e) / (1 - P_e) if (1 - P_e) else float("nan")
    return float(kappa), P_bar, P_e


def analyse(overlap_labels, field, categories, ai_map):
    """overlap_labels: {cid: [labelA,labelB,labelC,labelD]}. Only 4-valid items counted."""
    rows, ids = [], []
    for cid, labs in overlap_labels.items():
        valid = [l for l in labs if l in categories]
        if len(valid) == 4:
            rows.append(valid); ids.append(cid)
    if not rows:
        return None
    kappa, P_bar, P_e = fleiss_kappa(rows, categories)
    # pairwise % agreement (avg over the 6 pairs)
    agr = []
    for r in rows:
        c = Counter(r); top = c.most_common(1)[0][1]
        agr.append((top * (top - 1)) / (4 * 3))   # prob two random raters agree
    verdict = ("OK (>=0.60 substantial)" if kappa >= 0.60 else
               "MODERATE" if kappa >= 0.40 else "LOW — refine guideline & re-label")
    return {"field": field, "n_items_4rater": len(rows), "fleiss_kappa": round(kappa, 4),
            "avg_pairwise_agreement": round(float(np.mean(agr)), 4),
            "verdict": verdict, "P_bar": round(P_bar, 4), "P_e": round(P_e, 4)}


def majority(labs, ai, categories):
    valid = [l for l in labs if l in categories]
    if not valid:
        return ai, "empty→ai"
    c = Counter(valid).most_common()
    if len(c) == 1 or c[0][1] > c[1][1]:
        return c[0][0], "majority"
    return (ai if ai in categories else c[0][0]), "tie→ai"


def main():
    missing = [c for c in CODES if not (ANN / f"annotator_{c}.xlsx").exists()]
    if missing:
        sys.exit(f"Missing annotator files: {missing}")
    sheets = {c: load(c).set_index("comment_id") for c in CODES}

    # overlap = comment_ids present in ALL four sheets
    overlap = set(sheets["A"].index)
    for c in CODES[1:]:
        overlap &= set(sheets[c].index)
    overlap = sorted(overlap)

    ai = pd.read_csv(ANN / "overlap_ids.csv", dtype=str, keep_default_na=False).set_index("comment_id")

    labelled = 0
    pol_over, emo_over = {}, {}
    for cid in overlap:
        pl = [sheets[c].loc[cid, "polarity"] if cid in sheets[c].index else "" for c in CODES]
        el = [sheets[c].loc[cid, "emotion"] if cid in sheets[c].index else "" for c in CODES]
        pol_over[cid], emo_over[cid] = pl, el
        if all(p in POLARITY for p in pl):
            labelled += 1
    if labelled == 0:
        sys.exit("No fully-labelled overlap rows yet — all four must label the shared 450 first.")

    pol = analyse(pol_over, "polarity", POLARITY, {})
    emo = analyse(emo_over, "emotion", EMOTION, {})

    # ---- assemble gold labels for the FULL set ----
    aip = ai["ai_polarity"].to_dict(); aie = ai["ai_emotion"].to_dict()
    gold = {}
    for cid in overlap:
        gp, _ = majority(pol_over[cid], aip.get(cid, ""), POLARITY)
        ge, _ = majority(emo_over[cid], aie.get(cid, ""), EMOTION)
        gold[cid] = (gp, ge, "overlap-majority")
    for c in CODES:
        for cid, r in sheets[c].iterrows():
            if cid in overlap:
                continue
            gold[cid] = (r["polarity"], r["emotion"], f"unique-{c}")
    gdf = pd.DataFrame([(k, v[0], v[1], v[2]) for k, v in gold.items()],
                       columns=["comment_id", "polarity", "emotion", "source"])
    gdf.to_csv(ANN / "human_labels.csv", index=False, encoding="utf-8")

    out = {"n_overlap": len(overlap), "n_overlap_fully_labelled": labelled,
           "polarity": pol, "emotion": emo, "n_gold_labels": len(gdf)}
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "kappa.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Fleiss' Kappa (4 annotators, 450 overlap) ===")
    for r in (pol, emo):
        if r:
            print(f"[{r['field']}] n={r['n_items_4rater']}  Fleiss κ={r['fleiss_kappa']}  "
                  f"agreement={r['avg_pairwise_agreement']:.1%}  -> {r['verdict']}")
    print(f"\nGold labels assembled: {len(gdf)} → data/annotated/human_labels.csv")
    print(f"Wrote {RES/'kappa.json'}")


if __name__ == "__main__":
    main()
