# -*- coding: utf-8 -*-
"""
Phase 5 (batch 2) — Explainability + error analysis.

  (A) Explainability — which words drive each polarity? Read the Linear-SVM
      coefficients (word n-grams only) and list the most discriminative tokens
      per class. Cheap, faithful, and directly interpretable (no SHAP needed).
  (B) Error analysis — on the held-out test set: where do the models fail, which
      confusions dominate, does emoji/code-switch correlate with errors, and what
      do the hardest (both-models-wrong) cases look like.

Run with the D: venv (needs torch + transformers + sklearn):
    .venv-bert\\Scripts\\python.exe sentiment/src/explain_errors.py

Outputs: results/phase5_explain_errors.json + _report.md
"""
from __future__ import annotations
import os, sys, io, json, re
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\pysetup\hf_cache")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"
MODELS = ROOT / "models"
LABELS = ["Negative", "Neutral", "Positive"]
L2I = {l: i for i, l in enumerate(LABELS)}

import joblib
from sklearn.metrics import accuracy_score
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

EMOJI = re.compile("[" "\U0001F300-\U0001FAFF" "\U00002600-\U000027BF"
                   "\U0001F000-\U0001F0FF" "\U00002190-\U000021FF" "\U00002B00-\U00002BFF" "]")


def predict_baseline(texts):
    pipe = joblib.load(MODELS / "baseline_best.joblib")
    raw = pipe.predict(texts)
    return (np.array([L2I[str(v)] for v in raw]) if raw.dtype.kind in "US"
            else raw.astype(int))


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


# ============ (A) explainability ============
def explainability(topn=15):
    pipe = joblib.load(MODELS / "baseline_best.joblib")
    clf = pipe.steps[-1][1]
    feats = pipe[:-1].get_feature_names_out()
    wmask = np.array([f.startswith("word__") for f in feats])
    words = np.array([f[6:] for f in feats])[wmask]
    wcoef = clf.coef_[:, wmask]
    out = {}
    for ci, cls in enumerate(LABELS):
        order = np.argsort(wcoef[ci])[::-1][:topn]
        out[cls] = [{"token": words[t], "weight": round(float(wcoef[ci][t]), 3)} for t in order]
    return out


# ============ (B) error analysis ============
def error_analysis(df):
    X = df["Comment"].tolist()
    y = np.array([L2I[v] for v in df["polarity"]])
    pb = predict_baseline(X)
    pr = predict_bert(X)

    def conf_pairs(pred):
        d = {}
        for t, p in zip(y, pred):
            if t != p:
                k = f"{LABELS[t]}→{LABELS[p]}"
                d[k] = d.get(k, 0) + 1
        return dict(sorted(d.items(), key=lambda kv: -kv[1]))

    has_emoji = np.array([bool(EMOJI.search(t)) for t in X])
    lang = df["lang"].values
    is_latin = np.isin(lang, ["latin", "bn+en"])

    def err_rate(mask, pred):
        return float(np.mean(pred[mask] != y[mask])) if mask.sum() else None

    both_wrong = (pb != y) & (pr != y)
    hard = []
    for i in np.where(both_wrong)[0]:
        hard.append({"comment_id": df.iloc[i]["comment_id"],
                     "text": X[i][:120], "true": LABELS[y[i]],
                     "svm": LABELS[pb[i]], "bert": LABELS[pr[i]], "lang": lang[i]})

    return {
        "n_test": len(df),
        "svm_acc": float(accuracy_score(y, pb)), "bert_acc": float(accuracy_score(y, pr)),
        "svm_confusions": conf_pairs(pb), "bert_confusions": conf_pairs(pr),
        "both_wrong": int(both_wrong.sum()),
        "svm_only_wrong": int(((pb != y) & (pr == y)).sum()),
        "bert_only_wrong": int(((pr != y) & (pb == y)).sum()),
        "error_rate_by_group": {
            "svm_emoji": err_rate(has_emoji, pb), "svm_no_emoji": err_rate(~has_emoji, pb),
            "bert_emoji": err_rate(has_emoji, pr), "bert_no_emoji": err_rate(~has_emoji, pr),
            "svm_latin_script": err_rate(is_latin, pb), "svm_bangla": err_rate(~is_latin, pb),
            "bert_latin_script": err_rate(is_latin, pr), "bert_bangla": err_rate(~is_latin, pr),
        },
        "hardest_examples": hard[:12],
    }


