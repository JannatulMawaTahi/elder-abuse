# -*- coding: utf-8 -*-
"""
Phase 3 (Part 2) — BanglaBERT fine-tune for SENTIMENT (polarity).

READY-TO-RUN, but needs a working PyTorch. On this machine PyTorch fails to load
under Python 3.14 (WinError 193 — the 3.14 wheels are not yet ABI-stable). Run it
in a Python 3.11/3.12 environment, e.g.:

    py -3.12 -m venv .venv-bert
    .venv-bert\\Scripts\\activate
    pip install torch transformers scikit-learn pandas numpy matplotlib
    python sentiment/src/train_bert.py

Trains on data/splits/train.csv, selects on val.csv. Test stays LOCKED.
Class-weighted cross-entropy handles the Neg/Neu/Pos imbalance.

Outputs : results/phase3_bert.json + _report.md
          figures/15_bert_confusion.png
          models/banglabert_polarity/  (best checkpoint)
"""
from __future__ import annotations
import os, sys, io, json
from pathlib import Path

# Keep all HuggingFace/torch caches OFF the full C: drive (this machine's C: is full).
os.environ.setdefault("HF_HOME", r"D:\pysetup\hf_cache")
os.environ.setdefault("TMP", r"D:\pysetup\tmp")
os.environ.setdefault("TEMP", r"D:\pysetup\tmp")

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"
FIG = ROOT / "figures"
MODELS = ROOT / "models"
for d in (RES, FIG, MODELS):
    d.mkdir(parents=True, exist_ok=True)

SEED = 42
TARGET = "polarity"
LABELS = ["Negative", "Neutral", "Positive"]
L2I = {l: i for i, l in enumerate(LABELS)}
MODEL_NAME = "sagorsarker/bangla-bert-base"   # BanglaBERT; swap for xlm-roberta-base to compare
MAX_LEN = 128
EPOCHS = 5            # tuned run: more epochs, best val-checkpoint is kept
BATCH = 16
LR = 2e-5
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01

try:
    import torch
    from torch import nn
    from torch.utils.data import Dataset
    from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                              TrainingArguments, Trainer)
except Exception as e:                        # pragma: no cover
    sys.exit(f"[blocked] PyTorch/transformers unavailable: {e}\n"
             f"Run this script in a Python 3.11/3.12 env (see module docstring).")

from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
torch.manual_seed(SEED); np.random.seed(SEED)


def load(name):
    df = pd.read_csv(SPLITS / f"{name}.csv", dtype=str, keep_default_na=False)
    return df["Comment"].tolist(), [L2I[y] for y in df[TARGET]]


class DS(Dataset):
    def __init__(self, enc, labels):
        self.enc = enc; self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, i):
        item = {k: torch.tensor(v[i]) for k, v in self.enc.items()}
        item["labels"] = torch.tensor(self.labels[i])
        return item


def metrics(eval_pred):
    logits, y = eval_pred
    pred = np.argmax(logits, axis=1)
    return {"macro_f1": f1_score(y, pred, average="macro"),
            "accuracy": accuracy_score(y, pred)}


class WeightedTrainer(Trainer):
    def __init__(self, class_weights, **kw):
        super().__init__(**kw)
        self.cw = class_weights
    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        labels = inputs.pop("labels")
        out = model(**inputs)
        loss = nn.CrossEntropyLoss(weight=self.cw.to(out.logits.device))(out.logits, labels)
        return (loss, out) if return_outputs else loss


def main():
    Xtr, ytr = load("train"); Xva, yva = load("val")
    print(f"train {len(Xtr)} | val {len(Xva)} | model {MODEL_NAME}")

    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    enc_tr = tok(Xtr, truncation=True, padding="max_length", max_length=MAX_LEN)
    enc_va = tok(Xva, truncation=True, padding="max_length", max_length=MAX_LEN)
    ds_tr, ds_va = DS(enc_tr, ytr), DS(enc_va, yva)

    counts = np.bincount(ytr, minlength=3)
    cw = torch.tensor((counts.sum() / (3 * counts)), dtype=torch.float)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=3)

    args = TrainingArguments(
        output_dir=str(MODELS / "banglabert_polarity"),
        num_train_epochs=EPOCHS, per_device_train_batch_size=BATCH,
        per_device_eval_batch_size=BATCH, learning_rate=LR,
        warmup_ratio=WARMUP_RATIO, weight_decay=WEIGHT_DECAY,
        eval_strategy="epoch", save_strategy="epoch",
        load_best_model_at_end=True, metric_for_best_model="macro_f1",
        save_total_limit=1, seed=SEED, logging_steps=50, report_to=[])
    trainer = WeightedTrainer(class_weights=cw, model=model, args=args,
                              train_dataset=ds_tr, eval_dataset=ds_va,
                              compute_metrics=metrics)
    ckpts = sorted((MODELS / "banglabert_polarity").glob("checkpoint-*"),
                   key=lambda p: int(p.name.split("-")[1]))
    resume = bool(ckpts)
    print(f"resume_from_checkpoint={resume}" + (f" ({ckpts[-1].name})" if resume else ""))
    trainer.train(resume_from_checkpoint=resume)

    pred = np.argmax(trainer.predict(ds_va).predictions, axis=1)
    rep = classification_report(yva, pred, target_names=LABELS, output_dict=True, zero_division=0)
    out = {"task": "sentiment/polarity", "phase": "3 (BanglaBERT)", "model": MODEL_NAME,
           "dev_split": "val (test locked)", "macro_f1": float(f1_score(yva, pred, average="macro")),
           "accuracy": float(accuracy_score(yva, pred)), "per_class": rep}
    (RES / "phase3_bert.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    cm = confusion_matrix(yva, pred)
    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    im = ax.imshow(cm, cmap="Greens")
    ax.set_xticks(range(3)); ax.set_xticklabels(LABELS)
    ax.set_yticks(range(3)); ax.set_yticklabels(LABELS)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    for i in range(3):
        for j in range(3):
            ax.text(j, i, int(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > cm.max()*0.55 else "#222", fontweight="bold")
    ax.set_title("Validation confusion — BanglaBERT", fontsize=12, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.savefig(FIG / "15_bert_confusion.png", dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    trainer.save_model(str(MODELS / "banglabert_polarity"))
    tok.save_pretrained(str(MODELS / "banglabert_polarity"))   # keep the tokenizer with the model
    print(f"BanglaBERT val macro-F1 {out['macro_f1']:.4f} | acc {out['accuracy']:.4f}")


if __name__ == "__main__":
    main()
