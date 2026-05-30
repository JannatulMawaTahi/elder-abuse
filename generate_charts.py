"""
Phase 1 — EDA Chart Generator
Generates all charts and saves to data/ folder.
Run: python generate_charts.py
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH  = r"d:\499 CAPSTONE\elder-abuse\data\Elder_abuse_Dataset.csv"
OUT_DIR    = r"d:\499 CAPSTONE\elder-abuse\data"
DPI        = 180
plt.rcParams.update({
    'font.family':     'DejaVu Sans',
    'font.size':       11,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'figure.facecolor':   'white',
    'axes.facecolor':     'white',
})

# ── Load & Normalize ──────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH, encoding='utf-8')

# Normalize Abuse Category
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

# Normalize Relation
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
    'Union Council Member': 'Govt. Official',
    'Police': 'Govt. Official',
}
df['Relation_Norm'] = df['Abuse Relation'].str.strip().replace(rel_map)
df['Relation_Norm'] = df['Relation_Norm'].fillna(df['Abuse Relation'].str.strip())

# Severity Score
severity_map = {
    'Murder': 5,
    'Financial + Murder': 5,
    'Physical Abuse': 4,
    'Financial + Physical': 4,
    'Physical + Abandonment': 4,
    'Financial + Physical + Abandonment': 4,
    'Physical + Neglect': 4,
    'Abandonment': 3,
    'Neglect + Abandonment': 3,
    'Financial + Abandonment': 3,
    'Financial Exploitation': 2,
    'Neglect': 2,
    'Financial + Neglect': 2,
    'Verbal Abuse': 1,
}
df['Severity_Score'] = df['Category_Norm'].map(severity_map).fillna(2)

# Trust Blind Spot
family_kw = ['son','daughter','spouse','husband','wife','child','nephew','grandchild']
df['Trust_Blind_Spot'] = df['Relation_Norm'].str.lower().str.contains(
    '|'.join(family_kw), na=False).astype(int)

# Age numeric
df['Age_Numeric'] = pd.to_numeric(df['Age'], errors='coerce')

# Year
df['Date_Parsed'] = pd.to_datetime(df['Date'].str.strip(), errors='coerce', dayfirst=True)
df['Year'] = df['Date_Parsed'].dt.year

print(f"Dataset loaded: {len(df)} rows")

# ── Palette helpers ───────────────────────────────────────────────────────────
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
    print(f"  [OK] {name}.png saved")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Abuse Category Distribution (horizontal, no overlap)
# ══════════════════════════════════════════════════════════════════════════════
counts = df['Category_Norm'].value_counts()
colors = make_colors(len(counts))

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(counts.index[::-1], counts.values[::-1],
               color=colors[::-1], height=0.65, edgecolor='white', linewidth=0.8)

for bar, val in zip(bars, counts.values[::-1]):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
            str(val), va='center', ha='left', fontsize=10, fontweight='bold',
            color='#333333')

ax.set_title('Abuse Category Distribution', fontsize=16, fontweight='bold',
             pad=18, color='#1a1a2e')
ax.set_xlabel('Number of Cases', fontsize=12, color='#444')
ax.set_xlim(0, counts.max() + 8)
ax.tick_params(axis='y', labelsize=10)
ax.tick_params(axis='x', labelsize=10)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_01_abuse_category')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Abuser Relation (different color each bar)
# ══════════════════════════════════════════════════════════════════════════════
rel_counts = df['Relation_Norm'].value_counts().head(12)
colors2 = make_colors(len(rel_counts))

fig, ax = plt.subplots(figsize=(12, 7))
bars2 = ax.barh(rel_counts.index[::-1], rel_counts.values[::-1],
                color=colors2[::-1], height=0.62, edgecolor='white', linewidth=0.8)

for bar, val in zip(bars2, rel_counts.values[::-1]):
    ax.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height() / 2,
            f"{val}  ({val/len(df)*100:.1f}%)",
            va='center', ha='left', fontsize=10, fontweight='bold', color='#333333')

ax.set_title('Who is the Abuser? — Relation Distribution', fontsize=16,
             fontweight='bold', pad=18, color='#1a1a2e')
ax.set_xlabel('Number of Cases', fontsize=12, color='#444')
ax.set_xlim(0, rel_counts.max() + 18)
ax.tick_params(axis='y', labelsize=10)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_02_abuser_relation')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — Top 15 Locations
# ══════════════════════════════════════════════════════════════════════════════
loc_col  = 'Location'
loc_counts = df[loc_col].str.strip().value_counts()
loc_counts = loc_counts[loc_counts.index.str.lower() != 'unknown'].head(15)
colors3  = make_colors(len(loc_counts))

fig, ax = plt.subplots(figsize=(12, 7))
bars3 = ax.bar(range(len(loc_counts)), loc_counts.values,
               color=colors3, edgecolor='white', linewidth=0.8, width=0.7)

for i, (bar, val) in enumerate(zip(bars3, loc_counts.values)):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
            str(val), ha='center', va='bottom', fontsize=9.5, fontweight='bold',
            color='#333333')

ax.set_xticks(range(len(loc_counts)))
ax.set_xticklabels(loc_counts.index, rotation=38, ha='right', fontsize=10)
ax.set_title('Top 15 Locations by Number of Cases', fontsize=16,
             fontweight='bold', pad=18, color='#1a1a2e')
ax.set_ylabel('Number of Cases', fontsize=12, color='#444')
ax.set_ylim(0, loc_counts.max() + 5)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_03_top15_locations')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — Gender Distribution (Pie)
# ══════════════════════════════════════════════════════════════════════════════
gen_counts = df['Gender'].str.strip().value_counts()
pie_colors = ['#457B9D', '#E63946', '#2A9D8F', '#E9C46A'][:len(gen_counts)]

fig, ax = plt.subplots(figsize=(8, 8))
wedges, texts, autotexts = ax.pie(
    gen_counts.values,
    labels=None,
    autopct='%1.1f%%',
    colors=pie_colors,
    startangle=140,
    pctdistance=0.75,
    wedgeprops={'edgecolor': 'white', 'linewidth': 2.5},
    explode=[0.04] * len(gen_counts),
)
for t in autotexts:
    t.set_fontsize(13)
    t.set_fontweight('bold')
    t.set_color('white')

legend_labels = [f"{g}  ({v})" for g, v in zip(gen_counts.index, gen_counts.values)]
ax.legend(wedges, legend_labels, title="Gender", title_fontsize=12,
          fontsize=11, loc='lower center', bbox_to_anchor=(0.5, -0.08),
          ncol=2, frameon=False)
ax.set_title('Victim Gender Distribution', fontsize=16, fontweight='bold',
             pad=20, color='#1a1a2e')
plt.tight_layout()
save('chart_04_gender_pie')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Severity Score Distribution
# ══════════════════════════════════════════════════════════════════════════════
sev_labels = {1: 'Verbal\n(Score 1)', 2: 'Financial/Neglect\n(Score 2)',
              3: 'Abandonment\n(Score 3)', 4: 'Physical\n(Score 4)',
              5: 'Murder\n(Score 5)'}
sev_counts = df['Severity_Score'].value_counts().sort_index()
sev_colors = ['#52B788', '#E9C46A', '#F4A261', '#E76F51', '#E63946']

fig, ax = plt.subplots(figsize=(10, 6))
bars5 = ax.bar([sev_labels[s] for s in sev_counts.index],
               sev_counts.values,
               color=[sev_colors[int(i)-1] for i in sev_counts.index],
               edgecolor='white', linewidth=1.2, width=0.6)

for bar, val in zip(bars5, sev_counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.4,
            f"{val}\n({val/len(df)*100:.1f}%)",
            ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='#333333')

ax.set_title('Severity Score Distribution', fontsize=16, fontweight='bold',
             pad=18, color='#1a1a2e')
ax.set_ylabel('Number of Cases', fontsize=12, color='#444')
ax.set_ylim(0, sev_counts.max() + 12)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_05_severity_score')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Age Distribution
# ══════════════════════════════════════════════════════════════════════════════
age_data = df['Age_Numeric'].dropna()

fig, ax = plt.subplots(figsize=(10, 6))
n, bins, patches = ax.hist(age_data, bins=12, edgecolor='white', linewidth=1.2,
                            color='#457B9D', alpha=0.9)

# Color gradient: younger=lighter, older=darker
cmap = plt.cm.Blues
for patch, val in zip(patches, n):
    patch.set_facecolor(cmap(0.35 + 0.55 * val / n.max()))

ax.axvline(age_data.mean(), color='#E63946', linestyle='--', linewidth=2,
           label=f'Mean: {age_data.mean():.1f} yrs')
ax.axvline(age_data.median(), color='#2A9D8F', linestyle='--', linewidth=2,
           label=f'Median: {age_data.median():.1f} yrs')

ax.set_title('Victim Age Distribution', fontsize=16, fontweight='bold',
             pad=18, color='#1a1a2e')
ax.set_xlabel('Age (years)', fontsize=12, color='#444')
ax.set_ylabel('Number of Cases', fontsize=12, color='#444')
ax.legend(fontsize=11, frameon=False)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_06_age_distribution')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Year-wise Trend
# ══════════════════════════════════════════════════════════════════════════════
year_counts = df['Year'].dropna().astype(int).value_counts().sort_index()
year_counts = year_counts[year_counts.index >= 2010]

fig, ax = plt.subplots(figsize=(12, 6))
ax.fill_between(year_counts.index, year_counts.values, alpha=0.18, color='#457B9D')
ax.plot(year_counts.index, year_counts.values, marker='o', markersize=8,
        color='#E63946', linewidth=2.5, markerfacecolor='white',
        markeredgecolor='#E63946', markeredgewidth=2.5)

for x, y in zip(year_counts.index, year_counts.values):
    ax.text(x, y + 0.4, str(y), ha='center', va='bottom', fontsize=10,
            fontweight='bold', color='#333333')

ax.set_title('Year-wise Case Trend (2010–2026)', fontsize=16, fontweight='bold',
             pad=18, color='#1a1a2e')
ax.set_xlabel('Year', fontsize=12, color='#444')
ax.set_ylabel('Number of Cases', fontsize=12, color='#444')
ax.set_xticks(year_counts.index)
ax.tick_params(axis='x', rotation=45)
ax.set_ylim(0, year_counts.max() + 4)
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_07_year_trend')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 8 — Heatmap: Abuse Category × Relation
# ══════════════════════════════════════════════════════════════════════════════
top_cats = df['Category_Norm'].value_counts().head(8).index.tolist()
top_rels = df['Relation_Norm'].value_counts().head(8).index.tolist()

heat_df = df[df['Category_Norm'].isin(top_cats) & df['Relation_Norm'].isin(top_rels)]
pivot   = heat_df.pivot_table(index='Category_Norm', columns='Relation_Norm',
                               aggfunc='size', fill_value=0)
pivot   = pivot.loc[[c for c in top_cats if c in pivot.index]]
pivot   = pivot[[c for c in top_rels if c in pivot.columns]]

fig, ax = plt.subplots(figsize=(13, 7))
cmap_heat = LinearSegmentedColormap.from_list('heat', ['#EAF4FB', '#457B9D', '#1D3557'])
im = ax.imshow(pivot.values, aspect='auto', cmap=cmap_heat)

ax.set_xticks(range(len(pivot.columns)))
ax.set_yticks(range(len(pivot.index)))
ax.set_xticklabels(pivot.columns, rotation=35, ha='right', fontsize=10)
ax.set_yticklabels(pivot.index, fontsize=10)

for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        if val > 0:
            text_color = 'white' if val > pivot.values.max() * 0.5 else '#1a1a2e'
            ax.text(j, i, str(val), ha='center', va='center',
                    fontsize=11, fontweight='bold', color=text_color)

cbar = plt.colorbar(im, ax=ax, shrink=0.8)
cbar.set_label('Number of Cases', fontsize=11)
ax.set_title('Heatmap — Abuse Category × Abuser Relation', fontsize=16,
             fontweight='bold', pad=18, color='#1a1a2e')
plt.tight_layout()
save('chart_08_heatmap_cat_relation')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 9 — Trust Blind Spot
# ══════════════════════════════════════════════════════════════════════════════
tbs_family  = df['Trust_Blind_Spot'].sum()
tbs_other   = len(df) - tbs_family
tbs_labels  = ['Family Member\n(Trust Blind Spot)', 'Non-Family\nAbuser']
tbs_vals    = [tbs_family, tbs_other]
tbs_colors  = ['#E63946', '#2A9D8F']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

# Pie
wedges, texts, autos = ax1.pie(
    tbs_vals, labels=None, autopct='%1.1f%%',
    colors=tbs_colors, startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 3},
    pctdistance=0.70, explode=[0.05, 0])
for t in autos:
    t.set_fontsize(14); t.set_fontweight('bold'); t.set_color('white')
ax1.legend(wedges, [f"{l}  (n={v})" for l, v in zip(tbs_labels, tbs_vals)],
           fontsize=11, loc='lower center', bbox_to_anchor=(0.5, -0.12),
           frameon=False)
ax1.set_title('Trust Blind Spot Overview', fontsize=14, fontweight='bold', pad=15)

# Bar by relation — family members only
family_rels = df[df['Trust_Blind_Spot'] == 1]['Relation_Norm'].value_counts().head(8)
fam_colors  = make_colors(len(family_rels))
ax2.barh(family_rels.index[::-1], family_rels.values[::-1],
         color=fam_colors[::-1], height=0.6, edgecolor='white')
for i, (idx, val) in enumerate(zip(family_rels.index[::-1], family_rels.values[::-1])):
    ax2.text(val + 0.2, i, str(val), va='center', fontsize=10, fontweight='bold')
ax2.set_title('Family Abusers — Breakdown', fontsize=14, fontweight='bold', pad=15)
ax2.set_xlabel('Cases', fontsize=11)
ax2.set_xlim(0, family_rels.max() + 8)
ax2.grid(False)
ax2.spines['left'].set_color('#cccccc')
ax2.spines['bottom'].set_color('#cccccc')

fig.suptitle(f'Trust Blind Spot Analysis — {tbs_family/len(df)*100:.1f}% of Abusers are Family Members',
             fontsize=15, fontweight='bold', color='#1a1a2e', y=1.01)
plt.tight_layout()
save('chart_09_trust_blind_spot')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 10 — Data Source Type
# ══════════════════════════════════════════════════════════════════════════════
src_counts = df['Data Type'].str.strip().value_counts()
src_colors = ['#457B9D', '#2A9D8F', '#E63946'][:len(src_counts)]

fig, ax = plt.subplots(figsize=(8, 8))
wedges2, texts2, autos2 = ax.pie(
    src_counts.values, labels=None, autopct='%1.1f%%',
    colors=src_colors, startangle=140,
    wedgeprops={'edgecolor': 'white', 'linewidth': 3},
    pctdistance=0.72, explode=[0.04]*len(src_counts))
for t in autos2:
    t.set_fontsize(13); t.set_fontweight('bold'); t.set_color('white')

legend2 = [f"{s}  (n={v})" for s, v in zip(src_counts.index, src_counts.values)]
ax.legend(wedges2, legend2, fontsize=11, loc='lower center',
          bbox_to_anchor=(0.5, -0.1), frameon=False, ncol=1)
ax.set_title('Data Source Type Distribution', fontsize=16, fontweight='bold',
             pad=20, color='#1a1a2e')
plt.tight_layout()
save('chart_10_data_source_type')


# ══════════════════════════════════════════════════════════════════════════════
# CHART 11 — Severity by Gender (grouped bar)
# ══════════════════════════════════════════════════════════════════════════════
sev_gender = df.groupby(['Severity_Score', 'Gender']).size().unstack(fill_value=0)
sev_gender = sev_gender.reindex(sorted(sev_gender.index))

gender_colors = {'Male': '#457B9D', 'Female': '#E63946', 'Male & Female': '#2A9D8F'}
x = np.arange(len(sev_gender.index))
width = 0.25
cols  = [c for c in sev_gender.columns if c in gender_colors]

fig, ax = plt.subplots(figsize=(11, 6))
for i, col in enumerate(cols):
    offset = (i - len(cols)/2 + 0.5) * width
    bars_g = ax.bar(x + offset, sev_gender[col], width,
                    label=col, color=gender_colors[col],
                    edgecolor='white', linewidth=0.8)
    for bar in bars_g:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.15,
                    str(int(h)), ha='center', va='bottom', fontsize=9, fontweight='bold')

sev_xlabels = {1:'Verbal\n(1)', 2:'Financial\n/Neglect (2)',
               3:'Abandonment\n(3)', 4:'Physical\n(4)', 5:'Murder\n(5)'}
ax.set_xticks(x)
ax.set_xticklabels([sev_xlabels.get(s, str(s)) for s in sev_gender.index], fontsize=10)
ax.set_title('Severity Score by Gender', fontsize=16, fontweight='bold',
             pad=18, color='#1a1a2e')
ax.set_ylabel('Number of Cases', fontsize=12, color='#444')
ax.legend(fontsize=11, frameon=False, loc='upper right')
ax.grid(False)
ax.spines['left'].set_color('#cccccc')
ax.spines['bottom'].set_color('#cccccc')
plt.tight_layout()
save('chart_11_severity_by_gender')


# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 52)
print("  ALL CHARTS GENERATED SUCCESSFULLY")
print("=" * 52)
print(f"  Saved to: {OUT_DIR}")
print()
charts = [
    "chart_01_abuse_category",
    "chart_02_abuser_relation",
    "chart_03_top15_locations",
    "chart_04_gender_pie",
    "chart_05_severity_score",
    "chart_06_age_distribution",
    "chart_07_year_trend",
    "chart_08_heatmap_cat_relation",
    "chart_09_trust_blind_spot",
    "chart_10_data_source_type",
    "chart_11_severity_by_gender",
]
for c in charts:
    print(f"  [OK] {c}.png")
