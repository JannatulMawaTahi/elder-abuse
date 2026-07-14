# -*- coding: utf-8 -*-
"""
Phase 1.5 — Exploratory Data Analysis (in-depth) on the AI silver labels.

Reads  : sentiment/data/annotated/llm_labels.csv  (2301 comments, polarity + emotion)
Writes : sentiment/figures/*.png   (paper-ready charts)
         sentiment/results/eda_stats.json
         sentiment/results/eda_findings.md   (human-readable summary of findings)

All charts use a Bengali-capable font so Bangla tokens render correctly.
This is descriptive analysis only (no modelling) — it characterises the dataset
and surfaces the paper's key cross-findings (victim-blaming & religious framing
by abuse topic, language/platform effects, engagement).
"""
from __future__ import annotations
import sys, io, json, re
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "data" / "annotated" / "llm_labels.csv"
FIG = ROOT / "figures"
RES = ROOT / "results"
FIG.mkdir(parents=True, exist_ok=True)
RES.mkdir(parents=True, exist_ok=True)

BN_FONT = Path(r"d:\499 CAPSTONE\elder-abuse\backend\fonts\NotoSansBengali-Regular.ttf")
if BN_FONT.exists():
    font_manager.fontManager.addfont(str(BN_FONT))
    bn_name = font_manager.FontProperties(fname=str(BN_FONT)).get_name()
    # per-glyph fallback: Bengali font first, DejaVu Sans for Latin/digits
    plt.rcParams["font.family"] = [bn_name, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# HarfBuzz-based shaping for Bengali labels (matplotlib can't shape conjuncts).
# Falls back to plain text if the shaping libs are unavailable.
try:
    from bn_shape import BnFont, zoom_for
    BNF = BnFont(str(BN_FONT)) if BN_FONT.exists() else None
    BN_DPI = 220
except Exception as _e:           # pragma: no cover
    BNF = None
    print("bn_shape unavailable, Bengali labels may render unshaped:", _e)


def bn_label_y(ax, x, y, text, size_pt=15, color="#222222", ha_right=True):
    """Place a properly-shaped Bengali label anchored at data (x, y)."""
    if BNF is None or str(text).isascii():
        ax.text(x, y, str(text), ha="right" if ha_right else "left",
                va="center", fontsize=size_pt * 0.75, color=color)
        return
    img = BNF.render_image(str(text), float(size_pt), color)
    oi = OffsetImage(img, zoom=zoom_for(BN_DPI))
    ab = AnnotationBbox(oi, (x, y), xybox=(-6 if ha_right else 6, 0),
                        xycoords="data", boxcoords="offset points",
                        box_alignment=(1 if ha_right else 0, 0.5),
                        frameon=False, pad=0)
    ax.add_artist(ab)

# colour palettes
POL_ORDER = ["Negative", "Neutral", "Positive"]
POL_COL = {"Negative": "#E63946", "Neutral": "#6C757D", "Positive": "#2A9D8F"}
EMO_ORDER = ["Anger/Condemnation", "Victim-blaming", "Grief/Sympathy",
             "Prayer/Religious", "Neutral-Other"]
EMO_COL = {"Anger/Condemnation": "#E63946", "Victim-blaming": "#9D4EDD",
           "Grief/Sympathy": "#457B9D", "Prayer/Religious": "#E9C46A",
           "Neutral-Other": "#ADB5BD"}

STATS: dict = {}


def save(fig, name):
    p = FIG / name
    fig.savefig(p, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", p.name)


def pct(n, d):
    return round(100 * n / d, 1) if d else 0.0


# ───────────────────────────── load ─────────────────────────────
df = pd.read_csv(LABELS, dtype=str, keep_default_na=False)
df["Likes"] = pd.to_numeric(df["Likes"], errors="coerce").fillna(0).astype(int)
df["char_len"] = pd.to_numeric(df["char_len"], errors="coerce").fillna(0).astype(int)
N = len(df)
STATS["n_comments"] = N
print(f"loaded {N} comments")

# normalise abuse_type display (keep as-is but title for charts)
abuse_order = df["abuse_type"].value_counts().index.tolist()
lang_order = df["lang"].value_counts().index.tolist()


# ── 1. Polarity distribution ──
def chart_polarity():
    vc = df["polarity"].value_counts().reindex(POL_ORDER).fillna(0).astype(int)
    STATS["polarity"] = {k: int(v) for k, v in vc.items()}
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(vc.index, vc.values, color=[POL_COL[k] for k in vc.index], width=0.6)
    for b, v in zip(bars, vc.values):
        ax.text(b.get_x() + b.get_width() / 2, v + 12, f"{v}\n({pct(v, N)}%)",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_title("Sentiment polarity distribution (n=%d)" % N, fontsize=13, fontweight="bold")
    ax.set_ylabel("Comments"); ax.set_ylim(0, vc.max() * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "01_polarity_dist.png")


# ── 2. Emotion distribution ──
def chart_emotion():
    vc = df["emotion"].value_counts().reindex(EMO_ORDER).fillna(0).astype(int)
    STATS["emotion"] = {k: int(v) for k, v in vc.items()}
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    order = vc.sort_values(ascending=True)
    bars = ax.barh(order.index, order.values, color=[EMO_COL[k] for k in order.index])
    for b, v in zip(bars, order.values):
        ax.text(v + 6, b.get_y() + b.get_height() / 2, f"{v} ({pct(v, N)}%)",
                va="center", fontsize=10, fontweight="bold")
    ax.set_title("Fine-grained emotion distribution (n=%d)" % N, fontsize=13, fontweight="bold")
    ax.set_xlabel("Comments"); ax.set_xlim(0, order.max() * 1.18)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "02_emotion_dist.png")


# ── 3. Polarity x Emotion heatmap ──
def chart_pol_emo():
    ct = pd.crosstab(df["emotion"], df["polarity"]).reindex(index=EMO_ORDER, columns=POL_ORDER).fillna(0)
    STATS["polarity_x_emotion"] = ct.astype(int).to_dict()
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    im = ax.imshow(ct.values, cmap="YlOrRd", aspect="auto")
    ax.set_xticks(range(len(POL_ORDER))); ax.set_xticklabels(POL_ORDER)
    ax.set_yticks(range(len(EMO_ORDER))); ax.set_yticklabels(EMO_ORDER)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            v = int(ct.values[i, j])
            ax.text(j, i, v, ha="center", va="center", fontsize=10,
                    color="white" if v > ct.values.max() * 0.55 else "#222", fontweight="bold")
    ax.set_title("Polarity × Emotion (counts)", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8, label="comments")
    save(fig, "03_polarity_x_emotion.png")


# ── 4. Abuse-type x Emotion (row-normalised %) — KEY cross-finding ──
def chart_abuse_emo():
    ct = pd.crosstab(df["abuse_type"], df["emotion"]).reindex(index=abuse_order, columns=EMO_ORDER).fillna(0)
    row_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    STATS["abuse_x_emotion_pct"] = row_pct.round(1).to_dict()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    im = ax.imshow(row_pct.values, cmap="viridis", aspect="auto")
    ax.set_xticks(range(len(EMO_ORDER))); ax.set_xticklabels(EMO_ORDER, rotation=20, ha="right")
    ax.set_yticks(range(len(abuse_order))); ax.set_yticklabels(abuse_order)
    for i in range(row_pct.shape[0]):
        for j in range(row_pct.shape[1]):
            v = row_pct.values[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=9,
                    color="white" if v < 55 else "#111", fontweight="bold")
    ax.set_title("Emotion mix by abuse topic (row %)", fontsize=13, fontweight="bold")
    fig.colorbar(im, ax=ax, shrink=0.8, label="% of topic's comments")
    save(fig, "04_abusetype_x_emotion.png")


# ── 5. Abuse-type x Polarity (stacked %) ──
def chart_abuse_pol():
    ct = pd.crosstab(df["abuse_type"], df["polarity"]).reindex(index=abuse_order, columns=POL_ORDER).fillna(0)
    row_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    STATS["abuse_x_polarity_pct"] = row_pct.round(1).to_dict()
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    left = np.zeros(len(abuse_order))
    for pol in POL_ORDER:
        vals = row_pct[pol].values
        ax.barh(abuse_order, vals, left=left, color=POL_COL[pol], label=pol)
        for i, (v, l) in enumerate(zip(vals, left)):
            if v > 6:
                ax.text(l + v / 2, i, f"{v:.0f}%", ha="center", va="center",
                        fontsize=9, color="white", fontweight="bold")
        left += vals
    ax.set_title("Polarity by abuse topic (%)", fontsize=13, fontweight="bold")
    ax.set_xlabel("% of comments"); ax.set_xlim(0, 100)
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.22))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "05_abusetype_x_polarity.png")


