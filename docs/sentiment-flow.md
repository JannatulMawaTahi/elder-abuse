# Sentiment Analysis Component — Flow & Progress Tracker

> **Goal:** A publishable research paper on **sentiment / emotion analysis of social-media
> comments about elder abuse** (Bangla + Banglish + English), Supervisor brief:
> "যত বেশি deep analysis তত better."
>
> This file is the **single source of truth** for the sentiment paper. It is updated
> **immediately after every finished step** so progress is always trackable.
>
> Status legend:  ⬜ not started · 🔄 in progress · ✅ done · ⏸️ blocked / waiting on decision

---

## 0. Guiding principle — where "perfect" metrics come from

Trustworthy + high evaluation metrics come from **three** things, not tricks:
1. **Clean, consistent labels** (low annotator noise → higher achievable macro-F1).
2. **Zero data leakage** (dedupe BEFORE split; locked test set).
3. **Right metrics for imbalanced data** (macro-F1 primary, not accuracy).

Every phase below is designed around these three.

---

## 1. Dataset — what we actually have (profiled, real numbers)

- **2454 rows × 9 columns**: `platform, source_id, source_url, Name, Date, Likes, Comment, Comment URL, abuse_type`
- **Platform:** YouTube 1750 · Facebook 704
- **abuse_type (VIDEO-level, not comment-level):** Neglect 777 · Abandonment 708 · Physical Abuse 475 · Verbal Abuse 309 · Murder 185
- **Sources:** 32 unique (most capped at exactly 100 comments → scraper limit)
- **Language:** Bangla 78% · Latin/Banglish 16% · emoji-only 5% · bn+en mix 34 · Arabic 3

### Known data issues (confirmed by profiling)
| # | Issue | Impact | Action |
|---|---|---|---|
| 1 | `Date` = scrape time, NOT post time (20 comments share exact same second) | Temporal analysis invalid | Drop temporal claims OR caveat as year-level "indicative only" |
| 2 | `abuse_type` is video-level (0 of 32 sources have >1 label) | Not a per-comment ground truth | Use only as "video context" in cross-analysis |
| 3 | **No sentiment label exists** | Cannot train without it | Manual annotation (Phase 1) |
| 4 | 62 exact duplicates, 118 emoji-only, ~36 spam/off-topic | Label noise | Remove in cleaning (Phase 0) |
| 5 | Likes: 84% are 0 | Weak engagement signal | Engagement analysis = secondary only |
| 6 | Class imbalance + Murder only on Facebook | Confound | Class-weighted loss + report caveat |

> ✅ **Encoding is FINE** — the raw `.csv` on disk is clean UTF-8 (0% mojibake). The garbled
> text seen earlier was only a chat-paste display artifact. **No encoding fix needed.**

---

## 2. Folder structure (decided)

```
sentiment/
├── data/
│   ├── raw/          original scraped CSV (untouched)
│   ├── interim/      cleaned.csv, removed.csv, language-tagged
│   ├── annotated/    annotation batches + final gold labels
│   └── splits/       train.csv / val.csv / test.csv (test locked)
├── notebooks/        01_cleaning · 02_annotation_prep · 03_eda · 04_modeling · 05_deep_analysis
├── src/              clean.py · dataset.py · train.py · evaluate.py · analyze.py
├── models/           saved checkpoints (gitignored)
├── results/          metrics.json, confusion matrices, kappa.json
├── figures/          paper-ready charts/tables
└── annotation_guideline.md
```
**Rationale:** self-contained & reproducible; `raw/` never modified; logic in `src/` imported by
notebooks (no duplication, testable); separate from the existing abuse-classifier work.

---

## 3. Label scheme (proposed — pending confirmation)

- **Level A — Sentiment polarity (3):** Negative / Neutral / Positive  → robust, high-agreement baseline.
- **Level B — Fine-grained emotion (5):** Anger/Condemnation · Grief/Sympathy · Prayer/Religious ·
  Victim-blaming · Neutral-Other  → the novel contribution.

---

## 4. Decisions (resolved)

