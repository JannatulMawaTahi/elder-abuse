"""
Update charts: regenerate chart_02 and chart_09 with Son normalization fix,
and delete old/unwanted chart files.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = r"d:\499 CAPSTONE\elder-abuse\data\Elder_abuse_Dataset.csv"
OUT_DIR   = r"d:\499 CAPSTONE\elder-abuse\data"
DPI       = 180

plt.rcParams.update({
    'font.family':        'DejaVu Sans',
    'font.size':          11,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.facecolor':   'white',
    'axes.facecolor':     'white',
})

# ── Delete old unwanted files ─────────────────────────────────────────────────
to_delete = [
    r"d:\499 CAPSTONE\elder-abuse\data\chart_03_data_source.png",
    r"d:\499 CAPSTONE\elder-abuse\data\chart_04_gender.png",
    r"d:\499 CAPSTONE\elder-abuse\data\chart_10_data_source_type.png",
]
for f in to_delete:
    if os.path.exists(f):
        os.remove(f)
        print(f"Deleted: {os.path.basename(f)}")
    else:
        print(f"Not found (skip): {os.path.basename(f)}")

# ── Load & Normalize ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding='utf-8')

# Strip ALL whitespace from Abuse Relation first, then normalize
df['Abuse Relation'] = df['Abuse Relation'].str.strip()

cat_map = {
    'Physical': 'Physical Abuse',
    'Physcial': 'Physical Abuse',
    'Physical Abuse': 'Physical Abuse',
    'Physical and neglect': 'Physical Abuse',
    'Verbally': 'Verbal Abuse',
    'verbally': 'Verbal Abuse',
    'Neglect ': 'Neglect',
    'Abandonment and physical': 'Physical + Abandonment',
    'Neglect and Abandonment': 'Neglect + Abandonment',
    'Financial Exploitation and Abandonment': 'Financial + Abandonment',
    'Financial Exploitation and physical': 'Financial + Physical',
    'Financial Exploitation and neglect': 'Financial + Neglect',
    'Financial Exploitation and Murder': 'Financial + Murder',
    'Financial Exploitation and Neglect': 'Financial + Neglect',
    'Financial Exploitation, physical and abandonment': 'Financial + Physical + Abandonment',
}
df['Category_Norm'] = df['Abuse Category'].str.strip().replace(cat_map)
df['Category_Norm'] = df['Category_Norm'].fillna(df['Abuse Category'].str.strip())

rel_map = {
    'Son and daughter-in-law': 'Son & Daughter-in-law',
    'Children': 'Children',
    'Son': 'Son',
    'Daughter-in-law': 'Daughter-in-law',
    'Family': 'Family',
    'Neighbor': 'Neighbor',
    'Relative': 'Relative',
    'Neighbors': 'Neighbor',
    'Homemaid': 'House Help',
    'Landlord': 'Landlord',
    'Grand son': 'Grandchild',
    'Wife and Children': 'Spouse & Children',
    'Nephew and his wife': 'Nephew & Wife',
    'Husband and daughter-in-law': 'Husband & D-in-law',
    'Son-in-law and Grand son': 'Son-in-law & Grandson',
    'Son, daughter-in-law and grand son': 'Son & Family',
    'Son and Grand son': 'Son & Grandchild',
    'Union Council Member': 'Govt. Official',
    'Police': 'Govt. Official',
    'Younger Brother': 'Younger Brother',
    'Daughter': 'Daughter',
}
df['Relation_Norm'] = df['Abuse Relation'].replace(rel_map)
df['Relation_Norm'] = df['Relation_Norm'].fillna(df['Abuse Relation'])

# Trust Blind Spot
family_kw = ['son','daughter','spouse','husband','wife','child','nephew','grandchild']
df['Trust_Blind_Spot'] = df['Relation_Norm'].str.lower().str.contains(
    '|'.join(family_kw), na=False).astype(int)

# Severity
severity_map = {
    'Murder': 5, 'Financial + Murder': 5,
    'Physical Abuse': 4, 'Financial + Physical': 4,
    'Physical + Abandonment': 4, 'Financial + Physical + Abandonment': 4,
    'Abandonment': 3, 'Neglect + Abandonment': 3, 'Financial + Abandonment': 3,
    'Financial Exploitation': 2, 'Neglect': 2, 'Financial + Neglect': 2,
    'Verbal Abuse': 1,
}
df['Severity_Score'] = df['Category_Norm'].map(severity_map).fillna(2)

print(f"\nDataset loaded: {len(df)} rows")
print("Relation_Norm unique Sons:", df[df['Relation_Norm'] == 'Son'].shape[0])

# ── Palette ───────────────────────────────────────────────────────────────────
RICH_PALETTE = [
    '#E63946','#2A9D8F','#E9C46A','#264653','#F4A261',
    '#A8DADC','#457B9D','#1D3557','#6D6875','#B5838D',
    '#E76F51','#52B788','#90E0EF','#C77DFF','#F72585',
    '#4CC9F0','#FF9F1C','#CBFF8C','#8338EC','#FB5607',
]
def make_colors(n):
    return RICH_PALETTE[:n] if n <= len(RICH_PALETTE) else (RICH_PALETTE * 3)[:n]

def save(name):
    path = f"{OUT_DIR}\\{name}.png"
    plt.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"[OK] {name}.png saved")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Abuser Relation (fixed: Son normalized, unique colors)
# ══════════════════════════════════════════════════════════════════════════════
rel_counts = df['Relation_Norm'].value_counts().head(12)
colors2    = make_colors(len(rel_counts))

fig, ax = plt.subplots(figsize=(12, 7))
bars2 = ax.barh(rel_counts.index[::-1], rel_counts.values[::-1],
                color=colors2[::-1], height=0.62,
                edgecolor='white', linewidth=0.8)

for bar, val in zip(bars2, rel_counts.values[::-1]):
    ax.text(bar.get_width() + 0.15,
            bar.get_y() + bar.get_height() / 2,
            f"{val}  ({val/len(df)*100:.1f}%)",
            va='center', ha='left', fontsize=10,
            fontweight='bold', color='#333333')

ax.set_title("Who is the Abuser? — Relation Distribution",
             fontsize=16, fontweight='bold', pad=18, color='#1a1a2e')
ax.set_xlabel('Number of Cases', fontsize=12, color='#444')
ax.set_xlim(0, rel_counts.max() + 22)
ax.tick_params(axis='y', labelsize=10)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_02_abuser_relation')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Trust Blind Spot (fixed: Son normalized)
# ══════════════════════════════════════════════════════════════════════════════
tbs_family = df['Trust_Blind_Spot'].sum()
tbs_other  = len(df) - tbs_family
tbs_labels = ['Family Member\n(Trust Blind Spot)', 'Non-Family\nAbuser']
tbs_vals   = [tbs_family, tbs_other]
tbs_colors = ['#E63946', '#2A9D8F']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

# Pie
wedges, texts, autos = ax1.pie(
    tbs_vals, labels=None, autopct='%1.1f%%',
    colors=tbs_colors, startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 3},
    pctdistance=0.70, explode=[0.05, 0])
for t in autos:
    t.set_fontsize(14)
    t.set_fontweight('bold')
    t.set_color('white')
ax1.legend(wedges,
           [f"{l}  (n={v})" for l, v in zip(tbs_labels, tbs_vals)],
           fontsize=11, loc='lower center',
           bbox_to_anchor=(0.5, -0.12), frameon=False)
ax1.set_title('Trust Blind Spot Overview', fontsize=14,
              fontweight='bold', pad=15)

# Bar — family members breakdown
family_rels = df[df['Trust_Blind_Spot'] == 1]['Relation_Norm'].value_counts().head(8)
fam_colors  = make_colors(len(family_rels))
ax2.barh(family_rels.index[::-1], family_rels.values[::-1],
         color=fam_colors[::-1], height=0.6, edgecolor='white')
for i, val in enumerate(family_rels.values[::-1]):
    ax2.text(val + 0.2, i, str(val), va='center',
             fontsize=10, fontweight='bold', color='#333333')
ax2.set_title('Family Abusers — Breakdown', fontsize=14,
              fontweight='bold', pad=15)
ax2.set_xlabel('Cases', fontsize=11)
ax2.set_xlim(0, family_rels.max() + 10)
ax2.grid(False)
ax2.spines['left'].set_color('#cccccc')
ax2.spines['bottom'].set_color('#cccccc')

fig.suptitle(
    f'Trust Blind Spot — {tbs_family/len(df)*100:.1f}% of Abusers are Family Members',
    fontsize=15, fontweight='bold', color='#1a1a2e', y=1.01)
plt.tight_layout()
save('chart_09_trust_blind_spot')


print()
print("=" * 50)
print("  DONE")
print("=" * 50)
print(f"  chart_02 updated (Son normalized)")
print(f"  chart_09 updated (Son normalized)")
print(f"  3 old files deleted")
