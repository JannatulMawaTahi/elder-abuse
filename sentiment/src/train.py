# -*- coding: utf-8 -*-
"""
Phase 3 (Part 1) — Classical baseline for SENTIMENT (polarity).

Trains on data/splits/train.csv, develops & reports on data/splits/val.csv.
The test set stays LOCKED (used only in Phase 4 final evaluation).

Features : TF-IDF word (1-2 gram) + char_wb (3-5 gram) union — char n-grams help
           with Bengali morphology and Banglish/code-mix spelling variation.
Models   : Logistic Regression, Linear SVM, Complement Naive Bayes
           (all class-weighted where supported, to handle Neg/Neu/Pos imbalance).
Metric   : macro-F1 (primary, imbalance-aware) + accuracy + per-class P/R/F1.

Outputs  : results/phase3_baseline.json
           results/phase3_baseline_report.md
           figures/14_baseline_confusion.png
           models/baseline_best.joblib   (best model by val macro-F1)
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import ComplementNB
from sklearn.metrics import (f1_score, accuracy_score, classification_report,
                             confusion_matrix)
import joblib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"
FIG = ROOT / "figures"
MODELS = ROOT / "models"
for d in (RES, FIG, MODELS):
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET = "polarity"
LABELS = ["Negative", "Neutral", "Positive"]


def load(name):
    df = pd.read_csv(SPLITS / f"{name}.csv", dtype=str, keep_default_na=False)
    return df["Comment"].tolist(), df[TARGET].tolist()


# A word = a run of Latin letters OR a run of Bengali-block chars. The Bengali range
# (U+0980–U+09FF) covers consonants, vowel signs (kar), and the virama (hasant), so
# conjuncts/matras stay INSIDE the token. The default pattern (\b\w\w+\b) treats vowel
# signs as boundaries and shreds Bangla words (কষ্ট → কষ, মনে হয় → মন হয).
BN_TOKEN = r"(?u)[A-Za-z]+|[ঀ-৿]+"


def make_features():
    word = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2,
                           token_pattern=BN_TOKEN, sublinear_tf=True)
    char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2,
                           sublinear_tf=True)
    return FeatureUnion([("word", word), ("char", char)])


def build_models():
    return {
        "logreg": LogisticRegression(max_iter=2000, C=4.0,
                                     class_weight="balanced", random_state=SEED),
        "linsvc": LinearSVC(C=1.0, class_weight="balanced", random_state=SEED),
        "cnb": ComplementNB(),
    }


def evaluate(model, Xv, yv):
    pred = model.predict(Xv)
    return {
        "macro_f1": round(float(f1_score(yv, pred, average="macro")), 4),
        "accuracy": round(float(accuracy_score(yv, pred)), 4),
        "weighted_f1": round(float(f1_score(yv, pred, average="weighted")), 4),
        "per_class": classification_report(yv, pred, labels=LABELS,
                                            output_dict=True, zero_division=0),
        "_pred": pred,
    }


def confusion_chart(y_true, y_pred, name):
    cm = confusion_matrix(y_true, y_pred, labels=LABELS)
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(3)); ax.set_xticklabels(LABELS)
    ax.set_yticks(range(3)); ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    thr = cm.max() * 0.55
    for i in range(3):
        for j in range(3):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > thr else "#222", fontweight="bold")
    ax.set_title(f"Validation confusion — {name}", fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.savefig(FIG / "14_baseline_confusion.png", dpi=140,
                bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    Xtr, ytr = load("train")
    Xva, yva = load("val")
    print(f"train {len(Xtr)} | val {len(Xva)}")

    feats = make_features()
    feats.fit(Xtr)                       # fit vectoriser on TRAIN only (no leakage)
    Xtr_f = feats.transform(Xtr)
    Xva_f = feats.transform(Xva)

    results = {}
    best_name, best_f1, best_model, best_pred = None, -1.0, None, None
    for name, clf in build_models().items():
        clf.fit(Xtr_f, ytr)
        m = evaluate(clf, Xva_f, yva)
        pred = m.pop("_pred")
        results[name] = m
        print(f"  {name:7s} macro-F1 {m['macro_f1']:.4f} | acc {m['accuracy']:.4f}")
        if m["macro_f1"] > best_f1:
            best_name, best_f1, best_model, best_pred = name, m["macro_f1"], clf, pred

    print(f"best: {best_name} (val macro-F1 {best_f1:.4f})")
    confusion_chart(yva, best_pred, best_name)

    # persist best pipeline (vectoriser + classifier)
    pipe = Pipeline([("features", feats), ("clf", best_model)])
    joblib.dump(pipe, MODELS / "baseline_best.joblib")

    out = {
        "task": "sentiment/polarity",
        "phase": "3 (classical baseline)",
        "dev_split": "val (test remains locked)",
        "n_train": len(Xtr), "n_val": len(Xva),
        "features": "TF-IDF word(1-2) + char_wb(3-5), fit on train",
        "best_model": best_name,
        "best_val_macro_f1": best_f1,
        "models": results,
    }
    (RES / "phase3_baseline.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # markdown
    pcb = results[best_name]["per_class"]
    md = [
        "# Phase 3 (Part 1) — Sentiment Baseline (classical ML)",
        "",
        f"- Train **{len(Xtr)}** · Val **{len(Xva)}** (test set locked, untouched).",
        "- Features: TF-IDF word (1-2 gram) + char_wb (3-5 gram), fit on train only.",
        "- Metric: **macro-F1** (primary, imbalance-aware).",
        "",
        "## Model comparison (validation)",
        "",
        "| Model | macro-F1 | Accuracy | weighted-F1 |",
        "|---|---|---|---|",
    ]
    pretty = {"logreg": "Logistic Regression", "linsvc": "Linear SVM", "cnb": "Complement NB"}
    for key in ["logreg", "linsvc", "cnb"]:
        m = results[key]
        star = " ⭐" if key == best_name else ""
        md.append(f"| {pretty[key]}{star} | {m['macro_f1']:.3f} | {m['accuracy']:.3f} | {m['weighted_f1']:.3f} |")
    md += [
        "",
        f"**Best: {pretty[best_name]}** (val macro-F1 **{best_f1:.3f}**).",
        "",
        "## Per-class (best model, validation)",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for c in LABELS:
        r = pcb[c]
        md.append(f"| {c} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1-score']:.3f} | {int(r['support'])} |")
    md += [
        "",
        "Confusion matrix: `figures/14_baseline_confusion.png`.",
        "Saved model: `models/baseline_best.joblib`.",
        "",
        "> This is the **baseline** the transformer (BanglaBERT, Phase 3 Part 2) must beat.",
    ]
    (RES / "phase3_baseline_report.md").write_text("\n".join(md), encoding="utf-8")
    print("wrote results/phase3_baseline.json + _report.md + figures/14_baseline_confusion.png")


if __name__ == "__main__":
    main()
