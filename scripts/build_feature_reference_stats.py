"""
Phase D -- build the human-reference feature statistics the evidence
mapper compares an essay's observed feature values against (e.g. "this
essay's vocabulary diversity is higher than typical human writing in
the reference data").

This is NOT a model and NOT a fit: it is descriptive statistics (mean,
std) of already-frozen, already-tracked feature values --
experiments/EXP-003A/features.jsonl's TRAIN-split human rows -- exactly
the same category of action as GEN-001's/FAIR-001's feature-distribution
tables (mean/std per group), just persisted once as a small artifact
instead of recomputed inline in a report. No retraining, no new
fitting, no new data.

Only the TRAIN split is used (not validation/test) to keep this
consistent with "the frozen model was fit on train, so the reference
distribution it should be compared against is also train" -- and to
avoid any appearance of using test data for anything beyond its one
already-completed evaluation.

Output: backend/app/ml/feature_reference_stats.json (small, human-
readable -- unlike the .joblib model artifacts, there is no reason to
gitignore this one; it is transparent descriptive statistics of
already-public tracked data, not a scored model. Kept ignored anyway
for consistency with the other build artifacts and to keep the build
step as the single source of truth -- see docs/production-detector.md).
"""

import json
import sys
from pathlib import Path
from statistics import mean, stdev

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import ALL_FIELDS  # noqa: E402

FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
OUTPUT_PATH = REPO_ROOT / "backend" / "app" / "ml" / "feature_reference_stats.json"


def main() -> None:
    records = [json.loads(line) for line in FEATURES_PATH.read_text().splitlines() if line.strip()]
    human_train = [r for r in records if r["label"] == "human" and r["split"] == "train"]
    print(f"Computing reference stats from {len(human_train)} human TRAIN-split essays (EXP-003A).")

    stats = {}
    for f in ALL_FIELDS:
        values = [r[f] for r in human_train if r[f] is not None]
        stats[f] = {
            "mean": mean(values),
            "std": stdev(values) if len(values) > 1 else 0.0,
            "n": len(values),
        }

    output = {
        "source_experiment": "EXP-003A",
        "source_split": "train",
        "source_population": "human",
        "n_essays": len(human_train),
        "reference_stats_path": "experiments/EXP-003A/features.jsonl",
        "fields": stats,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"Wrote reference stats to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
