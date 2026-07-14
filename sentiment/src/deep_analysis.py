# -*- coding: utf-8 -*-
"""
Phase 5 (batch 1) — Deep analysis for the paper.

Three analyses that go beyond the descriptive EDA:

  (1) Language-wise model robustness  — does the classifier hold up on Banglish/
      Latin and code-mixed comments, not just pure Bangla?  (held-out test set)
  (2) Embedding structure             — do BanglaBERT sentence embeddings cluster
      into the human emotion/polarity classes on their own?  (KMeans + ARI + t-SNE)
  (3) Religious-framing prevalence    — how religious language distributes across
      polarity and emotion (religion as the *language* of both blessing and curse).

Run with the D: venv (needs torch + transformers + sklearn):
    .venv-bert\\Scripts\\python.exe sentiment/src/deep_analysis.py

Outputs: results/phase5_deep_analysis.json + _report.md
         figures/18_lang_distribution.png
         figures/19_lang_model_accuracy.png
         figures/20_embedding_tsne_emotion.png
         figures/21_religious_framing.png
"""
from __future__ import annotations
import os, sys, io, json
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\pysetup\hf_cache")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
ANN = ROOT / "data" / "annotated" / "llm_labels.csv"
RES = ROOT / "results"
FIG = ROOT / "figures"
MODELS = ROOT / "models"

LABELS = ["Negative", "Neutral", "Positive"]
L2I = {l: i for i, l in enumerate(LABELS)}
EMOS = ["Anger/Condemnation", "Grief/Sympathy", "Prayer/Religious",
        "Victim-blaming", "Neutral-Other"]

import joblib
from sklearn.metrics import accuracy_score, f1_score, adjusted_rand_score
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
NAVY, RED, GREEN, GREY = "#1D3557", "#E63946", "#2A9D8F", "#6C757D"
EMO_COLORS = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#ADB5BD"]

# ---- religious markers (Bangla + Banglish) ----
RELIG = ["আল্লাহ", "আল্লা", "ইসলাম", "কোরআন", "কুরআন", "হাদিস", "হাদীস", "দ্বীন", "দীন",
         "দ্বীনি", "দ্বীনী", "নামাজ", "নামায", "জান্নাত", "জাহান্নাম", "আমিন", "আমীন",
         "ইনশাআল্লাহ", "ইনশাল্লাহ", "রাসূল", "রাসুল", "দোয়া", "দুআ", "গুনাহ", "পাপ", "হারাম",
         "হালাল", "যাকাত", "কেয়ামত", "কিয়ামত", "আখেরাত", "আখিরাত", "মাদ্রাসা", "ধর্ম",
         "allah", "islam", "quran", "koran", "hadis", "deen", "din", "dua", "namaz",
         "jannat", "jahannam", "amin", "insha", "haram", "halal", "zakat"]


def is_religious(text: str) -> bool:
    t = str(text).lower()
    return any(m.lower() in t for m in RELIG)


# ======================= embeddings =======================
def bert_embeddings(texts, batch=32):
    import torch
    from transformers import AutoTokenizer, AutoModel
    mdl = str(MODELS / "banglabert_polarity")
    tok = AutoTokenizer.from_pretrained(mdl)
    model = AutoModel.from_pretrained(mdl)         # encoder only, for embeddings
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], truncation=True, padding=True,
                      max_length=128, return_tensors="pt")
            hs = model(**enc).last_hidden_state              # (B, T, H)
            mask = enc["attention_mask"].unsqueeze(-1).float()
            emb = (hs * mask).sum(1) / mask.sum(1).clamp(min=1e-9)   # mean-pool
            out.append(emb.cpu().numpy())
            print(f"  embed {min(i+batch,len(texts))}/{len(texts)}", end="\r")
    print()
    return np.vstack(out)


def predict_baseline(texts):
    pipe = joblib.load(MODELS / "baseline_best.joblib")
    raw = pipe.predict(texts)
    if raw.dtype.kind in "US":
        return np.array([L2I[str(v)] for v in raw])
    return raw.astype(int)


def predict_bert(texts, batch=32):
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    mdl = str(MODELS / "banglabert_polarity")
    tok = AutoTokenizer.from_pretrained(mdl)
    model = AutoModelForSequenceClassification.from_pretrained(mdl).eval()
    pr = []
    with torch.no_grad():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], truncation=True, padding=True,
                      max_length=128, return_tensors="pt")
            pr.extend(torch.argmax(model(**enc).logits, 1).tolist())
    return np.array(pr)


