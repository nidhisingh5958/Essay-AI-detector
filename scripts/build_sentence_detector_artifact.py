"""
Phase B -- build the production sentence-localization detector artifact.

Reproduces, exactly, the model EXP-003B's top1_localization block fit
(scripts/run_exp003b.py, the block immediately after
results["sentence_level"] is computed): StandardScaler + LogisticRegressionCV
fit on the sentence-level feature file's TRAIN split, positive_label=
"ai_assisted", the full 29-field ALL_FIELDS set (the group EXP-003B-R1
found outperforms every ablation for the top-1 metric specifically --
length/count features matter here, unlike essay-level classification).

This is the model used ONLY for ranking (predict_proba, sentences
sorted by score within an essay) -- never for a per-sentence binary
decision. EXP-003B's own run_evaluation() fits a mathematically
IDENTICAL model on the same data for its own separate threshold-based
P/R/F1 report (same train split, same fields, same seed = same fit) --
this script's refit is verified against BOTH recorded figures, not
just one, as a stronger check.

Verification performed before writing the artifact:
1. Refit chosen_C matches results.json's sentence_level.primary_combined_logreg
   value exactly.
2. Refit model reproduces EXP-003B's recorded top1_localization TEST
   accuracy exactly (9/15 correct, 60.0%) using the same
   top1_localization_accuracy computation already validated in
   run_exp003b.py.

Output: backend/app/ml/sentence_detector_v1.joblib (gitignored -- see
docs/production-detector.md).
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import ALL_FIELDS, RANDOM_SEED, fit_logreg_cv  # noqa: E402
from run_exp003b import to_xy, top1_localization_accuracy  # noqa: E402

SENTENCE_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "results.json"
ARTIFACT_PATH = REPO_ROOT / "backend" / "app" / "ml" / "sentence_detector_v1.joblib"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    exp003b_results = json.loads(RESULTS_PATH.read_text())
    sl = exp003b_results["sentence_level"]
    frozen_C = sl["primary_combined_logreg"]["chosen_C"]
    recorded_top1 = sl["top1_localization"]["test"]

    sentence_records = load_jsonl(SENTENCE_FEATURES_PATH)
    train = [r for r in sentence_records if r["split"] == "train"]

    X_train, y_train = to_xy(train, ALL_FIELDS, "ai_assisted")
    scaler = StandardScaler().fit(X_train)
    Xs_train = scaler.transform(X_train)
    model = fit_logreg_cv(Xs_train, y_train, seed=RANDOM_SEED)

    # --- Verification 1: chosen_C reproduction ---
    if not np.isclose(model.C_[0], frozen_C):
        raise RuntimeError(
            f"STOP: refit chosen_C ({model.C_[0]}) does not match EXP-003B's recorded sentence_level value ({frozen_C})."
        )
    print(f"Verification 1 passed: chosen_C={model.C_[0]} matches recorded value.")

    # --- Verification 2: top-1 localization test accuracy reproduction ---
    result = top1_localization_accuracy(sentence_records, model, scaler, "test")
    if result != recorded_top1:
        raise RuntimeError(
            f"STOP: refit top1_localization test result {result} does not match recorded value {recorded_top1}."
        )
    print(f"Verification 2 passed: top1_localization test result reproduces exactly: {result}")

    artifact = {
        "scaler": scaler,
        "model": model,
        "feature_order": list(ALL_FIELDS),
        "chosen_C": float(model.C_[0]),
        "source_experiment": "EXP-003B",
        "model_version": "sentence-detector-v1-2026-08-15",
        "reference_results_path": "experiments/EXP-003B/results.json",
        "random_seed": RANDOM_SEED,
        "usage": "ranking_only -- no per-sentence threshold; EXP-003B's own raw 0.34 threshold is degenerate and must never be used for a binary per-sentence label",
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, ARTIFACT_PATH)
    print(f"\nWrote verified sentence-localization detector artifact to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