- [x] **D1 — Label scheme:** ✅ **A+B both** (polarity + 5-emotion).
- [x] **D2 — Second annotator:** ✅ Lamia + a teammate (two annotators → Cohen's Kappa reportable).
- [x] **D3 — Copy raw CSV** from `Downloads/` into `sentiment/data/raw/`: ✅ yes.
- [x] **D4 — Labeling strategy:** ✅ **Hybrid (AI silver + human-validated)**. The model labels
  **all 2301** comments (silver labels, the training set). Humans then label only the **450 overlap**
  set *blind* to (a) measure human–human Cohen's Kappa and (b) validate the AI silver labels
  (human-gold vs AI agreement). This keeps it publishable (no circular "AI validates AI") while
  cutting human effort from 2301 → 450 each.
- [x] **D5 — Overlap sampling:** ✅ **450, stratified by AI silver emotion** (so rare classes —
  Grief, Prayer, Victim-blaming — are represented in Kappa). **Blind** pre-fill: annotators get
  empty polarity/emotion columns; AI labels are kept in a hidden key (`overlap_ids.csv`).

---

## 5. Phase-by-phase plan & progress

### Phase 0 — Data cleaning  ✅
- [x] Copy raw CSV → `sentiment/data/raw/all_comments_merged.csv`
- [x] Remove junk → `interim/removed.csv` (153 rows, with `remove_reason`, audited 0 false positives)
- [x] Language tagging (bengali / latin / bn+en / arabic / emoji)
- [x] Light normalization (emoji & punctuation kept — they carry emotion)
- [x] Output `interim/cleaned.csv` + `results/phase0_cleaning_report.md`
- **Result:** raw **2454 → kept 2301** (removed: textless 118, spam 13, exact-dup 13, too-short 9).
  Kept language: bengali 1899 · latin 367 · bn+en 33 · arabic 2.
  Kept abuse_type: Neglect 727 · Abandonment 660 · Physical 448 · Verbal 297 · Murder 169.
- **Code:** `sentiment/src/clean.py`

### Phase 1 — Annotation (Hybrid: AI silver + human validation)  🔄 (silver done; waiting on human labelling)
- [x] Write `annotation_guideline.md` (polarity + 5-emotion definitions + examples + tie-break rules)
- [x] **AI silver-labelling — ALL 2301 comments labelled** (polarity + emotion), batched into
  `annotated/llm_codes/batch_001..016.csv` (per-batch files = resilient to interruptions).
  - `src/dump_batch.py` (dumps a batch for labelling) + `src/assemble_llm_labels.py`
    (combines batches, validates full coverage / no dups, maps codes → full labels).
  - **Output: `annotated/llm_labels.csv`** (2301 rows, 0 missing / 0 extra — coverage verified).
  - Silver distribution — polarity: **Negative 1619 · Neutral 512 · Positive 170**;
    emotion: **Anger/Condemnation 808 · Neutral-Other 788 · Victim-blaming 310 · Prayer 213 · Grief 182**.
- [x] Build annotator sheets — `src/build_annotation.py` (SEED=42, **stratified by AI silver emotion**)
  - `annotated/annotator_A.xlsx` → Lamia (1375 rows = 450 overlap + 925), **blind** (empty labels)
  - `annotated/annotator_B.xlsx` → teammate (1376 rows = 450 overlap + 926), **blind**
  - `annotated/overlap_ids.csv` = **hidden key** (450 ids + `ai_polarity`,`ai_emotion`; NOT given to
    annotators). Overlap emotion coverage: ANG 158 · OTH 154 · BLM 61 · PRY 42 · GRF 35.
  - xlsx have dropdown validation on polarity & emotion + Instructions sheet
- [x] Write `src/kappa.py` (run AFTER labelling → human–human Cohen's Kappa, target κ ≥ 0.70)
- [ ] ⏳ **Lamia + teammate fill the two xlsx independently, blind** (human step)
- [ ] Run `python sentiment/src/kappa.py`; refine guideline if κ < 0.70
- [ ] Resolve disagreements on the 450 → adjudicated **gold-450**; then compare gold-450 vs
  AI silver (human-vs-AI agreement) to validate the silver labels (script TBD)
- [ ] Final training labels = AI silver for all 2301, with gold-450 as the human-verified test/anchor
- **Done when:** kappa.json (human–human) + silver-validation report saved.

### Phase 2 — Dataset construction  ✅ (sentiment / polarity target)
> **Emotion is deferred for now** (Lamia's call). The `emotion` column is kept in every
> split file, so emotion can be activated later on these **same** splits (locked test stays
> intact) without re-splitting. Active modelling target = **polarity**.
- [x] Final dedup on normalised comment text (prevents train/test leakage) → removed **2**
  near-duplicate rows (2301 → **2299**).
- [x] Stratified **70/15/15** split by polarity (SEED=42) → `data/splits/train.csv` (1609) ·
  `val.csv` (345) · `test.csv` (345). All original columns (incl. `emotion`) preserved.
- [x] **Test set locked** → `data/splits/test_lock.json` (id list + sha256, n=345).
- [x] Class-distribution report → `results/phase2_split.json` + `results/phase2_split_report.md`.
  - Polarity ratios held near-identical across splits (overall Neg 1618 / Neu 511 / Pos 170;
    train Neg 1132 / Neu 358 / Pos 119; val Neg 243 / Neu 76 / Pos 26; test Neg 243 / Neu 77 / Pos 25).
- **Code:** `sentiment/src/dataset.py`
- **Done.** train/val/test CSVs + lock + class-distribution table saved.

### Phase 3 — Modeling  🔄 (baseline + BanglaBERT both trained; tuning next)
- [x] **Baseline: TF-IDF + classical ML** — `src/train.py`. Features = TF-IDF word(1-2) +
  char_wb(3-5), fit on **train only** (no leakage). **Bengali-aware word `token_pattern`**
  (`[A-Za-z]+|[ঀ-৿]+`) so matras/conjuncts stay inside tokens (default `\w` shredded Bangla words).
  Models compared on **val** (test locked):
  | Model | val macro-F1 | accuracy |
  |---|---|---|
  | Logistic Regression | 0.653 | 0.759 |
  | **Linear SVM (best)** | **0.661** | **0.777** |
  | Complement NB | 0.487 | 0.704 |
  - Outputs: `results/phase3_baseline.json` + `_report.md`, `figures/14_baseline_confusion.png`,
    `models/baseline_best.joblib`.
- [x] **BanglaBERT fine-tune DONE** — `src/train_bert.py`, `sagorsarker/bangla-bert-base`,
  class-weighted CE, 3 epochs (CPU), val-based best checkpoint.
  | Model | val macro-F1 | accuracy |
  |---|---|---|
  | Linear SVM (baseline) | **0.661** | **0.777** |
  | BanglaBERT | 0.549 | 0.684 |
  - Per-class (BERT, val): Negative F1 0.810 · Neutral 0.413 · Positive 0.423.
  - **Finding:** on this small (1,609 train), imbalanced set the classical baseline **beats**
    the fine-tuned transformer — a defensible result (strong TF-IDF baseline on short texts;
    BERT undertrained at 3 CPU epochs, no HP search). Baseline is current best.
  - Outputs: `results/phase3_bert.json` + `_report.md`, `figures/15_bert_confusion.png`,
    `models/banglabert_polarity/`.
- [x] **BanglaBERT tuned DONE** — 5 epochs, warmup 0.1, weight-decay 0.01, class-weighted,
  best val-checkpoint (best = epoch 1). **Val macro-F1 0.579 / acc 0.713** — up from the 3-epoch
  0.549, but **still below the Linear SVM baseline (0.661)**.
  | Model | val macro-F1 | accuracy |
  |---|---|---|
  | **Linear SVM (baseline)** | **0.661** | **0.777** |
  | BanglaBERT (tuned, 5ep) | 0.579 | 0.713 |
  | BanglaBERT (initial, 3ep) | 0.549 | 0.684 |
  - Per-epoch val macro-F1: 0.579 / 0.467 / 0.573 / 0.567 / 0.543 (best epoch 1 kept).
  - Outputs: `results/phase3_bert.json`+`_report.md` (3ep archived as `phase3_bert_3ep.json`),
    `figures/15_bert_confusion.png`, `models/banglabert_polarity/`.
- [ ] Compare XLM-R / mBERT (swap `MODEL_NAME`) — optional, to round out the model table.
- **Done when:** baseline + tuned-transformer metrics both in `results/`. ✅ Both done — **classical
  baseline is the current best**; transformer trails on this small, imbalanced set.

### Phase 4 — Evaluation  ✅ (locked test set, touched once)
- [x] **Final test-set eval** — `src/evaluate.py`. Test set sha256-verified before use.
  | Model | val macro-F1 | **test macro-F1** | test acc | test weighted-F1 |
  |---|---|---|---|---|
  | **Linear SVM (baseline)** | 0.661 | **0.683** | 0.788 | 0.780 |
  | BanglaBERT (tuned) | 0.579 | **0.611** | 0.728 | 0.718 |
  - **Both generalise well** (test ≈ or **>** validation — no overfitting).
  - [x] Per-class P/R/F1 + weighted-F1 + accuracy (in `results/phase4_test_eval_report.md`).
  - [x] Confusion matrices → `figures/16_test_confusion_baseline.png`, `17_test_confusion_bert.png`.
  - [x] **McNemar (baseline vs BanglaBERT):** baseline-only-correct 51 · bert-only 30 ·
    **p = 0.026 → statistically significant.** After the Bengali tokenizer fix the SVM
    (test macro-F1 0.683) **significantly outperforms** BanglaBERT (0.611). SVM is also the
    practical choice (simpler, faster, no GPU).
  - [ ] 3–5 seeds → mean ± std (future; single frozen run reported now).
  - Outputs: `results/phase4_test_eval.json` + `_report.md`.
- **Done when:** full metrics table + plots in `figures/`. ✅
- **Bug fixed during this phase:** `train_bert.py` did not save the tokenizer with the model, so a
  naive reload used the wrong tokenizer and predicted all-Neutral (macro-F1 0.12). Fixed by
  `tok.save_pretrained(...)` + evaluating with the correct tokenizer → real numbers above.

### Phase 5 — Deep analysis  🔄 (batch 1 done)
- [x] Abuse-type × emotion cross-tab — done in EDA (`figures/04_abusetype_x_emotion.png`).
- [x] Victim-blaming prevalence — done in EDA (`figures/10_victimblame_by_abuse.png`).
- [x] **Language-wise model robustness (batch 1)** — `src/deep_analysis.py`, held-out test:
  | Language | n | SVM acc | BanglaBERT acc |
  |---|---|---|---|
  | Bangla | 288 | 0.809 | 0.774 |
  | Banglish (Latin) | 52 | **0.673** | **0.462** |
  | Code-mixed | 5 | 0.80 | 0.80 *(n=5, ignore)* |
  - ⭐ **Key finding:** BanglaBERT collapses on **Latin-script Banglish** (0.77→0.46) because it
    was pre-trained on Bangla script; the char-ngram SVM stays robust (0.79→0.71). Since ~16% of
    the corpus is Latin-script, **this largely explains why the classical baseline wins overall.**
    Figures: `18_lang_distribution.png`, `19_lang_model_accuracy.png`.
- [x] **Embedding structure (batch 1)** — BanglaBERT mean-pooled embeddings, KMeans vs labels:
  ARI(cluster↔emotion, k5) = **0.051**, ARI(cluster↔polarity, k3) = **0.059** (both low).
  t-SNE (`figures/20_embedding_tsne_emotion.png`) shows heavy overlap + a detached Latin-script
  blob. **Interpretation:** fine-grained emotion on short social text is not linearly separable in
  embedding space (semantic, not lexical) → supervised labels are genuinely needed, and BanglaBERT
  under-represents Banglish. Honest, not a weakness of the label scheme.
- [x] **Religious-framing (batch 1)** — **22.1%** of comments use religious language. Within them:
  Prayer/Religious 34%, Victim-blaming 24%, Anger 23% — **religion is the vehicle of BOTH blessing
  and condemnation/blame**. Religious comments skew more Positive (14.4% vs 5.4% dua/blessing).
  Figure: `figures/21_religious_framing.png`.
- [x] **Explainability (batch 2)** — `src/explain_errors.py`. Top word-features per polarity from
  the Linear-SVM coefficients (transparent, no black box):
  - **Negative** → বিচার · শিক্ষিত · অবস্থা · মহিলা · এমন (blame/justice)
  - **Neutral** → করা উচিত · মা বাবা · করতে হবে · হতে পারে · সাহায্য করবেন (advice/conditional)
  - **Positive** → ভিডিও · আল্লাহ সবাইকে · আমার বাবা · ধন্যবাদ · ভালো + English `good`/`thank` + Arabic `الله`
  - (Words are now clean full Bangla after the tokenizer fix — earlier they were shredded fragments.)
- [x] **Error analysis (batch 2)** — held-out test:
  - Dominant confusion for **both** models is **Neutral↔Negative** (the fuzzy middle) — Neutral→Neg
    34 (SVM)/43 (BERT), Negative→Neu 30/31.
  - **BanglaBERT weaknesses confirmed:** error rate **0.51 on Latin/code-mixed** vs 0.23 Bangla,
    and **0.43 on emoji comments** vs 0.25 without — its Bangla-script pretraining can't read Latin
    Banglish or emoji; the char-ngram SVM handles both (emoji err 0.20).
  - Both-models-wrong: 43/345; BERT-only-wrong (51) > SVM-only-wrong (36).
- [x] **Statistical significance (batch 3)** — `src/stats_tests.py` (scipy). Chi-square + Fisher's
  exact + Cramér's V on the key cross-tabs:
  | Association | p-value | Cramér's V | significant |
  |---|---|---|---|
  | emotion × abuse-type | 2.8e-47 | 0.170 | ✅ |
  | polarity × abuse-type | 4.9e-14 | 0.132 | ✅ |
  | emotion × platform | 1.7e-31 | 0.256 | ✅ |
  | polarity × platform | 1.2e-01 | 0.043 | no |
  | polarity × language | 1.8e-05 | 0.077 | ✅ |
  - **Fisher's exact** victim-blaming × Neglect/Abandonment: **OR = 4.87, p = 3.9e-25** — VB ~5×
    more likely in neglect topics. Key findings now statistically validated; the one non-significant
    result (polarity × platform) is an honest nuance (platform shifts emotion, not coarse polarity).
- [x] **Language-wise confusion (batch 3)** — `figures/22_language_confusion.png`: SVM keeps a
  balanced diagonal on Bangla & Banglish; **BanglaBERT collapses on Banglish** (acc 0.46, never
  predicts Positive, scatters to Neutral) — the language finding made visual.
- Outputs: `results/phase5_deep_analysis.json`, `phase5_explain_errors.json`, `phase5_stats.json`
  (+ `_report.md` each), figures 18–22.
- **Done when:** analysis figures + written findings here. ✅ **Phase 5 batches 1–3 complete.**

### Phase 6 — Paper output  🔄 (assets assembled)
- [x] **Paper-ready asset document** — `src/build_paper_assets.py` → `docs/paper_assets.md`
  (auto-pulled from `results/*.json`). Contains: dataset table, model comparison (val+test) +
  McNemar, per-class tables, deep-analysis findings (language/embedding/religion/explainability/
  errors), full **figure index** (21 figures → paper section), and a key-findings/contributions list.
- [ ] Camera-ready formatting of chosen tables/figures into the manuscript (during writing).
- **Done when:** all paper assets in `figures/` + `results/` + `docs/paper_assets.md`. ✅ (assets
  assembled; final manuscript formatting happens during write-up.)

---

## 6. Update log
- **2026-06-28** — Created tracker. Dataset profiled (2454 rows). Folder structure & methodology
  decided. Encoding myth cleared (file is clean UTF-8). Awaiting decisions D1–D3 before Phase 0.
- **2026-06-28** — Decisions resolved: D1 = A+B both, D2 = Lamia + teammate, D3 = copy raw = yes.
  Annotation concept explained to Lamia. Still waiting on explicit "proceed" before Phase 0.
- **2026-06-28** — **Phase 0 DONE.** Built `sentiment/` structure, copied raw, wrote `src/clean.py`.
  Cleaned 2454 → 2301 (153 removed, audited). Outputs: `interim/cleaned.csv`, `interim/removed.csv`,
  `results/phase0_cleaning_report.md`. Next: Phase 1 (annotation guideline + sheet).
- **2026-06-28** — **Phase 1 setup DONE.** Added `comment_id` (C00001–C02301). Wrote
  `annotation_guideline.md`, `src/build_annotation.py`, `src/kappa.py`. Generated annotator_A/B.xlsx
  (450 overlap, stratified) + overlap_ids.csv. **Blocked on human labelling** before Phase 2.
- **2026-06-28** — **D4/D5 Hybrid labeling adopted + AI silver-labelling DONE.** Labelled all
  **2301** comments (polarity+emotion) via 16 batch files → `assemble_llm_labels.py` →
  `annotated/llm_labels.csv` (coverage verified, 0 missing). Silver dist: Neg 1619/Neu 512/Pos 170;
  emotion ANG 808/OTH 788/BLM 310/PRY 213/GRF 182. Reworked `build_annotation.py` to stratify the
  450 overlap by **emotion** and emit `overlap_ids.csv` as a hidden AI-label key; regenerated blind
  annotator_A/B.xlsx. **Next human step:** Lamia + teammate label the 450 blind → kappa.py.
- **2026-06-28** — **Phase 2 DONE (polarity target; emotion deferred per Lamia).** Wrote
  `src/dataset.py`: final text-dedup (2301 → 2299, 2 near-dups) → stratified 70/15/15 split by
  polarity (SEED=42) → `data/splits/{train,val,test}.csv` (1609/345/345, `emotion` column kept) →
  locked test set (`test_lock.json`, sha256) → `results/phase2_split.json` + `_report.md`.
  Polarity ratios consistent across splits. **Next:** Phase 3 modelling (sentiment baseline →
  BanglaBERT). Emotion to be activated later on the same splits if Lamia asks.
- **2026-06-28** — **Phase 3 Part 1 DONE (classical baseline).** `src/train.py`: TF-IDF
  word+char_wb (fit on train) → LogReg / Linear SVM / Complement NB, compared on val.
  **Best = Linear SVM, val macro-F1 0.653 / acc 0.762** (Neg F1 0.856, Neu 0.479, Pos 0.625).
  Saved `results/phase3_baseline.json`+`_report.md`, `figures/14_baseline_confusion.png`,
  `models/baseline_best.joblib`. Wrote `src/train_bert.py` (BanglaBERT, ready). **BanglaBERT
  run blocked:** torch fails to load on Python 3.14 (WinError 193) — needs a Py 3.11/3.12 env.
- **2026-06-29** — **Phase 3 Part 2 DONE (BanglaBERT).** Root-caused the torch failure to a
  **full C: drive** (not the 3.14 ABI); built a working **Python 3.12** venv (`.venv-bert`) with
  CPU torch + transformers 5.12 + accelerate, all caches/TMP redirected to **D:**. Ran
  `src/train_bert.py` (resumed from checkpoint-202 after a session teardown). **BanglaBERT val
  macro-F1 0.549 / acc 0.684 — below the Linear SVM baseline (0.653 / 0.762).** Honest finding:
  strong TF-IDF baseline beats an undertrained transformer on this small, imbalanced set. Saved
  `results/phase3_bert.json`+`_report.md`, `figures/15_bert_confusion.png`,
  `models/banglabert_polarity/`. Updated `progress_update.pptx` (16 slides, + comparison slide)
  and Downloads copy. **Next:** BanglaBERT tuning + XLM-R/mBERT comparison.
- **2026-06-29** — **Victim-blaming label audit (manual, first pass).** Built
  `src/audit_victimblame.py` → `data/annotated/review/victimblame_audit.xlsx` (all 310 VB comments,
  dropdowns). Read every one; kept the codebook rule (blaming the victim/parent/their
  past/upbringing/society = VB). Corrected **17** clear mislabels via `src/apply_vb_audit.py`
  (**emotion only**, polarity untouched → locked test set & polarity models unaffected):
  4 → Anger/Condemnation (condemn abuser/3rd party), 13 → Neutral-Other (generic advice/observation).
  Emotion dist now: ANG 812 / OTH 801 / **BLM 293** / PRY 213 / GRF 182. Splits patched by
  comment_id (train 13, val 2, test 2). Report: `results/victimblame_audit_applied.md`.
  **Note:** human inter-annotator (Kappa) validation still pending; EDA emotion charts use the
  pre-audit numbers (13.5% VB) and can be regenerated after the full human review.
- **2026-06-29** — **BanglaBERT tuning started (Phase 3 continuation).** Bumped `train_bert.py`
  to 5 epochs + warmup 0.1 + weight-decay 0.01 (class-weighted, best val-checkpoint). Cleared the
  stale 3-epoch checkpoints, preserved old result as `phase3_bert_3ep.json`. Running fresh on the
  D: venv in background (505 steps ≈ 1h40m CPU). **Human Kappa track runs in parallel** (teammate
  time; not blocking this). Slides will be regenerated later on Lamia's go-ahead. **Next after
  tuning:** XLM-R/mBERT comparison, then Phase 4 evaluation on the locked test set.
- **2026-06-29** — **BanglaBERT tuning DONE.** 5 epochs finished; best val checkpoint = epoch 1.
  **Tuned val macro-F1 0.579 / acc 0.713** (up from 3-epoch 0.549). Per-epoch: 0.579/0.467/0.573/
  0.567/0.543. **Baseline Linear SVM (0.653) still leads** — a genuine, publishable finding that a
  strong classical baseline beats a fine-tuned transformer on this small (1,609-train), imbalanced
  set. Updated `results/phase3_bert.json`+`_report.md`, `figures/15_bert_confusion.png`. **Next:**
  optional XLM-R/mBERT, then Phase 4 (locked-test evaluation) once models are frozen.
- **2026-06-29** — **Phase 4 DONE (final test-set evaluation).** Wrote `src/evaluate.py`; verified
  the locked test set by sha256, then evaluated both frozen models once. **Test macro-F1: Linear
  SVM 0.672 · BanglaBERT (tuned) 0.611.** Both generalise well (test ≥ val). **McNemar p = 0.133 →
  the gap is NOT statistically significant** — the models are comparable on held-out data, SVM
  numerically ahead. Caught & fixed a tokenizer-not-saved bug (`train_bert.py` now saves the
  tokenizer; first eval wrongly gave all-Neutral 0.12 before the fix). Outputs:
  `results/phase4_test_eval.json`+`_report.md`, `figures/16_/17_test_confusion_*.png`. **Next:**
  Phase 5 deep analysis (emotion×topic, victim-blaming/religious framing, BERTopic/clustering).
- **2026-06-29** — **Phase 5 batch 1 DONE (deep analysis).** `src/deep_analysis.py` (sklearn only,
  no new installs). (1) **Language robustness:** BanglaBERT drops to **0.46** acc on Latin-script
  Banglish vs SVM **0.71** — the script gap ≈ why the classical baseline wins overall. (2)
  **Embedding structure:** KMeans↔label ARI only 0.05 (emotion) / 0.06 (polarity) — classes overlap
  in embedding space; t-SNE shows a detached Latin-script blob. (3) **Religious framing:** 22.1% of
  comments are religious; religion carries both prayer (34%) and blame/anger (~47%). Outputs:
  `results/phase5_deep_analysis.json`+`_report.md`, `figures/18–21`. **Next (batch 2):** linear-SVM
  coefficient explainability (top words per class) + error analysis. Emotion labels here are the
  current LLM labels (VB audit / Kappa still pending) — splits will refresh once labels finalise.
- **2026-07-07** — **Phase 5 batch 2 DONE (explainability + error analysis).** `src/explain_errors.py`.
  (A) SVM word-coefficients give a transparent word→sentiment map (Negative=pain/blame,
  Neutral=advice/conditional, Positive=dua/gratitude incl. English `thank`/Arabic `الله`).
  (B) On test, the dominant error for both models is **Neutral↔Negative** (the fuzzy middle);
  **BanglaBERT error rate is 0.51 on Latin/code-mixed and 0.43 on emoji comments** (vs ~0.23–0.25
  otherwise) — reinforcing why the char-ngram SVM wins. Outputs `results/phase5_explain_errors.json`
  +`_report.md`. **Phase 5 (batches 1+2) complete.** Remaining: (optional) XLM-R/mBERT; human track
  (VB-audit apply, Kappa); Phase 6 paper assets. No commit/push; slides on Lamia's go-ahead.
- **2026-07-07** — **Phase 6 assets assembled.** `src/build_paper_assets.py` reads all
  `results/*.json` and emits **`docs/paper_assets.md`** — one paper-ready document: dataset table,
  model comparison (val+test) + McNemar, per-class tables, all deep-analysis findings, a 21-figure
  index mapped to paper sections, and the contributions/talking-points list. Regenerate after any
  experiment to keep tables in sync. **Modelling+analysis pipeline (Phase 0–6) now end-to-end
  complete.** Remaining is the human track (VB-audit apply + Kappa) and the manuscript write-up
  (optional XLM-R/mBERT). No commit/push; slides on Lamia's go-ahead.
- **2026-07-07** — **Full presentation deck built (21 slides) + Bengali tokenizer bug fixed.**
  Built `src/build_slides.py` → `sentiment/results/progress_update.pptx` (Phase 0→6: dataset,
  language, label scheme+method, EDA findings, split, models+why, val+test results, deep analysis,
  contributions; numbers auto-pulled from JSON; saved to `C:\Users\ACER\Downloads`). While checking
  the explainability slide, Lamia spotted the top Bangla words looked shredded (কষ্ট→কষ, মনে হয়→মন
  হয়). **Root cause:** the word TF-IDF used the default `token_pattern \b\w\w+\b`, which treats
  Bengali vowel-signs/virama as boundaries. **Fix:** `token_pattern=[A-Za-z]+|[ঀ-৿]+` in
  `train.py`. **Cascade re-run** (train → evaluate → deep_analysis → explain_errors → paper_assets
  → slides): baseline **improved** — val macro-F1 0.653→**0.661**, **test 0.672→0.683 / acc 0.788**;
  **McNemar now p=0.026 → the SVM SIGNIFICANTLY beats BanglaBERT** (was p=0.133 n.s.). Explainability
  words are now clean full Bangla. All result JSONs, figures 14/16, and the deck refreshed. Baseline
  retrained under sklearn 1.9 (venv-bert) so no version-mismatch warnings. No commit/push.
- **2026-07-07** — **Phase 5 batch 3 DONE (statistical tests + language confusion).**
  `src/stats_tests.py` (scipy). Chi-square + Fisher's exact + Cramér's V validate the key findings:
  emotion×topic (p=2.8e-47), emotion×platform (p=1.7e-31, V=0.26), polarity×language (p=1.8e-5), and
  **Fisher's victim-blaming×Neglect OR=4.87, p=3.9e-25**. polarity×platform is n.s. (p=0.12) — a fair
  nuance. Added `figures/22_language_confusion.png` (2 models × Bangla/Banglish) showing BanglaBERT
  collapsing on Banglish. Regenerated `docs/paper_assets.md` (now 3f stats section + fig 22) and the
  **deck → 23 slides** (added Statistical Validation + Language Confusion slides). Deck saved to
  Downloads as `progress_update_v2.pptx` (original was open in PowerPoint). Decided the stats/
  confusion additions do NOT need to wait for human Kappa — reproducible, re-run after label
  finalisation. No commit/push.
- **2026-07-07** — **Human-track prep (VB-audit apply verified + guideline edge-cases added).**
  Confirmed the victim-blaming audit was already applied (`apply_vb_audit.py`, changelog
  `results/victimblame_audit_applied.md`): **17 emotion-only fixes** (4→Anger, 13→Neutral-Other),
  polarity untouched → **Victim-blaming 310→293, Anger 808→812, Neutral-Other 788→801**; splits
  updated (train 13/val 2/test 2). Synced `review/victimblame_audit.csv` to match. Added a new
  **"Victim-blaming vs Anger vs Neutral-Other"** edge-case section to `annotation_guideline.md`
  (with the audit's worked examples) so the two human annotators label the tricky boundary
  consistently → **Kappa is now prep-ready.** NOTE: Phase-5 batch 1–3 stats already read the
  corrected labels (293 VB); the older **EDA figures/`eda_stats.json` still use pre-audit 310 VB
  (13.5%)** — to be regenerated together after the full human Kappa review (not worth doing twice).
  **Next (human track, teammate time):** Lamia + teammate label the 450-blind sheet → `kappa.py`.
  No commit/push.
- **2026-07-07** — **Kappa setup verified & proven ready (human step only remains).** Checked the
  infrastructure end-to-end: `data/annotated/annotator_A.xlsx` (1375 rows, "Annotate" sheet) and
  `annotator_B.xlsx` (1376) — both **blind** (0 pre-filled, dropdowns for polarity/emotion), sharing
  exactly **450 overlap** comment_ids. `src/kappa.py` reads the "Annotate" sheet, merges on
  comment_id, and reports Cohen's Kappa + % agreement + confusion for polarity & emotion (verdict
  ≥0.70). Ran a **non-destructive simulation** on the real 450 overlap (AI labels + injected
  disagreement) → the machinery runs and emits sensible output (sim polarity κ≈0.86, emotion κ≈0.80).
  **Everything is ready; the only missing piece is the two humans labelling.** To do it: open
  `annotator_A.xlsx` (Lamia) & `annotator_B.xlsx` (teammate), fill the `polarity`+`emotion` dropdowns
  on the "Annotate" sheet **independently**, save, then run `python sentiment/src/kappa.py` →
  `results/kappa.json`. No commit/push.
- **2026-07-07** — **Switched to Option 3: FOUR-annotator full human labelling (team has 4 members).**
  Built `src/build_kappa4.py` → `annotator_{A,B,C,D}.xlsx`, each ~913 rows = **450 shared overlap +
  ~463 unique** (emotion-stratified `StratifiedKFold`). Coverage: every one of the 2,301 comments
  gets ≥1 human label; the 450 overlap gets 4 → a **fully human-annotated dataset** (big upgrade from
  LLM silver labels). Wrote `src/kappa4.py`: **Fleiss' Kappa** (4 raters) on the overlap for polarity
  & emotion, plus assembles gold `human_labels.csv` (overlap = majority vote, ties → AI tiebreak;
  unique = that annotator's label). Cohen's `kappa.py` kept for reference. Verified end-to-end with a
  non-destructive simulation (sim Fleiss κ: polarity 0.75, emotion 0.73). Updated
  `annotation_guideline.md` (4 annotators + how-to). **Human step (team time):** all 4 fill the
  "Annotate" sheet independently → `python sentiment/src/kappa4.py` → `results/kappa.json` +
  `human_labels.csv`. Then models/EDA can be re-run on the human gold labels. No commit/push.
- **2026-07-07** — **EDA refreshed on corrected labels + paper sections added (Human track deferred).**
  Re-ran `eda.py` on the post-audit labels (VB 310→**293**), refreshing `eda_stats.json` + figures
  01–13. Added: `paper_extras.py` → **`figures/23_per_class_metrics.png`** (per-class P/R/F1, both
  models); **error-examples** table (hardest both-wrong cases) into `paper_assets.md` + a deck slide;
  and written **Limitations** and **Ethics** sections in `paper_assets.md` (now §6/§7) + deck slides.
  Regenerated `docs/paper_assets.md` (152 lines) and the **deck → 27 slides** (+ per-class, error
  examples, Limitations, Ethics). Downloads copy refreshed. Human annotation/Kappa is **deferred**
  (sir hasn't raised it; it blocks nothing) — the light validation can be done later. No commit/push.
