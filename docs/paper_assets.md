# Paper Assets — Sentiment & Emotion Analysis of Elder-Abuse Comments

*Auto-generated from `results/*.json` by `src/build_paper_assets.py` — regenerate after any experiment so the tables stay in sync.*

## 1. Dataset (→ paper §Dataset)

| Item | Value |
|---|---|
| Raw scraped comments | 2,454 |
| After cleaning | 2301 |
| After text-dedup (modelling set) | 2299 |
| Language mix | Bangla 1899 · Banglish (Latin) 367 · Code-mixed 33 · Arabic 2 |
| Polarity distribution | Negative 1619 · Neutral 512 · Positive 170 |
| Emotion distribution | Anger/Condemnation 812 · Victim-blaming 293 · Grief/Sympathy 182 · Prayer/Religious 213 · Neutral-Other 801 |
| Split (train/val/test) | train 1609 · val 345 · test 345 — stratified, seed 42 |
| Platforms | YouTube 1632 · Facebook 669 |

**Label scheme:** 2 levels — polarity (Negative/Neutral/Positive) + fine-grained emotion (Anger/Condemnation · Grief/Sympathy · Prayer/Religious · Victim-blaming · Neutral-Other). Test set is sha256-locked. Human inter-annotator (Kappa) validation is in progress.

## 2. Model results (→ paper §Experiments/Results)

| Model | val macro-F1 | **test macro-F1** | test acc | test weighted-F1 |
|---|---|---|---|---|
| **Linear SVM (TF-IDF word+char)** | 0.661 | **0.683** | 0.788 | 0.780 |
| BanglaBERT (fine-tuned, tuned) | 0.579 | 0.611 | 0.728 | 0.718 |

**Significance (McNemar):** baseline-only-correct 51 · BERT-only-correct 30 · p = 0.026 → **significant**. Both models generalise (test ≥ validation). The classical baseline is the practical choice.

**Per-class (test) — Linear SVM**

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.837 | 0.905 | 0.870 | 243 |
| Neutral | 0.591 | 0.506 | 0.545 | 77 |
| Positive | 0.812 | 0.520 | 0.634 | 25 |

**Per-class (test) — BanglaBERT**

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Negative | 0.806 | 0.856 | 0.830 | 243 |
| Neutral | 0.452 | 0.364 | 0.403 | 77 |
| Positive | 0.600 | 0.600 | 0.600 | 25 |

## 2b. Representative errors (both models wrong — → paper §Error analysis)

| id | true | SVM | BanglaBERT | comment |
|---|---|---|---|---|
| C00064 | Neutral | Negative | Negative | Ai Milton shomdder keo koto bitorko korselo.jara Valo kaj Kore tader o char nai |
| C00163 | Neutral | Negative | Negative | উনাকে বৃদ্ধা আশ্রমে তো দিতে পারে, সাংবাদিক  ভাইরা চাইলে পারবে |
| C00206 | Positive | Neutral | Negative | নাদিরা বেগম কি বেঁচে আছেন?  She seems very lonely and you don't  even mentioned about her children. I hope she find peac |
| C00277 | Neutral | Negative | Negative | ৩১ বছর আগে তো উনি বুড়া ছিলেন না |
| C00282 | Neutral | Negative | Negative | আপনি কলেজে শিক্ষক আপনার সন্তানদের মানুষ করতে যে পরিমাণ পরিশ্রম হয়েছে আপনার। তাহলে আপনাকে মানুষের মতো মানুষ করতে আপনার প |
| C00316 | Neutral | Negative | Negative | এমন দুর্দশা থেকে মুক্ত করতেই কুরআনের আগমন। আপনারা আধুনিক হতে হতে আমেরিকাকে ছাড়িয়ে যেতে পারেন, তবে শান্তি জিনিসটা কুরআন |
| C00369 | Neutral | Positive | Negative | Briddasromtir payment ki rokom ,ki dhoroner sujog shubidha achey ? Address din pls.Ami ctg thekey dekchi.amr boyosh 70 b |
| C00414 | Positive | Negative | Negative | Perfect bou hote parbo kina jni na kintu sosur sasuri k kokhonoi biddhasrom a pathabo na😢 |

