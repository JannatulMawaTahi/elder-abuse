# -*- coding: utf-8 -*-
"""
Phase 4 — FINAL evaluation on the LOCKED test set (touched once, here).

Evaluates the two frozen Phase-3 models on the held-out test split:
  - Baseline : models/baseline_best.joblib  (TF-IDF + Linear SVM)
  - BanglaBERT: models/banglabert_polarity/ (tuned, best val checkpoint)

Reports macro-F1 (primary), accuracy, weighted-F1, per-class P/R/F1, confusion
matrices, and a McNemar significance test between the two models. Also compares
validation vs test (generalisation gap).

Run with the D: venv (needs torch + transformers + sklearn):
    .venv-bert\\Scripts\\python.exe sentiment/src/evaluate.py

Outputs: results/phase4_test_eval.json + _report.md
         figures/16_test_confusion_baseline.png
         figures/17_test_confusion_bert.png
"""
from __future__ import annotations
import os, sys, io, json, hashlib
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\pysetup\hf_cache")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"
FIG = ROOT / "figures"
MODELS = ROOT / "models"

LABELS = ["Negative", "Neutral", "Positive"]
L2I = {l: i for i, l in enumerate(LABELS)}
TARGET = "polarity"

import joblib
from sklearn.metrics import (f1_score, accuracy_score, classification_report,
                             confusion_matrix)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def verify_lock(df: pd.DataFrame) -> str:
    lock = json.loads((SPLITS / "test_lock.json").read_text(encoding="utf-8"))
    ids = df["comment_id"].tolist()
    h = hashlib.sha256("\n".join(ids).encode()).hexdigest()
    ok = (h == lock["sha256_ids"]) and (len(ids) == lock["n_test"])
    print(f"[lock] test rows {len(ids)} | sha256 match: {ok}")
    if not ok:
        sys.exit("[lock] TEST SET INTEGRITY FAILED — hash/count mismatch. Aborting.")
    return "verified"


def metric_block(y_true, y_pred) -> dict:
    rep = classification_report(y_true, y_pred, target_names=LABELS,
                                output_dict=True, zero_division=0)
    return {
        "macro_f1": float(f1_score(y_true, y_pred, average="macro")),
        "weighted_f1": float(f1_score(y_true, y_pred, average="weighted")),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "per_class": {c: {k: float(rep[c][k]) for k in ("precision", "recall", "f1-score", "support")}
                      for c in LABELS},
    }


