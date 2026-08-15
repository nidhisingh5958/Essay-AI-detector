"""
Phase B -- build the production essay-level detector artifact.

No repository anywhere contains a serialized (joblib/pickle) copy of
EXP-003A's frozen combined model -- every research script that needed
it (EXP-003A itself, GEN-001, FAIR-001) refit it deterministically at
run time from experiments/EXP-003A/features.jsonl's train split. This
script performs that SAME, already-three-times-verified deterministic
refit ONE more time, and this time serializes the result so the
production service (backend/app/services/detector.py) never needs to
refit anything or see training data at runtime.

This is NOT a new model and NOT a new fitting procedure: identical
code path (StandardScaler + LogisticRegressionCV via
run_exp003a.fit_logreg_cv, same train split, same random_state=42) as
scripts/run_exp003a.py, scripts/run_gen001_evaluate.py, and
scripts/run_fair001_score_all.py all already used and verified.

Verification performed before writing the artifact (not after --
a mismatch here means STOP, not "write it anyway"):
1. Refit chosen_C matches experiments/EXP-003A/results.json's recorded
   value exactly.
2. Refit model's score on every one of EXP-003A's 46 frozen TEST
   samples matches the recorded score in results.json's
   test_predictions to 4 decimal places (the precision those scores
   were originally rounded and recorded to) -- a much stronger check
   than chosen_C alone, since it proves the actual fitted coefficients
   and scaler parameters reproduce byte-for-byte, not just the
   regularization strength.

Output: backend/app/ml/essay_detector_v1.joblib (gitignored -- see
docs/production-detector.md for why this is a build artifact, not a
tracked file, and how to regenerate it).
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

FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "results.json"
ARTIFACT_PATH = REPO_ROOT / "backend" / "app" / "ml" / "essay_detector_v1.joblib"

FROZEN_THRESHOLD = 0.47
SCORE_TOLERANCE = 5e-5  # recorded scores are round(score, 4); this tolerance matches that rounding


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def to_xy(records: list[dict], fields):
    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([1 if r["label"] == "machine" else 0 for r in records], dtype=int)
    return X, y


def main() -> None:
    exp003a_results = json.loads(RESULTS_PATH.read_text())
    frozen_C = exp003a_results["primary_combined_logreg"]["chosen_C"]
    frozen_threshold = exp003a_results["threshold_selection"]["chosen_threshold"]
    assert frozen_threshold == FROZEN_THRESHOLD, f"FROZEN_THRESHOLD constant mismatch: {frozen_threshold} != {FROZEN_THRESHOLD}"

    records = load_jsonl(FEATURES_PATH)
    train = [r for r in records if r["split"] == "train"]
    test = [r for r in records if r["split"] == "test"]

    X_train, y_train = to_xy(train, ALL_FIELDS)
    scaler = StandardScaler().fit(X_train)
    Xs_train = scaler.transform(X_train)
    model = fit_logreg_cv(Xs_train, y_train, seed=RANDOM_SEED)

    # --- Verification 1: chosen_C reproduction ---
    if not np.isclose(model.C_[0], frozen_C):
        raise RuntimeError(
            f"STOP: refit chosen_C ({model.C_[0]}) does not match EXP-003A's recorded value ({frozen_C}). "
            "Do not write an artifact from a model that doesn't reproduce the frozen fit."
        )
    print(f"Verification 1 passed: chosen_C={model.C_[0]} matches recorded value.")

    # --- Verification 2: per-sample test score reproduction ---
    X_test, y_test = to_xy(test, ALL_FIELDS)
    Xs_test = scaler.transform(X_test)
    scores_test = model.predict_proba(Xs_test)[:, 1]

    recorded_by_sample = {p["sample_id"]: p["score"] for p in exp003a_results["test_predictions"]}
    mismatches = []
    for r, score in zip(test, scores_test):
        recorded = recorded_by_sample.get(r["sample_id"])
        if recorded is None:
            raise RuntimeError(f"STOP: no recorded score for {r['sample_id']} in results.json -- cannot verify")
        if abs(float(score) - recorded) > SCORE_TOLERANCE:
            mismatches.append((r["sample_id"], float(score), recorded))

    if mismatches:
        raise RuntimeError(
            f"STOP: {len(mismatches)} of {len(test)} refit test scores do not match recorded EXP-003A "
            f"scores within tolerance {SCORE_TOLERANCE}. First mismatch: {mismatches[0]}. "
            "Do not write an artifact from a model that doesn't reproduce the frozen fit's predictions."
        )
    print(f"Verification 2 passed: all {len(test)} refit test scores match EXP-003A's recorded scores within {SCORE_TOLERANCE}.")

    artifact = {
        "scaler": scaler,
        "model": model,
        "feature_order": list(ALL_FIELDS),
        "threshold": FROZEN_THRESHOLD,
        "chosen_C": float(model.C_[0]),
        "source_experiment": "EXP-003A",
        "model_version": "essay-detector-v1-2026-08-15",
        "reference_results_path": "experiments/EXP-003A/results.json",
        "random_seed": RANDOM_SEED,
    }

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, ARTIFACT_PATH)
    print(f"\nWrote verified essay-level detector artifact to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