# ── 6. Platform x emotion (%) ──
def chart_platform():
    ct = pd.crosstab(df["platform"], df["emotion"]).reindex(columns=EMO_ORDER).fillna(0)
    row_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    STATS["platform_counts"] = df["platform"].value_counts().to_dict()
    STATS["platform_x_emotion_pct"] = row_pct.round(1).to_dict()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    x = np.arange(len(EMO_ORDER)); w = 0.38
    plats = row_pct.index.tolist()
    for k, plat in enumerate(plats):
        ax.bar(x + (k - 0.5) * w, row_pct.loc[plat].values, width=w, label=plat,
               color=["#FF0000", "#1877F2"][k % 2])
    ax.set_xticks(x); ax.set_xticklabels(EMO_ORDER, rotation=20, ha="right")
    ax.set_ylabel("% within platform")
    ax.set_title("Emotion mix: YouTube vs Facebook", fontsize=13, fontweight="bold")
    ax.legend(frameon=False); ax.spines[["top", "right"]].set_visible(False)
    save(fig, "06_platform_x_emotion.png")


# ── 7. Language x polarity (%) ──
def chart_language():
    ct = pd.crosstab(df["lang"], df["polarity"]).reindex(index=lang_order, columns=POL_ORDER).fillna(0)
    STATS["lang_counts"] = df["lang"].value_counts().to_dict()
    row_pct = ct.div(ct.sum(axis=1), axis=0) * 100
    STATS["lang_x_polarity_pct"] = row_pct.round(1).to_dict()
    fig, ax = plt.subplots(figsize=(8, 4.3))
    left = np.zeros(len(lang_order))
    for pol in POL_ORDER:
        vals = row_pct[pol].values
        ax.barh(lang_order, vals, left=left, color=POL_COL[pol], label=pol)
        left += vals
    ax.set_title("Polarity by language (%)", fontsize=13, fontweight="bold")
    ax.set_xlabel("% of comments"); ax.set_xlim(0, 100)
    ax.legend(ncol=3, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.25))
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "07_language_x_polarity.png")


