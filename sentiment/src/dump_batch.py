# -*- coding: utf-8 -*-
"""Print a batch of comments (comment_id <TAB> single-line comment) for LLM labelling.
Usage: python dump_batch.py START COUNT      (START is 1-based row number in cleaned.csv)
"""
import sys, io, re
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "interim" / "cleaned.csv", dtype=str, keep_default_na=False)

start = int(sys.argv[1]); count = int(sys.argv[2])
batch = df.iloc[start - 1: start - 1 + count]
for _, r in batch.iterrows():
    txt = re.sub(r"\s+", " ", r["Comment"]).strip()[:350]
    print(f"{r['comment_id']}\t{txt}")
print(f"# rows {start}..{start+len(batch)-1}  (returned {len(batch)})", file=sys.stderr)
