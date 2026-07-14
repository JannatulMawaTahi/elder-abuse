# Phase 3 (Part 2) — BanglaBERT fine-tune (SENTIMENT / polarity)

- Model: **sagorsarker/bangla-bert-base**, class-weighted cross-entropy.
- **Tuned run:** 5 epochs, warmup 0.1, weight-decay 0.01, best val-checkpoint kept (best = epoch 1).
- Train **1609** / Val **345** (test locked). Metric: **macro-F1**.

## Result vs baseline (validation)

| Model | macro-F1 | Accuracy |
|---|---|---|
| **Linear SVM (baseline)** ⭐ | **0.653** | **0.762** |
| BanglaBERT (tuned, 5 epochs) | 0.579 | 0.713 |
| BanglaBERT (initial, 3 epochs) | 0.549 | 0.684 |

## Per-class (tuned BanglaBERT, validation)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.796 | 0.852 | 0.823 | 243 |
| Neutral | 0.426 | 0.303 | 0.354 | 76 |
| Positive | 0.516 | 0.615 | 0.561 | 26 |

## Per-epoch validation macro-F1

| epoch | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| macro-F1 | **0.579** | 0.467 | 0.573 | 0.567 | 0.543 |

Confusion matrix: `figures/15_bert_confusion.png`. Saved model: `models/banglabert_polarity/`.

> **Finding:** Tuning lifted BanglaBERT from 0.549 → **0.579**, but the classical TF-IDF +
> Linear SVM baseline (**0.653**) still outperforms it on this small (1,609-train), imbalanced
> dataset. This is a genuine, publishable result: strong classical baselines are hard to beat
> for short-text classification with limited data. Next: XLM-R / mBERT comparison, and more
> labelled data would likely be what closes the gap.