> Most hard cases sit on the Neutral↔Negative boundary (rhetorical questions, mixed sentiment, sarcasm) — inherently ambiguous even for humans.

## 3. Deep analysis (→ paper §Analysis/Discussion)

**3a. Language-wise robustness (test accuracy)**

| Language | n | SVM | BanglaBERT |
|---|---|---|---|
| Bangla | 288 | 0.809 | 0.774 |
| Banglish (Latin) | 52 | 0.673 | 0.462 |
| Code-mixed | 5 | 0.800 | 0.800 |

> BanglaBERT collapses on Latin-script Banglish (Bangla-script pretraining); the char-ngram SVM stays robust — the main reason the baseline wins overall.

**3b. Embedding structure:** KMeans↔label Adjusted Rand Index — emotion 0.051 (k=5), polarity 0.059 (k=3). Low ⇒ classes overlap in embedding space (semantic, not lexically separable) ⇒ supervised labels are needed.

**3c. Religious framing:** 22.1% of comments use religious language; within them — Anger/Condemnation 23%, Grief/Sympathy 5%, Prayer/Religious 34%, Victim-blaming 24%, Neutral-Other 14%. Religion carries both blessing and blame/condemnation.

**3d. Explainability — top Linear-SVM word features per class**

- **Negative:** `ai` · `বিচার` · `এমন` · `শিক্ষিত` · `অবস্থা` · `o` · `মহিলা` · `সে` · `দেশে` · `না`
- **Neutral:** `করা উচিত` · `মা বাবা` · `ভাবে` · `দাও` · `করতে হবে` · `baber` · `হতে পারে` · `সাহায্য করবেন` · `চিনি` · `নাকি`
- **Positive:** `ভিডিও` · `আল্লাহ সবাইকে` · `আমার বাবা` · `good` · `ধন্যবাদ` · `সহায়` · `ভালো` · `k` · `সুন্দর` · `babai`

**3e. Error analysis (test):** dominant confusion is **Neutral↔Negative** for both models. BanglaBERT error rate 0.51 on Latin/code-mixed and 0.43 on emoji comments vs ~0.23 otherwise; the SVM is stable across both.

**3f. Statistical significance — Chi-square / Fisher's exact**

| Association | χ² | p-value | Cramér's V | significant |
|---|---|---|---|---|
| emotion × abuse-type | 265.89 | 2.8e-47 | 0.17 | yes |
| polarity × abuse-type | 79.98 | 4.9e-14 | 0.132 | yes |
| emotion × platform | 150.4 | 1.7e-31 | 0.256 | yes |
| polarity × platform | 4.24 | 1.2e-01 | 0.043 | no |
| polarity × language | 27.25 | 1.8e-05 | 0.077 | yes |

Fisher's exact — victim-blaming × Neglect/Abandonment: odds ratio **4.87**, p = 3.9e-25 (significant). The key descriptive findings (emotion↔topic, emotion↔platform, victim-blaming↔topic) are statistically validated; overall polarity↔platform is NOT significant (a fair nuance).

## 4. Figure index (→ where each goes)