# ── 8. Comment length by emotion (box) ──
def chart_length():
    data = [df.loc[df["emotion"] == e, "char_len"].values for e in EMO_ORDER]
    STATS["median_charlen_by_emotion"] = {e: int(np.median(d)) if len(d) else 0
                                          for e, d in zip(EMO_ORDER, data)}
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    bp = ax.boxplot(data, vert=True, patch_artist=True, showfliers=False,
                    medianprops=dict(color="black"))
    for patch, e in zip(bp["boxes"], EMO_ORDER):
        patch.set_facecolor(EMO_COL[e])
    ax.set_xticklabels(EMO_ORDER, rotation=20, ha="right")
    ax.set_ylabel("Comment length (chars)")
    ax.set_title("Comment length by emotion (outliers hidden)", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "08_length_by_emotion.png")


# ── 9. Engagement: mean Likes by emotion ──
def chart_engagement():
    m = df.groupby("emotion")["Likes"].mean().reindex(EMO_ORDER).fillna(0)
    STATS["mean_likes_by_emotion"] = {k: round(float(v), 2) for k, v in m.items()}
    fig, ax = plt.subplots(figsize=(8.5, 4.3))
    bars = ax.bar(range(len(m)), m.values, color=[EMO_COL[e] for e in m.index])
    for b, v in zip(bars, m.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(m))); ax.set_xticklabels(m.index, rotation=20, ha="right")
    ax.set_ylabel("Mean likes")
    ax.set_title("Engagement (mean likes) by emotion", fontsize=13, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "09_likes_by_emotion.png")


