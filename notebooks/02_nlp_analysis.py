# -*- coding: utf-8 -*-
"""NLP analysis on the Scenario text columns — generates 4 NLP charts.
   These complement the 11 EDA charts: EDA = structured columns,
   NLP = free-text Bangla/English scenario columns."""
import os, re, json
from collections import Counter
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud

DATA = r"d:\499 CAPSTONE\elder-abuse\data"
KWJS = r"d:\499 CAPSTONE\elder-abuse\backend\phase1_outputs\keyword_dictionary.json"
BN_FONT = r"d:\499 CAPSTONE\elder-abuse\backend\fonts\NotoSansBengali-Regular.ttf"

PAL = ['#457B9D', '#E63946', '#2A9D8F', '#E9C46A', '#1D3557',
       '#52B788', '#F4A261', '#E76F51', '#264653', '#8AB17D']


def save(fig, name):
    p = os.path.join(DATA, name)
    fig.savefig(p, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print("saved", name)


df = pd.read_csv(os.path.join(DATA, "cleaned_dataset.csv"))

# ── core-category map (same logic as keyword extraction, notebook Cell 55) ────
core_map = {
    'Physical Abuse': 'Physical', 'Financial + Physical': 'Physical',
    'Physical + Abandonment': 'Abandonment', 'Financial + Physical + Abandonment': 'Physical',
    'Abandonment': 'Abandonment', 'Neglect + Abandonment': 'Abandonment',
    'Financial + Abandonment': 'Abandonment', 'Neglect': 'Neglect',
    'Financial + Neglect': 'Neglect', 'Financial Exploitation': 'Financial',
    'Verbal Abuse': 'Verbal', 'Murder': 'Murder', 'Financial + Murder': 'Murder',
}
df['Core'] = df['Category_Norm'].map(core_map)

EN_STOP = {
    'the','a','an','and','or','but','in','on','at','to','for','of','is','was','were',
    'are','be','been','his','her','their','its','he','she','they','him','who','which',
    'that','this','with','by','from','after','over','as','not','no','so','also','had',
    'have','has','did','do','does','into','than','then','when','up','out','it','we','i',
    'you','my','your','our','all','one','two','three','old','elderly','man','woman',
    'father','mother','aged','son','daughter','family','children','child','home','house',
    'because','being','due','being','because','being'
}

BN_STOP = {
    'এবং','করে','তার','থেকে','এই','একটি','হয়','না','করা','ও','এর','তাকে','তারা','কে','যে',
    'হয়েছে','করেছে','করেন','জন্য','সাথে','পরে','কিন্তু','আর','একজন','হয়ে','দিয়ে','নিয়ে','আছে',
    'ছিল','হলে','তিনি','আমি','আমার','তাদের','কিছু','সব','যা','এক','করতে','হবে','বলে','এ','যান',
    'মা','বাবা','ছেলে','মেয়ে','সন্তান','বৃদ্ধ','বৃদ্ধা','পরিবার','বছর','মাকে','বাবাকে','ছেলেরা',
    'করায়','মায়ের','বাবার','দ্বারা','হয়।','করে।','মা।','গিয়ে','একই','পর'
}


def en_tokens(series):
    out = []
    for txt in series.dropna():
        for w in re.findall(r'[a-z]+', str(txt).lower()):
            if w not in EN_STOP and len(w) > 3:
                out.append(w)
    return out


def bn_tokens(series):
    out = []
    for txt in series.dropna():
        for w in re.split(r'\s+', str(txt)):
            w = w.strip('।,.;:!?"\'()[]{}—–-0123456789০১২৩৪৫৬৭৮৯ ')
            if w and w not in BN_STOP and len(w) > 1 and re.search(r'[ঀ-৿]', w):
                out.append(w)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# CHART 12 — Top English keywords per abuse category  (text mining)
# ═════════════════════════════════════════════════════════════════════════════
cats = ['Physical', 'Abandonment', 'Neglect', 'Financial', 'Verbal', 'Murder']
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle('NLP — Top Keywords per Abuse Category (from English Scenario text)',
             fontsize=17, fontweight='bold', color='#1a1a2e', y=1.0)
for ax, cat, col in zip(axes.flat, cats, PAL):
    sub = df[df['Core'] == cat]['Scenerio(English)']
    top = Counter(en_tokens(sub)).most_common(8)
    if not top:
        ax.axis('off'); continue
    words = [w for w, _ in top][::-1]
    vals = [c for _, c in top][::-1]
    ax.barh(words, vals, color=col, edgecolor='white', height=0.7)
    for i, v in enumerate(vals):
        ax.text(v + 0.1, i, str(v), va='center', fontsize=9, fontweight='bold', color='#333')
    ax.set_title(f'{cat}  ({len(sub)} cases)', fontsize=12, fontweight='bold', color=col)
    ax.set_xlim(0, max(vals) + 2)
    ax.tick_params(labelsize=9.5)
    for sp in ['top', 'right']:
        ax.spines[sp].set_visible(False)
plt.tight_layout()
save(fig, 'chart_12_nlp_keywords_by_category.png')

# ═════════════════════════════════════════════════════════════════════════════
# CHART 13 — English scenario WORD CLOUD
# ═════════════════════════════════════════════════════════════════════════════
en_freq = Counter(en_tokens(df['Scenerio(English)']))
wc_en = WordCloud(width=1400, height=720, background_color='white',
                  colormap='YlGnBu', max_words=120, prefer_horizontal=0.92,
                  collocations=False).generate_from_frequencies(en_freq)
fig, ax = plt.subplots(figsize=(13, 6.6))
ax.imshow(wc_en, interpolation='bilinear'); ax.axis('off')
ax.set_title('NLP — Word Cloud of English Abuse Scenarios',
             fontsize=17, fontweight='bold', color='#1a1a2e', pad=14)
save(fig, 'chart_13_nlp_wordcloud_english.png')

# ═════════════════════════════════════════════════════════════════════════════
# CHART 14 — Bangla scenario WORD CLOUD  (Bengali font)
# ═════════════════════════════════════════════════════════════════════════════
bn_freq = Counter(bn_tokens(df['Scenerio(Bangla)']))
wc_bn = WordCloud(width=1400, height=720, background_color='white',
                  font_path=BN_FONT, colormap='OrRd', max_words=110,
                  prefer_horizontal=0.95, collocations=False,
                  regexp=r"[ঀ-৿]+").generate_from_frequencies(bn_freq)
fig, ax = plt.subplots(figsize=(13, 6.6))
ax.imshow(wc_bn, interpolation='bilinear'); ax.axis('off')
ax.set_title('NLP — Word Cloud of Bangla Abuse Scenarios',
             fontsize=17, fontweight='bold', color='#1a1a2e', pad=14)
save(fig, 'chart_14_nlp_wordcloud_bangla.png')

# ═════════════════════════════════════════════════════════════════════════════
# CHART 15 — Keyword dictionary composition (NLP asset built from text)
# ═════════════════════════════════════════════════════════════════════════════
with open(KWJS, encoding='utf-8') as f:
    kw = json.load(f)
cats2 = list(kw.keys())
bn = [len(kw[c].get('bangla', [])) for c in cats2]
en = [len(kw[c].get('english', [])) for c in cats2]
mx = [len(kw[c].get('mixed_forms', [])) for c in cats2]
labels = [c.capitalize() for c in cats2]
fig, ax = plt.subplots(figsize=(12, 6.4))
import numpy as np
x = np.arange(len(cats2))
ax.bar(x, bn, 0.6, label='Bangla', color='#E63946', edgecolor='white')
ax.bar(x, en, 0.6, bottom=bn, label='English', color='#457B9D', edgecolor='white')
ax.bar(x, mx, 0.6, bottom=np.array(bn) + np.array(en), label='Mixed (Banglish)',
       color='#2A9D8F', edgecolor='white')
tot = np.array(bn) + np.array(en) + np.array(mx)
for i, t in enumerate(tot):
    ax.text(i, t + 0.6, str(t), ha='center', fontsize=11, fontweight='bold', color='#333')
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=11.5)
ax.set_ylabel('Number of keywords', fontsize=12, color='#444')
ax.set_title('NLP — Keyword Dictionary built from Scenario text  (231 keywords)',
             fontsize=16, fontweight='bold', color='#1a1a2e', pad=16)
ax.set_ylim(0, tot.max() + 8)
ax.legend(fontsize=11, frameon=False)
for sp in ['top', 'right']:
    ax.spines[sp].set_visible(False)
plt.tight_layout()
save(fig, 'chart_15_nlp_keyword_dictionary.png')

print("ALL NLP CHARTS DONE")
