# Phase 5 — Statistical Significance & Language Confusion (batch 3)

## A. Association tests on the key cross-tabulations

| Cross-tabulation | χ² | dof | p-value | Cramér's V | effect | significant |
|---|---|---|---|---|---|---|
| emotion × abuse-type | 265.89 | 16 | 2.82e-47 | 0.17 | small | ✅ yes |
| polarity × abuse-type | 79.98 | 8 | 4.92e-14 | 0.132 | small | ✅ yes |
| emotion × platform | 150.4 | 4 | 1.67e-31 | 0.256 | small | ✅ yes |
| polarity × platform | 4.24 | 2 | 1.20e-01 | 0.043 | negligible | no |
| polarity × language | 27.25 | 4 | 1.77e-05 | 0.077 | negligible | ✅ yes |

**Fisher's exact (2×2)** — victim-blaming (yes/no) × Neglect/Abandonment (yes/no): odds ratio **4.87**, p = 3.90e-25 → statistically significant. Victim-blaming is strongly concentrated in Neglect/Abandonment topics.

> These tests turn the descriptive findings into **statistically validated** claims: emotion, polarity, victim-blaming and platform associations are not chance patterns.

## B. Language-wise confusion matrices

`figures/22_language_confusion.png` — for both models, on Bangla vs Banglish test comments. The SVM keeps a balanced diagonal on both scripts; BanglaBERT's diagonal breaks down on Banglish (it mislabels romanized comments), visually confirming the language-robustness finding.