# ======================= (1) language-wise =======================
def lang_analysis(full, test):
    # normalise lang buckets
    def bucket(l):
        l = str(l).lower()
        if l.startswith("beng"): return "Bangla"
        if l in ("latin", "banglish"): return "Banglish (Latin)"
        if "bn+en" in l or "mix" in l: return "Code-mixed"
        if "arab" in l: return "Arabic"
        return "Other"
    full = full.copy(); full["lb"] = full["lang"].map(bucket)
    test = test.copy(); test["lb"] = test["lang"].map(bucket)

    dist = full["lb"].value_counts()
    # polarity share per language
    pol_by_lang = (full.groupby("lb")["polarity"].value_counts(normalize=True)
                   .unstack().reindex(columns=LABELS).fillna(0))

    # model accuracy per language on the TEST set
    Xt = test["Comment"].tolist(); yt = np.array([L2I[v] for v in test["polarity"]])
    pb = predict_baseline(Xt); pr = predict_bert(Xt)
    rows = []
    for lb in ["Bangla", "Banglish (Latin)", "Code-mixed"]:
        m = test["lb"] == lb
        n = int(m.sum())
        if n == 0:
            continue
        rows.append({"lang": lb, "n": n,
                     "svm_acc": float(accuracy_score(yt[m.values], pb[m.values])),
                     "bert_acc": float(accuracy_score(yt[m.values], pr[m.values]))})
    lang_acc = pd.DataFrame(rows)

    # ---- chart 18: distribution + polarity mix ----
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
    dist.plot.bar(ax=ax[0], color=NAVY)
    ax[0].set_title("Comments by language", fontweight="bold")
    ax[0].set_ylabel("count"); ax[0].tick_params(axis="x", rotation=20)
    pol_by_lang.plot.bar(stacked=True, ax=ax[1],
                         color=[RED, GREY, GREEN])
    ax[1].set_title("Polarity mix within each language", fontweight="bold")
    ax[1].set_ylabel("share"); ax[1].tick_params(axis="x", rotation=20)
    ax[1].legend(title="", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "18_lang_distribution.png", dpi=140, facecolor="white")
    plt.close(fig)

    # ---- chart 19: per-language model accuracy ----
    fig, ax = plt.subplots(figsize=(7, 4.4))
    x = np.arange(len(lang_acc)); w = 0.38
    ax.bar(x - w/2, lang_acc["svm_acc"], w, label="Linear SVM", color=NAVY)
    ax.bar(x + w/2, lang_acc["bert_acc"], w, label="BanglaBERT", color=RED)
    ax.set_xticks(x); ax.set_xticklabels([f"{r.lang}\n(n={r.n})" for r in lang_acc.itertuples()])
    ax.set_ylabel("test accuracy"); ax.set_ylim(0, 1)
    ax.set_title("Model accuracy by language (held-out test)", fontweight="bold")
    ax.legend()
    for i, r in enumerate(lang_acc.itertuples()):
        ax.text(i - w/2, r.svm_acc + .02, f"{r.svm_acc:.2f}", ha="center", fontsize=9)
        ax.text(i + w/2, r.bert_acc + .02, f"{r.bert_acc:.2f}", ha="center", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "19_lang_model_accuracy.png", dpi=140, facecolor="white")
    plt.close(fig)
    return {"distribution": dist.to_dict(),
            "polarity_by_language": pol_by_lang.round(3).to_dict(orient="index"),
            "test_accuracy_by_language": lang_acc.round(3).to_dict(orient="records")}


# ======================= (2) embedding structure =======================
def embedding_analysis(full):
    texts = full["Comment"].tolist()
    emb = bert_embeddings(texts)

    emo = full["emotion"].values
    pol = full["polarity"].values
    emo_idx = np.array([EMOS.index(e) if e in EMOS else -1 for e in emo])
    pol_idx = np.array([L2I[p] for p in pol])

    km5 = KMeans(n_clusters=5, n_init=10, random_state=42).fit_predict(emb)
    km3 = KMeans(n_clusters=3, n_init=10, random_state=42).fit_predict(emb)
    ari_emo = float(adjusted_rand_score(emo_idx, km5))
    ari_pol = float(adjusted_rand_score(pol_idx, km3))

    # t-SNE (subsample for speed if large)
    rng = np.random.RandomState(42)
    n = len(emb); idx = np.arange(n)
    if n > 1500:
        idx = rng.choice(n, 1500, replace=False)
    xy = TSNE(n_components=2, perplexity=30, init="pca",
              random_state=42).fit_transform(emb[idx])

    fig, ax = plt.subplots(figsize=(7.2, 6))
    for k, e in enumerate(EMOS):
        m = emo[idx] == e
        ax.scatter(xy[m, 0], xy[m, 1], s=10, alpha=.6, color=EMO_COLORS[k], label=e)
    ax.set_title(f"BanglaBERT embeddings (t-SNE) coloured by emotion\n"
                 f"cluster↔emotion ARI = {ari_emo:.3f} · cluster↔polarity ARI = {ari_pol:.3f}",
                 fontsize=11, fontweight="bold")
    ax.set_xticks([]); ax.set_yticks([])
    ax.legend(fontsize=8, markerscale=1.5, loc="best")
    fig.tight_layout(); fig.savefig(FIG / "20_embedding_tsne_emotion.png", dpi=140, facecolor="white")
    plt.close(fig)
    return {"ari_cluster_vs_emotion_k5": ari_emo, "ari_cluster_vs_polarity_k3": ari_pol,
            "n_embedded": int(n)}


