# Phase 3 (Part 1) — Sentiment Baseline (classical ML)

- Train **1609** · Val **345** (test set locked, untouched).
- Features: TF-IDF word (1-2 gram) + char_wb (3-5 gram), fit on train only.
- Metric: **macro-F1** (primary, imbalance-aware).

## Model comparison (validation)

| Model | macro-F1 | Accuracy | weighted-F1 |
|---|---|---|---|
| Logistic Regression | 0.653 | 0.759 | 0.758 |
| Linear SVM ⭐ | 0.661 | 0.777 | 0.766 |
| Complement NB | 0.487 | 0.704 | 0.669 |

**Best: Linear SVM** (val macro-F1 **0.661**).

## Per-class (best model, validation)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.833 | 0.905 | 0.868 | 243 |
| Neutral | 0.559 | 0.434 | 0.489 | 76 |
| Positive | 0.682 | 0.577 | 0.625 | 26 |

Confusion matrix: `figures/14_baseline_confusion.png`.
Saved model: `models/baseline_best.joblib`.

> This is the **baseline** the transformer (BanglaBERT, Phase 3 Part 2) must beat.