# -*- coding: utf-8 -*-
"""
Apply the Victim-blaming audit corrections to the emotion labels.

Only the `emotion` column is changed (polarity is left untouched, so the locked
test set and the polarity models are unaffected — emotion is a deferred axis).

Corrections were made by reading every one of the 310 Victim-blaming comments and
keeping the codebook rule: blaming the elder/parent/their past/upbringing/society
for their suffering = Victim-blaming (STAYS). Only move a comment out when it:
  - condemns/curses the ABUSER or a third party (not the victim) -> Anger/Condemnation
  - is generic advice/observation with NO blame directed at the victim -> Neutral-Other

Writes back annotated/llm_labels.csv and propagates the same emotion fix into
data/splits/{train,val,test}.csv by comment_id. Emits a changelog report.
"""
import sys, io
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "annotated" / "llm_labels.csv"
SPLITS = ROOT / "data" / "splits"
RES = ROOT / "results"

# comment_id -> (new_emotion, reason)
FIX = {
    # --- condemns the abuser / a third party, NOT the elderly victim -> Anger ---
    "C00234": ("Anger/Condemnation", "calls the abusers 'poison of society' — condemns abuser, not victim"),
    "C00268": ("Anger/Condemnation", "condemns ungrateful educated children who fail to respect parents"),
    "C00705": ("Anger/Condemnation", "'dhikkar' (denunciation) of the neglectful educated society/children"),
    "C01609": ("Anger/Condemnation", "expresses hatred ('ghrina kori') toward wives/women — third party"),
    # --- generic advice / observation, no blame directed at the victim -> Neutral-Other ---
    "C00228": ("Neutral-Other", "generic opinion: 'all education without religion is worthless'"),
    "C00700": ("Neutral-Other", "general observation: no poor person's parents are in old-age homes"),
    "C01428": ("Neutral-Other", "cynical generalization about educating girls; no victim blame"),
    "C00683": ("Neutral-Other", "generic advice: everyone needs Islamic education / legal income"),
    "C00181": ("Neutral-Other", "generic advice: parents should raise children per Surah Luqman"),
    "C00993": ("Neutral-Other", "generic advice to give children Islamic education (+ insha'Allah)"),
    "C00310": ("Neutral-Other", "pure imperative advice: 'religious education must be given'"),
    "C00432": ("Neutral-Other", "pure advice: Islamic / Quranic knowledge is needed"),
    "C00259": ("Neutral-Other", "opinion: making a good human matters more than making one educated"),
    "C00436": ("Neutral-Other", "advice: give moral education, not just academic"),
    "C00077": ("Neutral-Other", "advice: Islamic / justice education is very important"),
    "C00255": ("Neutral-Other", "general lesson: understand the halal-haram distinction"),
    "C01054": ("Neutral-Other", "generic advice on raising children religiously + sympathy for the mother"),
}
OLD = "Victim-blaming"


def main() -> None:
    df = pd.read_csv(SRC, dtype=str, keep_default_na=False)
    idx = df.set_index("comment_id")

    # validate all targets currently Victim-blaming
    bad = [c for c in FIX if c not in idx.index or idx.loc[c, "emotion"] != OLD]
    if bad:
        sys.exit(f"Aborting — these ids are not currently '{OLD}': {bad}")

    log = []
    m = df["comment_id"].isin(FIX)
    for c, (new, reason) in FIX.items():
        df.loc[df["comment_id"] == c, "emotion"] = new
        log.append((c, new, reason))
    df.to_csv(SRC, index=False, encoding="utf-8")

    # propagate into the splits (emotion only; polarity untouched)
    touched = {}
    for name in ("train", "val", "test"):
        p = SPLITS / f"{name}.csv"
        if not p.exists():
            continue
        s = pd.read_csv(p, dtype=str, keep_default_na=False)
        n = 0
        for c, (new, _) in FIX.items():
            hit = s["comment_id"] == c
            if hit.any():
                s.loc[hit, "emotion"] = new
                n += int(hit.sum())
        s.to_csv(p, index=False, encoding="utf-8")
        touched[name] = n

    # report
    counts = df["emotion"].value_counts()
    lines = ["# Victim-blaming audit — applied corrections", "",
             f"Reviewed all { (df['emotion'].isin([OLD])).sum() + len(FIX)} originally-Victim-blaming comments; "
             f"corrected **{len(FIX)}** (emotion only, polarity unchanged).", "",
             "| comment_id | Victim-blaming → | reason |", "|---|---|---|"]
    for c, new, reason in log:
        lines.append(f"| {c} | {new} | {reason} |")
    lines += ["", "## Emotion distribution after fix", "",
              "| emotion | count |", "|---|---|"]
    for e, n in counts.items():
        lines.append(f"| {e} | {n} |")
    lines += ["", f"Splits updated (emotion only): "
              + ", ".join(f"{k} {v}" for k, v in touched.items()) + ".",
              "", "> Polarity was intentionally left unchanged so the locked test set and the "
              "polarity models are unaffected. A separate polarity re-audit can follow if needed."]
    (RES / "victimblame_audit_applied.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Applied {len(FIX)} emotion corrections.")
    print("New emotion counts:")
    print(counts.to_string())
    print(f"\nSplits updated: {touched}")
    print(f"Report: results/victimblame_audit_applied.md")


if __name__ == "__main__":
    main()
