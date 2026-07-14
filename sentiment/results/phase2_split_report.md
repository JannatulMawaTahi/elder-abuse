# Phase 2 — Dataset Split Report (sentiment / polarity)

- Labelled comments loaded: **2301**
- Removed as duplicate text (final dedup): **2**
- After dedup: **2299**
- Split: **70/15/15**, stratified by polarity, SEED=42
- Test set **locked** (`data/splits/test_lock.json`, sha256 `eada381baf811074…`).
- `emotion` column preserved in every split (deferred target).

## Polarity distribution per split

| Split | N | Negative | Neutral | Positive |
|---|---|---|---|---|
| Overall | 2299 | 1618 (70.4%) | 511 (22.2%) | 170 (7.4%) |
| Train | 1609 | 1132 (70.4%) | 358 (22.2%) | 119 (7.4%) |
| Val | 345 | 243 (70.4%) | 76 (22.0%) | 26 (7.5%) |
| Test | 345 | 243 (70.4%) | 77 (22.3%) | 25 (7.2%) |

Stratification keeps the polarity ratios near-identical across splits, so the locked test set is representative and there is no class-balance leakage.

## Files
- `data/splits/train.csv` · `val.csv` · `test.csv` (all original columns kept)
- `data/splits/test_lock.json` (id list + hash)
- `results/phase2_split.json` (machine-readable numbers)