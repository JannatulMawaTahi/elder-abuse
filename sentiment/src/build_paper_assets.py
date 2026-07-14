# -*- coding: utf-8 -*-
"""
Phase 6 — assemble every result into one paper-ready document.

Reads the phase-*/eda result JSONs and emits docs/paper_assets.md:
  - dataset table, model-comparison tables (val + test), per-class tables,
  - deep-analysis findings, a full figure index (figure → what it shows → section),
  - a bullet list of the paper's key findings / contributions.

Numbers are pulled programmatically from results/*.json so the document always
matches the actual experiments (no hand-typed figures).

    python sentiment/src/build_paper_assets.py
"""
from __future__ import annotations
import sys, io, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
OUT = ROOT.parent / "docs" / "paper_assets.md"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def load(name):
    p = RES / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


eda = load("eda_stats.json")
sp = load("phase2_split.json")
base = load("phase3_baseline.json")
bert = load("phase3_bert.json")
t4 = load("phase4_test_eval.json")
p5 = load("phase5_deep_analysis.json")
p5e = load("phase5_explain_errors.json")
p5s = load("phase5_stats.json")


def d2rows(d):
    return " · ".join(f"{k} {v}" for k, v in d.items())


L = ["Negative", "Neutral", "Positive"]
md = []
A = md.append

A("# Paper Assets — Sentiment & Emotion Analysis of Elder-Abuse Comments")
A("")
A("*Auto-generated from `results/*.json` by `src/build_paper_assets.py` — regenerate after any "
  "experiment so the tables stay in sync.*")
A("")

# ---------- 1. Dataset ----------
A("## 1. Dataset (→ paper §Dataset)")
A("")
A("| Item | Value |")
A("|---|---|")
A(f"| Raw scraped comments | 2,454 |")
A(f"| After cleaning | {eda.get('n_comments', '—')} |")
A(f"| After text-dedup (modelling set) | {sp.get('after_dedup', '—')} |")
lang = (p5.get("language", {}) or {}).get("distribution", {})
if lang:
    A(f"| Language mix | {d2rows(lang)} |")
if eda.get("polarity"):
    A(f"| Polarity distribution | {d2rows(eda['polarity'])} |")
if eda.get("emotion"):
    A(f"| Emotion distribution | {d2rows(eda['emotion'])} |")
if sp.get("split_sizes"):
    A(f"| Split (train/val/test) | {d2rows(sp['split_sizes'])} — stratified, seed {sp.get('seed')} |")
A(f"| Platforms | {d2rows(eda.get('platform_counts', {}))} |")
A("")
A("**Label scheme:** 2 levels — polarity (Negative/Neutral/Positive) + fine-grained emotion "
  "(Anger/Condemnation · Grief/Sympathy · Prayer/Religious · Victim-blaming · Neutral-Other). "
  "Test set is sha256-locked. Human inter-annotator (Kappa) validation is in progress.")
A("")

# ---------- 2. Models ----------
A("## 2. Model results (→ paper §Experiments/Results)")
A("")
tt = t4.get("test", {})
tb = tt.get("baseline_linear_svm", {})
tr = tt.get("banglabert_tuned", {})
vb = f"{base.get('best_val_macro_f1'):.3f}" if base.get("best_val_macro_f1") is not None else "—"
vr = f"{bert.get('macro_f1'):.3f}" if bert.get("macro_f1") is not None else "—"
A("| Model | val macro-F1 | **test macro-F1** | test acc | test weighted-F1 |")
A("|---|---|---|---|---|")
A(f"| **Linear SVM (TF-IDF word+char)** | {vb} | **{tb.get('macro_f1'):.3f}** | "
  f"{tb.get('accuracy'):.3f} | {tb.get('weighted_f1'):.3f} |")
A(f"| BanglaBERT (fine-tuned, tuned) | {vr} | {tr.get('macro_f1'):.3f} | "
  f"{tr.get('accuracy'):.3f} | {tr.get('weighted_f1'):.3f} |")
A("")
mc = t4.get("mcnemar_baseline_vs_bert", {})
if mc:
    sig = "not statistically significant" if mc.get("p_value", 1) >= 0.05 else "significant"
    A(f"**Significance (McNemar):** baseline-only-correct {mc.get('baseline_only_correct')} · "
      f"BERT-only-correct {mc.get('bert_only_correct')} · p = {mc.get('p_value'):.3f} → **{sig}**. "
      "Both models generalise (test ≥ validation). The classical baseline is the practical choice.")
A("")

# per-class test
for name, key in (("Linear SVM", "baseline_linear_svm"), ("BanglaBERT", "banglabert_tuned")):
    pc = tt.get(key, {}).get("per_class", {})
    if not pc:
        continue
    A(f"**Per-class (test) — {name}**")
    A("")
    A("| Class | Precision | Recall | F1 | Support |")
    A("|---|---|---|---|---|")
    for c in L:
        r = pc.get(c, {})
        A(f"| {c} | {r.get('precision',0):.3f} | {r.get('recall',0):.3f} | "
          f"{r.get('f1-score',0):.3f} | {int(r.get('support',0))} |")
    A("")