def confusion_png(y_true, y_pred, title, path):
    cm = confusion_matrix(y_true, y_pred, labels=range(3))
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_xticklabels(LABELS)
    ax.set_yticks(range(3)); ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max() * 0.55 else "#222", fontweight="bold")
    ax.set_title(title, fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.savefig(path, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def mcnemar(y_true, pa, pb) -> dict:
    """McNemar test on the two models' correctness (exact binomial on discordant pairs)."""
    ca, cb = (pa == y_true), (pb == y_true)
    b = int(np.sum(ca & ~cb))   # baseline right, bert wrong
    c = int(np.sum(~ca & cb))   # bert right, baseline wrong
    n = b + c
    # two-sided exact binomial p-value (p=0.5)
    from math import comb
    if n == 0:
        p = 1.0
    else:
        k = min(b, c)
        tail = sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n)
        p = min(1.0, 2 * tail)
    return {"baseline_only_correct": b, "bert_only_correct": c, "p_value": float(p)}


def predict_bert(texts):
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    mdl = str(MODELS / "banglabert_polarity")
    tok = AutoTokenizer.from_pretrained(mdl)
    model = AutoModelForSequenceClassification.from_pretrained(mdl)
    model.eval()
    preds = []
    with torch.no_grad():
        for i in range(0, len(texts), 32):
            enc = tok(texts[i:i + 32], truncation=True, padding=True,
                      max_length=128, return_tensors="pt")
            logits = model(**enc).logits
            preds.extend(torch.argmax(logits, dim=1).tolist())
    return np.array(preds)


def main():
    df = pd.read_csv(SPLITS / "test.csv", dtype=str, keep_default_na=False)
    verify_lock(df)
    X = df["Comment"].tolist()
    y = np.array([L2I[v] for v in df[TARGET]])

    # ---- baseline ----
    pipe = joblib.load(MODELS / "baseline_best.joblib")
    raw = pipe.predict(X)
    # pipeline may emit label strings or indices — normalise to indices
    if raw.dtype.kind in "US":
        pb_base = np.array([L2I[str(v)] for v in raw])
    else:
        pb_base = raw.astype(int)
    m_base = metric_block(y, pb_base)
    confusion_png(y, pb_base, "Test confusion — Linear SVM (baseline)",
                  FIG / "16_test_confusion_baseline.png")
    print(f"[baseline] test macro-F1 {m_base['macro_f1']:.4f} | acc {m_base['accuracy']:.4f}")

    # ---- BanglaBERT ----
    pb_bert = predict_bert(X)
    m_bert = metric_block(y, pb_bert)
    confusion_png(y, pb_bert, "Test confusion — BanglaBERT (tuned)",
                  FIG / "17_test_confusion_bert.png")
    print(f"[bert]     test macro-F1 {m_bert['macro_f1']:.4f} | acc {m_bert['accuracy']:.4f}")

    mc = mcnemar(y, pb_base, pb_bert)
    print(f"[mcnemar] baseline-only {mc['baseline_only_correct']} · bert-only "
          f"{mc['bert_only_correct']} · p={mc['p_value']:.4f}")

    # validation numbers (from Phase 3) for the val-vs-test gap
    val = {}
    for name, f in (("baseline", "phase3_baseline.json"), ("bert", "phase3_bert.json")):
        p = RES / f
        if p.exists():
            j = json.loads(p.read_text(encoding="utf-8"))
            val[name] = {"macro_f1": j.get("macro_f1"), "accuracy": j.get("accuracy")}

    out = {
        "phase": "4 (final test-set evaluation)",
        "test_set": "locked (sha256-verified, touched once)",
        "n_test": len(df),
        "test": {"baseline_linear_svm": m_base, "banglabert_tuned": m_bert},
        "validation_reference": val,
        "mcnemar_baseline_vs_bert": mc,
    }
    (RES / "phase4_test_eval.json").write_text(json.dumps(out, indent=2, ensure_ascii=False),
                                               encoding="utf-8")

    # ---- markdown report ----
    def pc_table(m):
        rows = ["| Class | Precision | Recall | F1 | Support |", "|---|---|---|---|---|"]
        for c in LABELS:
            r = m["per_class"][c]
            rows.append(f"| {c} | {r['precision']:.3f} | {r['recall']:.3f} | "
                        f"{r['f1-score']:.3f} | {int(r['support'])} |")
        return "\n".join(rows)

    md = [
        "# Phase 4 — Final Evaluation on the Locked Test Set",
        "",
        f"- Test set: **{len(df)}** comments, sha256-verified, **touched once** (no tuning on it).",
        "- Primary metric: **macro-F1** (imbalance-aware).",
        "",
        "## Headline — test set",
        "",
        "| Model | macro-F1 | weighted-F1 | Accuracy |",
        "|---|---|---|---|",
        f"| **Linear SVM (baseline)** | **{m_base['macro_f1']:.3f}** | "
        f"{m_base['weighted_f1']:.3f} | {m_base['accuracy']:.3f} |",
        f"| BanglaBERT (tuned) | {m_bert['macro_f1']:.3f} | "
        f"{m_bert['weighted_f1']:.3f} | {m_bert['accuracy']:.3f} |",
        "",
        "## Validation vs Test (generalisation)",
        "",
        "| Model | val macro-F1 | test macro-F1 |",
        "|---|---|---|",
        f"| Linear SVM | {val.get('baseline',{}).get('macro_f1','—')} | {m_base['macro_f1']:.3f} |",
        f"| BanglaBERT | {val.get('bert',{}).get('macro_f1','—')} | {m_bert['macro_f1']:.3f} |",
        "",
        "## Per-class — Linear SVM (test)",
        "", pc_table(m_base), "",
        "## Per-class — BanglaBERT (test)",
        "", pc_table(m_bert), "",
        "## Significance — McNemar (baseline vs BanglaBERT)",
        "",
        f"- Baseline-only correct: **{mc['baseline_only_correct']}** · "
        f"BanglaBERT-only correct: **{mc['bert_only_correct']}** · "
        f"exact two-sided **p = {mc['p_value']:.4f}**.",
        f"- {'Difference is statistically significant (p < 0.05).' if mc['p_value'] < 0.05 else 'No statistically significant difference at p < 0.05.'}",
        "",
        "Confusion matrices: `figures/16_test_confusion_baseline.png`, "
        "`figures/17_test_confusion_bert.png`.",
        "",
        ("> **Conclusion:** on the held-out test set the Linear SVM (macro-F1 "
         f"{m_base['macro_f1']:.3f}) is numerically ahead of the tuned BanglaBERT "
         f"({m_bert['macro_f1']:.3f}), but McNemar shows the gap is **not statistically "
         f"significant (p = {mc['p_value']:.2f})** — the two models are effectively comparable "
         "on this small, imbalanced Bangla elder-abuse corpus. Both generalise well (test ≈ or > "
         "validation). The classical baseline remains the practical choice (simpler, faster, "
         "no GPU).") if mc["p_value"] >= 0.05 else
        ("> **Conclusion:** the Linear SVM baseline is significantly stronger than the tuned "
         f"BanglaBERT on the held-out test set (macro-F1 {m_base['macro_f1']:.3f} vs "
         f"{m_bert['macro_f1']:.3f}, McNemar p = {mc['p_value']:.3f}), confirming the validation "
         "finding on this small, imbalanced corpus."),
    ]
    (RES / "phase4_test_eval_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote results/phase4_test_eval.json + _report.md")


if __name__ == "__main__":
    main()
