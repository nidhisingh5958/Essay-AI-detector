"""
FAIR-001 -- Stage 1: score ALL 150 families (not just the frozen test
split) using the already-frozen EXP-003A and EXP-003B essay-level
models, unchanged. Per DEC-018/FAIR-001.md: this is inference-only
re-application of an already-fitted, already-frozen model -- it does
NOT retrain, tune, or reselect anything. Scaler + model are refit
deterministically from the exact same train split/seed/code path as
run_exp003a.py / run_exp003b.py, and the refit is verified to reproduce
the recorded chosen_C/threshold values exactly before scoring anything.

This is necessary new code (not new model development) because
EXP-003A/B's results.json only ever persisted TEST-split predictions --
scoring train+validation rows too is what raises the `ell_status=Yes`
subgroup from 1 (test-only) to 10 (all 150 families).

No demographic attribute is read, joined, or used anywhere in this
script -- it only reads feature vectors and labels, exactly like
run_exp003a.py/run_exp003b.py do. The fairness join happens in a
separate script (run_fair001_fairness_analysis.py).

Output:
  experiments/FAIR-001/scored_exp003a_all_families.jsonl
  experiments/FAIR-001/scored_exp003b_essay_all_families.jsonl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import ALL_FIELDS, RANDOM_SEED, fit_logreg_cv  # noqa: E402
from run_exp003b import to_xy as to_xy_b  # noqa: E402

EXP003A_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
EXP003A_RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "results.json"
EXP003B_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl"
EXP003B_RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "results.json"

OUTPUT_DIR = REPO_ROOT / "experiments" / "FAIR-001"

EXP003A_FROZEN_THRESHOLD = 0.47
EXP003B_ESSAY_FROZEN_THRESHOLD = 0.34


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def to_xy_a(records: list[dict], fields: list[str]):
    import numpy as np

    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([1 if r["label"] == "machine" else 0 for r in records], dtype=int)
    return X, y


def score_exp003a_all() -> list[dict]:
    from sklearn.preprocessing import StandardScaler

    exp003a_results = json.loads(EXP003A_RESULTS_PATH.read_text())
    frozen_C = exp003a_results["primary_combined_logreg"]["chosen_C"]
    frozen_threshold = exp003a_results["threshold_selection"]["chosen_threshold"]
    assert frozen_threshold == EXP003A_FROZEN_THRESHOLD, (
        f"EXP003A_FROZEN_THRESHOLD constant ({EXP003A_FROZEN_THRESHOLD}) does not match "
        f"results.json ({frozen_threshold}) -- stop, do not proceed with a mismatched value"
    )

    records = load_jsonl(EXP003A_FEATURES_PATH)
    train = [r for r in records if r["split"] == "train"]

    X_train, y_train = to_xy_a(train, ALL_FIELDS)
    scaler = StandardScaler().fit(X_train)
    model = fit_logreg_cv(scaler.transform(X_train), y_train, seed=RANDOM_SEED)

    import numpy as np

    assert np.isclose(model.C_[0], frozen_C), (
        f"Refit chosen_C ({model.C_[0]}) does not match EXP-003A's frozen value ({frozen_C}) -- stop"
    )
    print(f"EXP-003A reproduction check passed: chosen_C={model.C_[0]}, frozen_threshold={frozen_threshold}")

    X_all, y_all = to_xy_a(records, ALL_FIELDS)
    scores = model.predict_proba(scaler.transform(X_all))[:, 1]

    scored = []
    for r, y, score in zip(records, y_all, scores):
        pred_label = "machine" if score >= frozen_threshold else "human"
        scored.append({
            "sample_id": r["sample_id"], "family_id": r["family_id"], "split": r["split"],
            "true_label": r["label"], "predicted_label": pred_label,
            "score": round(float(score), 4),
            "correct": pred_label == r["label"],
            "false_positive": r["label"] == "human" and pred_label == "machine",
            "false_negative": r["label"] == "machine" and pred_label == "human",
        })
    return scored


def score_exp003b_essay_all() -> list[dict]:
    from sklearn.preprocessing import StandardScaler

    exp003b_results = json.loads(EXP003B_RESULTS_PATH.read_text())
    el = exp003b_results["essay_level"]
    frozen_C = el["primary_combined_logreg"]["chosen_C"]
    frozen_threshold = el["threshold_selection"]["chosen_threshold"]
    assert frozen_threshold == EXP003B_ESSAY_FROZEN_THRESHOLD, (
        f"EXP003B_ESSAY_FROZEN_THRESHOLD constant ({EXP003B_ESSAY_FROZEN_THRESHOLD}) does not match "
        f"results.json ({frozen_threshold}) -- stop, do not proceed with a mismatched value"
    )

    records = load_jsonl(EXP003B_FEATURES_PATH)
    train = [r for r in records if r["split"] == "train"]

    X_train, y_train = to_xy_b(train, ALL_FIELDS, "ai_assisted")
    scaler = StandardScaler().fit(X_train)
    model = fit_logreg_cv(scaler.transform(X_train), y_train, seed=RANDOM_SEED)

    import numpy as np

    assert np.isclose(model.C_[0], frozen_C), (
        f"Refit chosen_C ({model.C_[0]}) does not match EXP-003B essay-level's frozen value ({frozen_C}) -- stop"
    )
    print(f"EXP-003B essay-level reproduction check passed: chosen_C={model.C_[0]}, frozen_threshold={frozen_threshold}")

    X_all, y_all = to_xy_b(records, ALL_FIELDS, "ai_assisted")
    scores = model.predict_proba(scaler.transform(X_all))[:, 1]

    scored = []
    for r, y, score in zip(records, y_all, scores):
        pred_label = "ai_assisted" if score >= frozen_threshold else "human"
        scored.append({
            "sample_id": r["sample_id"], "family_id": r["family_id"], "split": r["split"],
            "true_label": r["label"], "predicted_label": pred_label,
            "score": round(float(score), 4),
            "correct": pred_label == r["label"],
            "false_positive": r["label"] == "human" and pred_label == "ai_assisted",
            "false_negative": r["label"] == "ai_assisted" and pred_label == "human",
        })
    return scored


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scored_a = score_exp003a_all()
    print(f"Scored {len(scored_a)} EXP-003A (human vs full_ai) records across all splits.")
    n_families_a = len({r["family_id"] for r in scored_a})
    print(f"  covers {n_families_a} distinct families")
    (OUTPUT_DIR / "scored_exp003a_all_families.jsonl").write_text(
        "\n".join(json.dumps(r) for r in scored_a) + "\n"
    )

    scored_b = score_exp003b_essay_all()
    print(f"Scored {len(scored_b)} EXP-003B essay-level (human vs ai_assisted) records across all splits.")
    n_families_b = len({r["family_id"] for r in scored_b})
    print(f"  covers {n_families_b} distinct families")
    (OUTPUT_DIR / "scored_exp003b_essay_all_families.jsonl").write_text(
        "\n".join(json.dumps(r) for r in scored_b) + "\n"
    )

    print(f"\nWrote scored predictions to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