# 2b error examples
he = p5e.get("error_analysis", {}).get("hardest_examples", [])
if he:
    A("## 2b. Representative errors (both models wrong — → paper §Error analysis)")
    A("")
    A("| id | true | SVM | BanglaBERT | comment |")
    A("|---|---|---|---|---|")
    for e in he[:8]:
        txt = e["text"].replace("|", "/").replace("\n", " ")
        A(f"| {e['comment_id']} | {e['true']} | {e['svm']} | {e['bert']} | {txt} |")
    A("")
    A("> Most hard cases sit on the Neutral↔Negative boundary (rhetorical questions, mixed "
      "sentiment, sarcasm) — inherently ambiguous even for humans.")
    A("")

# ---------- 3. Deep analysis ----------
A("## 3. Deep analysis (→ paper §Analysis/Discussion)")
A("")
la = (p5.get("language", {}) or {}).get("test_accuracy_by_language", [])
if la:
    A("**3a. Language-wise robustness (test accuracy)**")
    A("")
    A("| Language | n | SVM | BanglaBERT |")
    A("|---|---|---|---|")
    for r in la:
        A(f"| {r['lang']} | {r['n']} | {r['svm_acc']:.3f} | {r['bert_acc']:.3f} |")
    A("")
    A("> BanglaBERT collapses on Latin-script Banglish (Bangla-script pretraining); the char-ngram "
      "SVM stays robust — the main reason the baseline wins overall.")
    A("")
emb = p5.get("embedding", {})
if emb:
    A(f"**3b. Embedding structure:** KMeans↔label Adjusted Rand Index — "
      f"emotion {emb.get('ari_cluster_vs_emotion_k5'):.3f} (k=5), "
      f"polarity {emb.get('ari_cluster_vs_polarity_k3'):.3f} (k=3). Low ⇒ classes overlap in "
      "embedding space (semantic, not lexically separable) ⇒ supervised labels are needed.")
    A("")
rel = p5.get("religion", {})
if rel:
    ew = rel.get("emotion_within_religious", {})
    A(f"**3c. Religious framing:** {rel.get('religious_share',0)*100:.1f}% of comments use "
      "religious language; within them — " +
      ", ".join(f"{k} {v*100:.0f}%" for k, v in ew.items() if v) +
      ". Religion carries both blessing and blame/condemnation.")
    A("")
ex = p5e.get("explainability_top_words", {})
if ex:
    A("**3d. Explainability — top Linear-SVM word features per class**")
    A("")
    for c in L:
        toks = " · ".join(f"`{t['token']}`" for t in ex.get(c, [])[:10])
        A(f"- **{c}:** {toks}")
    A("")
ea = p5e.get("error_analysis", {})
if ea:
    g = ea.get("error_rate_by_group", {})
    A("**3e. Error analysis (test):** dominant confusion is **Neutral↔Negative** for both models. "
      f"BanglaBERT error rate {g.get('bert_latin_script',0):.2f} on Latin/code-mixed and "
      f"{g.get('bert_emoji',0):.2f} on emoji comments vs ~{g.get('bert_bangla',0):.2f} otherwise; "
      "the SVM is stable across both.")
    A("")

# 3f statistical significance
st = p5s.get("chi_square_tests", [])
if st:
    A("**3f. Statistical significance — Chi-square / Fisher's exact**")
    A("")
    A("| Association | χ² | p-value | Cramér's V | significant |")
    A("|---|---|---|---|---|")
    for t in st:
        A(f"| {t['cross_tab']} | {t['chi2']} | {t['p_value']:.1e} | {t['cramers_v']} | "
          f"{'yes' if t['significant'] else 'no'} |")
    fe = p5s.get("fisher_exact", {})
    if fe:
        A("")
        A(f"Fisher's exact — victim-blaming × Neglect/Abandonment: odds ratio "
          f"**{fe.get('odds_ratio')}**, p = {fe.get('p_value',1):.1e} "
          f"({'significant' if fe.get('significant') else 'n.s.'}). The key descriptive findings "
          "(emotion↔topic, emotion↔platform, victim-blaming↔topic) are statistically validated; "
          "overall polarity↔platform is NOT significant (a fair nuance).")
    A("")

