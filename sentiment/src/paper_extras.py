# -*- coding: utf-8 -*-
"""
Phase 6 extra — per-class metric figure for the paper.

Reads results/phase4_test_eval.json and draws a grouped bar chart of per-class
Precision / Recall / F1 for both models on the held-out test set (figure 23).

    python sentiment/src/paper_extras.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "figures"
LABELS = ["Negative", "Neutral", "Positive"]
NAVY, RED = "#1D3557", "#E63946"

t4 = json.loads((RES / "phase4_test_eval.json").read_text(encoding="utf-8"))
tb = t4["test"]["baseline_linear_svm"]["per_class"]
tr = t4["test"]["banglabert_tuned"]["per_class"]

fig, axes = plt.subplots(1, 3, figsize=(12, 4.3), sharey=True)
metrics = ["precision", "recall", "f1-score"]
titles = ["Precision", "Recall", "F1-score"]
x = np.arange(len(LABELS)); w = 0.38
for ax, m, t in zip(axes, metrics, titles):
    svm = [tb[c][m] for c in LABELS]
    bert = [tr[c][m] for c in LABELS]
    ax.bar(x - w/2, svm, w, label="Linear SVM", color=NAVY)
    ax.bar(x + w/2, bert, w, label="BanglaBERT", color=RED)
    ax.set_xticks(x); ax.set_xticklabels(LABELS, fontsize=9)
    ax.set_title(t, fontweight="bold"); ax.set_ylim(0, 1)
    for i in range(len(LABELS)):
        ax.text(i - w/2, svm[i] + .02, f"{svm[i]:.2f}", ha="center", fontsize=7.5)
        ax.text(i + w/2, bert[i] + .02, f"{bert[i]:.2f}", ha="center", fontsize=7.5)
axes[0].set_ylabel("score"); axes[0].legend(fontsize=9, loc="upper right")
fig.suptitle("Per-class Precision / Recall / F1 on the held-out test set",
             fontsize=13, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig(FIG / "23_per_class_metrics.png", dpi=140, facecolor="white")
plt.close(fig)
print("saved figures/23_per_class_metrics.png")