| Figure | Shows | Paper section |
|---|---|---|
| `figures/01_polarity_dist.png` | Polarity distribution | Dataset |
| `figures/02_emotion_dist.png` | Emotion distribution | Dataset |
| `figures/03_polarity_x_emotion.png` | Polarity × emotion | Dataset |
| `figures/04_abusetype_x_emotion.png` | Abuse-type × emotion | Analysis |
| `figures/05_abusetype_x_polarity.png` | Abuse-type × polarity | Analysis |
| `figures/06_platform_x_emotion.png` | Platform × emotion | Analysis |
| `figures/07_language_x_polarity.png` | Language × polarity | Analysis |
| `figures/08_length_by_emotion.png` | Comment length by emotion | Analysis |
| `figures/09_likes_by_emotion.png` | Engagement (likes) by emotion | Analysis |
| `figures/10_victimblame_by_abuse.png` | Victim-blaming by abuse type | Analysis (key) |
| `figures/11_prayer_by_abuse.png` | Prayer/religious by abuse type | Analysis |
| `figures/12_top_tokens.png` | Distinctive tokens per emotion | Analysis |
| `figures/13_wordclouds.png` | Word clouds per emotion | Analysis |
| `figures/14_baseline_confusion.png` | SVM confusion (validation) | Experiments |
| `figures/15_bert_confusion.png` | BanglaBERT confusion (validation) | Experiments |
| `figures/16_test_confusion_baseline.png` | SVM confusion (test) | Experiments |
| `figures/17_test_confusion_bert.png` | BanglaBERT confusion (test) | Experiments |
| `figures/18_lang_distribution.png` | Language distribution + polarity mix | Analysis |
| `figures/19_lang_model_accuracy.png` | Model accuracy by language | Analysis (key) |
| `figures/20_embedding_tsne_emotion.png` | t-SNE of BanglaBERT embeddings | Analysis |
| `figures/21_religious_framing.png` | Religious vs non-religious framing | Analysis |
| `figures/22_language_confusion.png` | Language-wise confusion (SVM vs BanglaBERT) | Analysis (key) |
| `figures/23_per_class_metrics.png` | Per-class Precision/Recall/F1 (both models) | Experiments |

## 5. Key findings / contributions (paper talking points)

- A new **annotated Bangla/Banglish elder-abuse dataset** with a novel **victim-blaming** emotion class — the main contribution.
- **70% of public reactions are Negative**; anger and victim-blaming dominate the emotion mix.
- **Victim-blaming is topic-specific** — high for Neglect/Abandonment, ~0% for Murder.
- **Platform effect** — victim-blaming far higher on YouTube than Facebook; grief earns the most likes.
- **Classical TF-IDF + Linear SVM beats fine-tuned BanglaBERT** on this small, imbalanced, code-switched corpus (test macro-F1 0.68 vs 0.61; McNemar p = 0.026, significant).
- **Why:** BanglaBERT can't read Latin-script Banglish (err 0.51) or emoji (err 0.43); the char-ngram SVM is robust to both — a concrete, quantified explanation.
- **Religion is the vehicle of both blessing and condemnation** (22% of comments).
- Transparent explainability from SVM coefficients; hardest boundary is Neutral↔Negative.

## 6. Limitations (→ paper §Limitations)

- **Labels are model-generated (silver).** A codebook was followed, but human inter-annotator (Fleiss'/Cohen's Kappa) validation is planned, not yet complete — reliability is not yet quantified on gold labels.
- **Small and imbalanced** (2,301 comments; ~70% Negative, few Positive) — caps rare-class performance and limits transformer fine-tuning.
- **Narrow domain** — YouTube/Facebook comments on elder-abuse videos; findings may not transfer to other topics or platforms.
- **Subjective fine-grained emotion** — victim-blaming vs anger vs neutral is genuinely ambiguous at the boundary; some disagreement is expected.
- **Point-in-time scrape** — no temporal analysis; `abuse_type` is a video-level topic, not a per-comment label.
- **Model blind spots** — BanglaBERT under-reads Latin-script Banglish and emoji, so the transformer results are a lower bound for code-switched text.

## 7. Ethics statement (→ paper §Ethics)

- Only **publicly posted** social-media comments are used; no private messages or personal data.
- Analysis is **aggregate** — we report patterns, never profile, rank, or expose individual commenters; commenter names are not analysed or published.
- The topic (elder abuse) and victims are treated with care; **no attempt to re-identify** victims or commenters.
- The **victim-blaming** class is studied to *understand and surface* a harmful social attitude — not to endorse it.
- Comments may contain offensive language; they are used solely for research and shown only as de-identified examples.
- Data were collected in line with each platform's public-content terms; no user was contacted.