# ======================= (3) religious framing =======================
def religion_analysis(full):
    full = full.copy()
    full["relig"] = full["Comment"].map(is_religious)
    share = float(full["relig"].mean())

    pol_split = (full.groupby("relig")["polarity"].value_counts(normalize=True)
                 .unstack().reindex(columns=LABELS).fillna(0))
    emo_among_relig = (full[full["relig"]]["emotion"].value_counts(normalize=True)
                       .reindex(EMOS).fillna(0))

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
    pol_split.index = ["Non-religious", "Religious"]
    pol_split.plot.bar(ax=ax[0], color=[RED, GREY, GREEN])
    ax[0].set_title("Polarity mix: religious vs non-religious comments", fontweight="bold")
    ax[0].set_ylabel("share"); ax[0].tick_params(axis="x", rotation=0); ax[0].legend(fontsize=8)
    emo_among_relig.plot.bar(ax=ax[1], color=EMO_COLORS)
    ax[1].set_title("Emotion mix WITHIN religious comments", fontweight="bold")
    ax[1].set_ylabel("share"); ax[1].tick_params(axis="x", rotation=25)
    fig.tight_layout(); fig.savefig(FIG / "21_religious_framing.png", dpi=140, facecolor="white")
    plt.close(fig)
    return {"religious_share": share,
            "polarity_by_religious": pol_split.round(3).to_dict(orient="index"),
            "emotion_within_religious": emo_among_relig.round(3).to_dict()}


def main():
    full = pd.read_csv(ANN, dtype=str, keep_default_na=False)
    full = full[full["polarity"].isin(LABELS)]
    test = pd.read_csv(SPLITS / "test.csv", dtype=str, keep_default_na=False)
    print(f"full labelled {len(full)} | test {len(test)}")

    print("[1/3] language-wise robustness ...")
    lang = lang_analysis(full, test)
    print("[2/3] embedding structure (BanglaBERT + KMeans + t-SNE) ...")
    embd = embedding_analysis(full)
    print("[3/3] religious framing ...")
    relig = religion_analysis(full)

    out = {"phase": "5 (deep analysis, batch 1)", "n_full": len(full), "n_test": len(test),
           "language": lang, "embedding": embd, "religion": relig}
    (RES / "phase5_deep_analysis.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    la = pd.DataFrame(lang["test_accuracy_by_language"])
    md = [
        "# Phase 5 — Deep Analysis (batch 1)",
        "",
        "Three analyses beyond the descriptive EDA. (Emotion labels are the current LLM labels; the "
        "victim-blaming audit / human Kappa are still in progress, so emotion splits are indicative.)",
        "",
        "## 1. Language-wise model robustness (held-out test)",
        "",
        "| Language | n | Linear SVM acc | BanglaBERT acc |",
        "|---|---|---|---|",
    ]
    for r in la.itertuples():
        md.append(f"| {r.lang} | {r.n} | {r.svm_acc:.3f} | {r.bert_acc:.3f} |")
    md += [
        "",
        "> Shows whether the models hold up on Banglish/Latin & code-mixed comments, not just pure "
        "Bangla — a key robustness question for a code-switched corpus.",
        "",
        "## 2. Embedding structure — do the labels have unsupervised support?",
        "",
        f"- BanglaBERT sentence embeddings, KMeans vs human labels (Adjusted Rand Index):",
        f"  - cluster ↔ **emotion** (k=5): **ARI = {embd['ari_cluster_vs_emotion_k5']:.3f}**",
        f"  - cluster ↔ **polarity** (k=3): **ARI = {embd['ari_cluster_vs_polarity_k3']:.3f}**",
        "- t-SNE projection coloured by emotion: `figures/20_embedding_tsne_emotion.png`.",
        "> ARI > 0 means the human categories line up with natural structure in the embedding space "
        "(partial validation of the label scheme); low ARI means the classes overlap heavily in "
        "meaning — expected for fine-grained emotion on short social text.",
        "",
        "## 3. Religious framing",
        "",
        f"- **{relig['religious_share']*100:.1f}%** of all comments use religious language.",
        "- Religion is the *vehicle* of both condemnation and blessing — see the polarity split and "
        "the emotion mix within religious comments: `figures/21_religious_framing.png`.",
        "",
        "Figures: `18_lang_distribution.png`, `19_lang_model_accuracy.png`, "
        "`20_embedding_tsne_emotion.png`, `21_religious_framing.png`.",
    ]
    (RES / "phase5_deep_analysis_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("wrote results/phase5_deep_analysis.json + _report.md")
    print(f"  religious share {relig['religious_share']*100:.1f}% | "
          f"ARI emo {embd['ari_cluster_vs_emotion_k5']:.3f} / pol {embd['ari_cluster_vs_polarity_k3']:.3f}")


if __name__ == "__main__":
    main()