# ── 10. Victim-blaming & Prayer prevalence by abuse topic ──
def chart_blame_prayer():
    for emo, fname, col, title in [
        ("Victim-blaming", "10_victimblame_by_abuse.png", "#9D4EDD", "Victim-blaming"),
        ("Prayer/Religious", "11_prayer_by_abuse.png", "#E9C46A", "Prayer/Religious framing"),
    ]:
        sub = df[df["emotion"] == emo]
        share = (sub["abuse_type"].value_counts().reindex(abuse_order).fillna(0)
                 / df["abuse_type"].value_counts().reindex(abuse_order) * 100)
        STATS.setdefault("emotion_share_by_abuse_pct", {})[emo] = share.round(1).to_dict()
        fig, ax = plt.subplots(figsize=(8, 4.2))
        bars = ax.bar(share.index, share.values, color=col)
        for b, v in zip(bars, share.values):
            ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.1f}%", ha="center", va="bottom",
                    fontsize=10, fontweight="bold")
        ax.set_ylabel("% of topic's comments")
        ax.set_title(f"{title}: prevalence by abuse topic", fontsize=13, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
        save(fig, fname)


# ── 12-13. Top tokens per emotion + word clouds ──
EN_STOP = set("the a an and or but in on at to for of is was were are be been his her their "
              "its he she they him who which that this with by from after over as not no so also "
              "had have has did do does into than then when up out it we i you my your our all one "
              "ki na ar o e ei eta ki je tor tui ora oder kore koto hoy hobe ".split())
BN_STOP = {"এবং", "করে", "তার", "থেকে", "এই", "একটি", "হয়", "না", "করা", "ও", "এর", "তাকে",
           "তারা", "কে", "যে", "হয়েছে", "করেছে", "জন্য", "সাথে", "পরে", "কিন্তু", "আর", "একজন",
           "হয়ে", "দিয়ে", "নিয়ে", "আছে", "ছিল", "হলে", "তিনি", "আমি", "আমার", "তাদের", "কিছু",
           "সব", "যা", "এক", "করতে", "হবে", "বলে", "এ", "কি", "কী", "এসব", "এই", " এর", "ওরে",
           "কেন", "আজ", "হোক", "করি", "যায়", "মত", "মতো", "তো", "ই", "এমন", "শুরু", "হলো", "দেশে"}
TOK = re.compile(r"[ঀ-৿A-Za-z]{2,}")


def top_tokens(series, k=12):
    c = Counter()
    for t in series:
        for w in TOK.findall(str(t)):
            wl = w.lower()
            if wl in EN_STOP or w in BN_STOP:
                continue
            c[w] += 1
    return c.most_common(k)


def chart_keywords():
    kw = {}
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, emo in zip(axes, ["Anger/Condemnation", "Victim-blaming", "Grief/Sympathy"]):
        toks = top_tokens(df.loc[df["emotion"] == emo, "Comment"], 10)
        kw[emo] = toks
        words = [w for w, _ in toks][::-1]
        vals = [c for _, c in toks][::-1]
        ypos = list(range(len(words)))
        ax.barh(ypos, vals, color=EMO_COL[emo])
        ax.set_yticks(ypos)
        ax.set_yticklabels([""] * len(words))   # hide unshaped labels
        ax.set_ylim(-0.6, len(words) - 0.4)
        ax.margins(x=0.02)
        for y, w in zip(ypos, words):            # draw shaped Bengali labels
            bn_label_y(ax, 0, y, w, size_pt=15, color="#222222")
        ax.set_title(emo, fontsize=12, fontweight="bold")
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Top distinctive tokens per emotion (stopwords removed)",
                 fontsize=14, fontweight="bold")
    fig.subplots_adjust(left=0.12, wspace=0.45)
    save(fig, "12_top_tokens.png")
    STATS["top_tokens"] = {k_: v_ for k_, v_ in kw.items()}

    # ── 13. shaped, frequency-sized Bengali words (ranked list) ──
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    cmap = plt.get_cmap("magma")
    for ax, emo in zip(axes, ["Anger/Condemnation", "Victim-blaming"]):
        toks = top_tokens(df.loc[df["emotion"] == emo, "Comment"], 12)
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.set_title(emo, fontsize=13, fontweight="bold")
        if not toks:
            continue
        mx = toks[0][1]
        n = len(toks)
        for i, (w, c) in enumerate(toks):
            y = 1 - (i + 0.5) / n
            size = 13 + 24 * (c / mx)                # 13..37 pt by frequency
            col = matplotlib.colors.to_hex(cmap(0.12 + 0.6 * c / mx))
            bn_label_y(ax, 0.06, y, w, size_pt=size, color=col, ha_right=False)
    fig.suptitle("Frequency-sized distinctive words", fontsize=14, fontweight="bold")
    save(fig, "13_wordclouds.png")


# ───────────────────────────── run all ─────────────────────────────
chart_polarity(); chart_emotion(); chart_pol_emo(); chart_abuse_emo()
chart_abuse_pol(); chart_platform(); chart_language(); chart_length()
chart_engagement(); chart_blame_prayer(); chart_keywords()

# overall numbers
STATS["negative_share_pct"] = pct((df["polarity"] == "Negative").sum(), N)
STATS["victimblame_share_pct"] = pct((df["emotion"] == "Victim-blaming").sum(), N)
STATS["prayer_share_pct"] = pct((df["emotion"] == "Prayer/Religious").sum(), N)

(RES / "eda_stats.json").write_text(json.dumps(STATS, indent=2, ensure_ascii=False), encoding="utf-8")
print("\nwrote results/eda_stats.json")
print(f"figures: {len(list(FIG.glob('*.png')))} png in {FIG}")