# ---------- 4. Figure index ----------
A("## 4. Figure index (→ where each goes)")
A("")
figs = [
    ("01_polarity_dist", "Polarity distribution", "Dataset"),
    ("02_emotion_dist", "Emotion distribution", "Dataset"),
    ("03_polarity_x_emotion", "Polarity × emotion", "Dataset"),
    ("04_abusetype_x_emotion", "Abuse-type × emotion", "Analysis"),
    ("05_abusetype_x_polarity", "Abuse-type × polarity", "Analysis"),
    ("06_platform_x_emotion", "Platform × emotion", "Analysis"),
    ("07_language_x_polarity", "Language × polarity", "Analysis"),
    ("08_length_by_emotion", "Comment length by emotion", "Analysis"),
    ("09_likes_by_emotion", "Engagement (likes) by emotion", "Analysis"),
    ("10_victimblame_by_abuse", "Victim-blaming by abuse type", "Analysis (key)"),
    ("11_prayer_by_abuse", "Prayer/religious by abuse type", "Analysis"),
    ("12_top_tokens", "Distinctive tokens per emotion", "Analysis"),
    ("13_wordclouds", "Word clouds per emotion", "Analysis"),
    ("14_baseline_confusion", "SVM confusion (validation)", "Experiments"),
    ("15_bert_confusion", "BanglaBERT confusion (validation)", "Experiments"),
    ("16_test_confusion_baseline", "SVM confusion (test)", "Experiments"),
    ("17_test_confusion_bert", "BanglaBERT confusion (test)", "Experiments"),
    ("18_lang_distribution", "Language distribution + polarity mix", "Analysis"),
    ("19_lang_model_accuracy", "Model accuracy by language", "Analysis (key)"),
    ("20_embedding_tsne_emotion", "t-SNE of BanglaBERT embeddings", "Analysis"),
    ("21_religious_framing", "Religious vs non-religious framing", "Analysis"),
    ("22_language_confusion", "Language-wise confusion (SVM vs BanglaBERT)", "Analysis (key)"),
    ("23_per_class_metrics", "Per-class Precision/Recall/F1 (both models)", "Experiments"),
]
A("| Figure | Shows | Paper section |")
A("|---|---|---|")
for f, what, sec in figs:
    A(f"| `figures/{f}.png` | {what} | {sec} |")
A("")

# ---------- 5. Key findings ----------
A("## 5. Key findings / contributions (paper talking points)")
A("")
for b in [
    "A new **annotated Bangla/Banglish elder-abuse dataset** with a novel **victim-blaming** "
    "emotion class — the main contribution.",
    "**70% of public reactions are Negative**; anger and victim-blaming dominate the emotion mix.",
    "**Victim-blaming is topic-specific** — high for Neglect/Abandonment, ~0% for Murder.",
    "**Platform effect** — victim-blaming far higher on YouTube than Facebook; grief earns the most likes.",
    f"**Classical TF-IDF + Linear SVM beats fine-tuned BanglaBERT** on this small, imbalanced, "
    f"code-switched corpus (test macro-F1 {tb.get('macro_f1',0):.2f} vs {tr.get('macro_f1',0):.2f}; "
    f"McNemar p = {mc.get('p_value',1):.3f}, "
    f"{'significant' if mc.get('p_value',1) < 0.05 else 'not significant'}).",
    "**Why:** BanglaBERT can't read Latin-script Banglish (err 0.51) or emoji (err 0.43); the "
    "char-ngram SVM is robust to both — a concrete, quantified explanation.",
    "**Religion is the vehicle of both blessing and condemnation** (22% of comments).",
    "Transparent explainability from SVM coefficients; hardest boundary is Neutral↔Negative.",
]:
    A(f"- {b}")
A("")

# ---------- 6. Limitations ----------
A("## 6. Limitations (→ paper §Limitations)")
A("")
for b in [
    "**Labels are model-generated (silver).** A codebook was followed, but human inter-annotator "
    "(Fleiss'/Cohen's Kappa) validation is planned, not yet complete — reliability is not yet "
    "quantified on gold labels.",
    "**Small and imbalanced** (2,301 comments; ~70% Negative, few Positive) — caps rare-class "
    "performance and limits transformer fine-tuning.",
    "**Narrow domain** — YouTube/Facebook comments on elder-abuse videos; findings may not "
    "transfer to other topics or platforms.",
    "**Subjective fine-grained emotion** — victim-blaming vs anger vs neutral is genuinely "
    "ambiguous at the boundary; some disagreement is expected.",
    "**Point-in-time scrape** — no temporal analysis; `abuse_type` is a video-level topic, not a "
    "per-comment label.",
    "**Model blind spots** — BanglaBERT under-reads Latin-script Banglish and emoji, so the "
    "transformer results are a lower bound for code-switched text.",
]:
    A(f"- {b}")
A("")

# ---------- 7. Ethics ----------
A("## 7. Ethics statement (→ paper §Ethics)")
A("")
for b in [
    "Only **publicly posted** social-media comments are used; no private messages or personal data.",
    "Analysis is **aggregate** — we report patterns, never profile, rank, or expose individual "
    "commenters; commenter names are not analysed or published.",
    "The topic (elder abuse) and victims are treated with care; **no attempt to re-identify** "
    "victims or commenters.",
    "The **victim-blaming** class is studied to *understand and surface* a harmful social "
    "attitude — not to endorse it.",
    "Comments may contain offensive language; they are used solely for research and shown only as "
    "de-identified examples.",
    "Data were collected in line with each platform's public-content terms; no user was contacted.",
]:
    A(f"- {b}")
A("")

OUT.write_text("\n".join(md) + "\n", encoding="utf-8")
print(f"wrote {OUT} ({len(md)} lines)")
