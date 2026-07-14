# Phase 1.5 — EDA Findings (AI silver labels, n = 2301)

> Descriptive analysis of the silver-labelled corpus. Charts in `sentiment/figures/`,
> raw numbers in `sentiment/results/eda_stats.json`. These are the candidate
> "key findings" for the paper (to be confirmed once human-validated labels land).

## Headline numbers
- **70.4% of all comments are Negative** (1619), 22.3% Neutral (512), 7.4% Positive (170).
  → Public reaction to elder-abuse content is overwhelmingly negative/condemnatory.
- **Emotion mix:** Anger/Condemnation 808 (35.1%) · Neutral-Other 788 (34.2%) ·
  **Victim-blaming 310 (13.5%)** · Prayer/Religious 213 (9.3%) · Grief/Sympathy 182 (7.9%).
- Polarity↔emotion is consistent: every Anger/Victim-blaming/Grief comment is Negative;
  Positive comments are only Prayer (blessings) or Neutral-Other (appreciation/thanks).

## Key finding 1 — Victim-blaming is topic-dependent (not uniform)
Victim-blaming concentrates where the elder was **neglected / abandoned**, and almost
vanishes where the elder was **physically attacked or murdered**:

| Abuse topic | % Victim-blaming |
|---|---|
| Neglect | **25.7%** |
| Abandonment | 12.1% |
| Verbal Abuse | 11.1% |
| Physical Abuse | 2.2% |
| Murder | **0.0%** |

→ When elders are abandoned (e.g. educated/wealthy parents in old-age homes), a sizeable
minority blames the *victim* ("didn't give religious upbringing", "haram money", their own
fault). When the harm is undeniable violence, the public closes ranks in condemnation.
*(chart 10)*

## Key finding 2 — Direct-violence topics provoke the most condemnation
Anger/Condemnation share by topic: **Verbal 52.5% · Physical 46.2% · Murder 41.4%** vs
Neglect 29.6% · Abandonment 24.2%. Prayer/Religious peaks for **Murder (15.4%)** — death
draws dua. *(charts 04, 05)*

## Key finding 3 — Strong platform effect
Victim-blaming is almost entirely a **YouTube** phenomenon: **18.6% on YouTube vs 0.9% on
Facebook**. Facebook skews more Neutral-Other (46.9% vs 29.0%). Platform is a real
confound/feature worth modelling and caveating. *(chart 06)*

## Key finding 4 — Language effect
Bengali-script comments are more negative (**72.6% Neg**) than Banglish/Latin (60.8%) and
code-mixed bn+en (51.5%). Banglish/code-mix carries relatively more Neutral content.
*(chart 07)*

## Key finding 5 — Grief gets the engagement
Mean likes by emotion: **Grief/Sympathy 4.45** ≫ Neutral-Other 0.68 > Anger 0.44 ≈ Prayer
0.44 > Victim-blaming 0.35. Sympathetic comments resonate far more than angry ones.
*(chart 09)*

## Key finding 6 — Victim-blaming comments are the longest
Median comment length (chars): **Victim-blaming 84** > Anger 54 > Prayer 47 > Neutral 42 >
Grief 40. Blamers argue/justify at length; grief is short and raw. *(chart 08)*

## Key finding 7 — Clean lexical separation (validates the 5-emotion scheme)
Distinctive tokens per emotion are sharply different *(chart 12, 13)*:
- **Anger:** বিচার (justice), কুলাঙ্গার (wretch), আইনের (law), উচিত (should), ফাঁসি (hanging)
- **Victim-blaming:** শিক্ষা / শিক্ষিত (education/educated), বৃদ্ধাশ্রমে (old-age home), টাকা (money)
- **Grief:** কষ্ট (pain), দুঃখ (sorrow), নেই (gone/no more)

## Caveats
- `Date` = scrape time, not post time → no temporal analysis.
- `abuse_type` is **video-level** context, not a per-comment label → use only for cross-tabs.
- Numbers are on **AI silver labels**; final figures pending human-validated 450-set (κ check).
- Murder appears only on Facebook; the "Positive 21.9% for Murder" reflects appreciation/dua
  comments on those threads, not approval — interpret with care.

## Figures index (`sentiment/figures/`)
`01` polarity · `02` emotion · `03` polarity×emotion · `04` topic×emotion ·
`05` topic×polarity · `06` platform×emotion · `07` language×polarity · `08` length×emotion ·
`09` likes×emotion · `10` victim-blaming by topic · `11` prayer by topic ·
`12` top tokens · `13` word clouds