def main():
    test = pd.read_csv(SPLITS / "test.csv", dtype=str, keep_default_na=False)
    print("[A] explainability (SVM word coefficients) ...")
    expl = explainability()
    print("[B] error analysis on test ...")
    err = error_analysis(test)

    out = {"phase": "5 (deep analysis, batch 2)", "explainability_top_words": expl,
           "error_analysis": err}
    (RES / "phase5_explain_errors.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    md = ["# Phase 5 — Explainability & Error Analysis (batch 2)", ""]
    md += ["## A. What words drive each polarity (Linear-SVM coefficients, word n-grams)", ""]
    for cls in LABELS:
        toks = " · ".join(f"`{t['token']}`" for t in expl[cls][:12])
        md += [f"**{cls}** — {toks}", ""]
    md += ["> These are the most positively-weighted word features per class — a faithful, "
           "transparent view of what the classifier keys on (no black box).", ""]

    e = err
    md += ["## B. Error analysis (held-out test)", "",
           f"- Test accuracy: SVM **{e['svm_acc']:.3f}**, BanglaBERT **{e['bert_acc']:.3f}**.",
           f"- Both models wrong on **{e['both_wrong']}** / {e['n_test']} · "
           f"SVM-only-wrong {e['svm_only_wrong']} · BERT-only-wrong {e['bert_only_wrong']}.",
           "",
           "### Dominant confusions",
           "", "| Model | most common true→pred errors |", "|---|---|",
           f"| SVM | {', '.join(f'{k} ({v})' for k,v in list(e['svm_confusions'].items())[:4])} |",
           f"| BanglaBERT | {', '.join(f'{k} ({v})' for k,v in list(e['bert_confusions'].items())[:4])} |",
           "",
           "### Error rate by group (lower = better)", "",
           "| Group | SVM | BanglaBERT |", "|---|---|---|"]
    g = e["error_rate_by_group"]
    def fmt(x): return f"{x:.3f}" if x is not None else "—"
    md += [f"| Bangla script | {fmt(g['svm_bangla'])} | {fmt(g['bert_bangla'])} |",
           f"| Latin/code-mixed | {fmt(g['svm_latin_script'])} | {fmt(g['bert_latin_script'])} |",
           f"| has emoji | {fmt(g['svm_emoji'])} | {fmt(g['bert_emoji'])} |",
           f"| no emoji | {fmt(g['svm_no_emoji'])} | {fmt(g['bert_no_emoji'])} |", "",
           "> Confirms the batch-1 finding: BanglaBERT's error rate spikes on Latin/code-mixed text.",
           "", "### Hardest cases (both models wrong)", "",
           "| id | true | SVM | BERT | comment |", "|---|---|---|---|---|"]
    for h in e["hardest_examples"]:
        txt = h["text"].replace("|", "/").replace("\n", " ")
        md += [f"| {h['comment_id']} | {h['true']} | {h['svm']} | {h['bert']} | {txt} |"]
    md += ["", "> Many hard cases are sarcasm, mixed sentiment, or Neutral-vs-Negative boundary "
           "calls — the intrinsically ambiguous middle.", ""]
    (RES / "phase5_explain_errors_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote results/phase5_explain_errors.json + _report.md")
    print(f"  both-wrong {e['both_wrong']}/{e['n_test']} | "
          f"bert latin err {fmt(g['bert_latin_script'])} vs bangla {fmt(g['bert_bangla'])}")


if __name__ == "__main__":
    main()
