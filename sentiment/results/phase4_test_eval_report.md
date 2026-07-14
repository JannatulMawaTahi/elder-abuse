# Phase 4 — Final Evaluation on the Locked Test Set

- Test set: **345** comments, sha256-verified, **touched once** (no tuning on it).
- Primary metric: **macro-F1** (imbalance-aware).

## Headline — test set

| Model | macro-F1 | weighted-F1 | Accuracy |
|---|---|---|---|
| **Linear SVM (baseline)** | **0.683** | 0.780 | 0.788 |
| BanglaBERT (tuned) | 0.611 | 0.718 | 0.728 |

## Validation vs Test (generalisation)

| Model | val macro-F1 | test macro-F1 |
|---|---|---|
| Linear SVM | None | 0.683 |
| BanglaBERT | 0.5794370976122571 | 0.611 |

## Per-class — Linear SVM (test)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.837 | 0.905 | 0.870 | 243 |
| Neutral | 0.591 | 0.506 | 0.545 | 77 |
| Positive | 0.812 | 0.520 | 0.634 | 25 |

## Per-class — BanglaBERT (test)

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.806 | 0.856 | 0.830 | 243 |
| Neutral | 0.452 | 0.364 | 0.403 | 77 |
| Positive | 0.600 | 0.600 | 0.600 | 25 |

## Significance — McNemar (baseline vs BanglaBERT)

- Baseline-only correct: **51** · BanglaBERT-only correct: **30** · exact two-sided **p = 0.0257**.
- Difference is statistically significant (p < 0.05).

Confusion matrices: `figures/16_test_confusion_baseline.png`, `figures/17_test_confusion_bert.png`.

> **Conclusion:** the Linear SVM baseline is significantly stronger than the tuned BanglaBERT on the held-out test set (macro-F1 0.683 vs 0.611, McNemar p = 0.026), confirming the validation finding on this small, imbalanced corpus.
