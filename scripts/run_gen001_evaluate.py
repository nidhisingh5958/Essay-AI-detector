"""
GEN-001 -- Stage 3: evaluation. Applies the already-frozen EXP-003A
detector (scaler + L2 logistic regression + threshold, refit
deterministically from the exact same train split/seed/code path used in
run_exp003a.py -- reproducing byte-identical parameters, not retraining
on anything new) to the held-out Phi-3.5-mini-instruct essays.

HARD CONSTRAINT (GEN-001 / DEC-019): the Phi data is evaluation-only.
Nothing about the model, scaler, features, or threshold is fit, tuned,
or selected using Phi data anywhere in this file. The only thing Phi
data is used for is prediction and post-hoc descriptive analysis.

Reads:
  experiments/EXP-003A/features.jsonl  (Qwen train/validation/test + human)
  experiments/EXP-003A/results.json    (frozen threshold, frozen chosen_C
                                         values, for a reproduction check)
  experiments/GEN-001/features_phi.jsonl (held-out Phi full_ai features)

Writes:
  experiments/GEN-001/results.json
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import (  # noqa: E402
    ALL_FIELDS,
    LM_FIELDS,
    RANDOM_SEED,
    STYLO_FIELDS,
    fit_logreg_cv,
    metrics_at_threshold,
)
from run_exp003b_r1 import LM_PREDICTABILITY_NON_COUNT  # noqa: E402

EXP003A_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
EXP003A_RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "results.json"
PHI_FEATURES_PATH = REPO_ROOT / "experiments" / "GEN-001" / "features_phi.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "GEN-001" / "results.json"

# The already-frozen EXP-003A decision threshold (chosen on Qwen's
# validation split only, before EXP-003A's test set -- Qwen or Phi -- was
# ever touched). Not reselected here. Verified against results.json at
# runtime (see verify_reproduction).
FROZEN_THRESHOLD = 0.47


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def to_xy(records: list[dict], fields: list[str]):
    import numpy as np

    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([1 if r["label"] == "machine" else 0 for r in records], dtype=int)
    return X, y


def check_missingness(records: list[dict], fields: list[str]) -> dict:
    missing = {}
    for f in fields:
        n_missing = sum(1 for r in records if r.get(f) is None)
        if n_missing:
            missing[f] = n_missing
    return missing


def main() -> None:
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    exp003a_results = json.loads(EXP003A_RESULTS_PATH.read_text())
    assert exp003a_results["threshold_selection"]["chosen_threshold"] == FROZEN_THRESHOLD, (
        "FROZEN_THRESHOLD does not match EXP-003A's recorded chosen_threshold -- stop, do not proceed with a mismatched value"
    )

    qwen_records = load_jsonl(EXP003A_FEATURES_PATH)
    train = [r for r in qwen_records if r["split"] == "train"]
    qwen_test = [r for r in qwen_records if r["split"] == "test"]
    print(f"Loaded EXP-003A features: train={len(train)}, test={len(qwen_test)}")

    phi_records = load_jsonl(PHI_FEATURES_PATH)
    print(f"Loaded {len(phi_records)} Phi held-out records")

    missing = check_missingness(phi_records, ALL_FIELDS)
    if missing:
        raise RuntimeError(f"Missing feature values in Phi records -- stop and report, do not silently exclude: {missing}")

    # ---- Refit scaler + models on TRAIN ONLY (exact same code path as run_exp003a.py). ----
    # This is a deterministic reproduction of the already-frozen EXP-003A
    # models, not a new fit against anything Phi-related.
    X_train_all, y_train = to_xy(train, ALL_FIELDS)
    scaler = StandardScaler().fit(X_train_all)
    Xs_train_all = scaler.transform(X_train_all)

    field_idx = {f: i for i, f in enumerate(ALL_FIELDS)}

    def subset(X, fields):
        idx = [field_idx[f] for f in fields]
        return X[:, idx]

    model_combined = fit_logreg_cv(Xs_train_all, y_train, seed=RANDOM_SEED)
    model_stylo = fit_logreg_cv(subset(Xs_train_all, STYLO_FIELDS), y_train, seed=RANDOM_SEED)
    model_lm = fit_logreg_cv(subset(Xs_train_all, LM_FIELDS), y_train, seed=RANDOM_SEED)

    # ---- Reproduction check: refit chosen_C must exactly match EXP-003A's recorded values. ----
    reproduction_check = {
        "combined_chosen_C_matches": bool(
            np.isclose(model_combined.C_[0], exp003a_results["primary_combined_logreg"]["chosen_C"])
        ),
        "stylometric_chosen_C_matches": bool(
            np.isclose(model_stylo.C_[0], exp003a_results["baseline_B_stylometric_only"]["chosen_C"])
        ),
        "lm_chosen_C_matches": bool(
            np.isclose(model_lm.C_[0], exp003a_results["baseline_C_lm_only"]["chosen_C"])
        ),
    }
    if not all(reproduction_check.values()):
        raise RuntimeError(f"Refit models do not reproduce EXP-003A's frozen models -- stop: {reproduction_check}")
    print("Reproduction check passed: refit models exactly match EXP-003A's frozen chosen_C values.")

    results = {"reproduction_check": reproduction_check, "frozen_threshold": FROZEN_THRESHOLD}

    # ---- Qwen reference (existing EXP-003A test result, cited not recomputed for the primary model) ----
    results["qwen_reference"] = {
        "note": "Cited directly from experiments/EXP-003A/results.json test_evaluation -- not recomputed.",
        "primary_combined_test_at_frozen_threshold": exp003a_results["test_evaluation"]["metrics_at_frozen_threshold"],
    }

    # ---- Apply frozen models to Qwen's OWN test set for stylo-only/lm-only feature groups too ----
    # (EXP-003A only ever evaluated these on validation; touching test here
    # is a read-only application of an already-fixed model for
    # cross-generator feature-group comparison symmetry -- no selection
    # happens as a result of this number.)
    X_qwen_test_all, y_qwen_test = to_xy(qwen_test, ALL_FIELDS)
    Xs_qwen_test_all = scaler.transform(X_qwen_test_all)
    scores_qwen_stylo = model_stylo.predict_proba(subset(Xs_qwen_test_all, STYLO_FIELDS))[:, 1]
    scores_qwen_lm = model_lm.predict_proba(subset(Xs_qwen_test_all, LM_FIELDS))[:, 1]
    results["qwen_reference"]["stylometric_only_test_at_0.5"] = metrics_at_threshold(y_qwen_test, scores_qwen_stylo, 0.5)
    results["qwen_reference"]["lm_only_test_at_0.5"] = metrics_at_threshold(y_qwen_test, scores_qwen_lm, 0.5)

    # ---- Build the held-out Phi evaluation set: 23 human (reused EXP-003A test features) + 23 phi_full_ai ----
    human_test = [r for r in qwen_test if r["label"] == "human"]
    assert len(human_test) == 23, f"expected 23 human test records, got {len(human_test)}"
    assert len(phi_records) == 23, f"expected 23 Phi records, got {len(phi_records)}"

    phi_eval_set = human_test + phi_records
    X_phi_all, y_phi = to_xy(phi_eval_set, ALL_FIELDS)
    Xs_phi_all = scaler.transform(X_phi_all)

    results["phi_evaluation"] = {
        "note": "SINGLE evaluation of the already-frozen model against held-out Phi data. Nothing is re-fit or re-selected based on this result.",
        "n": len(phi_eval_set),
        "class_counts": {"human": 23, "phi_full_ai": 23},
    }

    scores_phi_combined = model_combined.predict_proba(Xs_phi_all)[:, 1]
    results["phi_evaluation"]["primary_combined_at_frozen_threshold"] = metrics_at_threshold(y_phi, scores_phi_combined, FROZEN_THRESHOLD)
    results["phi_evaluation"]["primary_combined_at_0.5_for_reference"] = metrics_at_threshold(y_phi, scores_phi_combined, 0.5)

    scores_phi_stylo = model_stylo.predict_proba(subset(Xs_phi_all, STYLO_FIELDS))[:, 1]
    scores_phi_lm = model_lm.predict_proba(subset(Xs_phi_all, LM_FIELDS))[:, 1]
    results["phi_evaluation"]["stylometric_only_at_0.5"] = metrics_at_threshold(y_phi, scores_phi_stylo, 0.5)
    results["phi_evaluation"]["lm_only_at_0.5"] = metrics_at_threshold(y_phi, scores_phi_lm, 0.5)

    # ---- Per-sample predictions (audit trail + failure analysis) ----
    per_sample = []
    for i, r in enumerate(phi_eval_set):
        score = float(scores_phi_combined[i])
        pred_label = "machine" if score >= FROZEN_THRESHOLD else "human"
        per_sample.append({
            "sample_id": r["sample_id"], "family_id": r["family_id"],
            "true_label": r["label"], "predicted_label": pred_label,
            "score": round(score, 4), "correct": pred_label == r["label"],
        })
    results["phi_per_sample_predictions"] = per_sample

    # ---- Score distribution summary ----
    def score_summary(scores, mask=None):
        s = scores[mask] if mask is not None else scores
        return {
            "n": int(len(s)), "mean": round(float(np.mean(s)), 4), "median": round(float(np.median(s)), 4),
            "std": round(float(np.std(s)), 4), "min": round(float(np.min(s)), 4), "max": round(float(np.max(s)), 4),
        }

    is_human = y_phi == 0
    is_phi_ai = y_phi == 1
    results["score_distribution"] = {
        "human_scores": score_summary(scores_phi_combined, is_human),
        "phi_full_ai_scores": score_summary(scores_phi_combined, is_phi_ai),
    }
    # Qwen's own test-set score distribution, for direct comparison
    scores_qwen_combined_test = model_combined.predict_proba(Xs_qwen_test_all)[:, 1]
    is_qwen_human = y_qwen_test == 0
    is_qwen_ai = y_qwen_test == 1
    results["score_distribution"]["qwen_human_scores_reference"] = score_summary(scores_qwen_combined_test, is_qwen_human)
    results["score_distribution"]["qwen_full_ai_scores_reference"] = score_summary(scores_qwen_combined_test, is_qwen_ai)

    # ---- Feature-distribution analysis: human vs Qwen full_ai vs Phi full_ai, ALL 29 features ----
    qwen_ai_test = [r for r in qwen_test if r["label"] == "machine"]
    feature_distribution = {}
    for f in ALL_FIELDS:
        feature_distribution[f] = {
            "human": {
                "mean": round(float(np.mean([r[f] for r in human_test])), 4),
                "std": round(float(np.std([r[f] for r in human_test])), 4),
            },
            "qwen_full_ai": {
                "mean": round(float(np.mean([r[f] for r in qwen_ai_test])), 4),
                "std": round(float(np.std([r[f] for r in qwen_ai_test])), 4),
            },
            "phi_full_ai": {
                "mean": round(float(np.mean([r[f] for r in phi_records])), 4),
                "std": round(float(np.std([r[f] for r in phi_records])), 4),
            },
        }
    results["feature_distribution_all_29"] = feature_distribution
    results["feature_distribution_note"] = (
        "Full 29-feature table computed with no cherry-picking. "
        "genuine LM predictability features (not length/count) per EXP-003B-R1's "
        "classification: " + ", ".join(LM_PREDICTABILITY_NON_COUNT)
    )

    # ---- Reproducibility record ----
    import platform

    import sklearn

    results["reproducibility"] = {
        "qwen_dataset": "PRIMARY-DATASET-v1 (unchanged, checksums verified before generation)",
        "phi_dataset": "data/generated/GEN-001/samples.jsonl",
        "generation_script": "scripts/run_gen001_generate.py",
        "feature_extraction_script": "scripts/run_gen001_features.py (reuses exp003a_extract_features.extract_features_for_essay unchanged)",
        "evaluation_script": "scripts/run_gen001_evaluate.py",
        "random_seed": RANDOM_SEED,
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "frozen_threshold_source": "experiments/EXP-003A/results.json threshold_selection.chosen_threshold",
        "detector_config": "Identical to EXP-003A's frozen primary model: L2 logistic regression via LogisticRegressionCV, "
        "5-fold StratifiedKFold(shuffle=True, random_state=42) on TRAIN, scoring=f1, StandardScaler fit on TRAIN only.",
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")
    print(json.dumps({k: v for k, v in results.items() if k not in ("phi_per_sample_predictions", "feature_distribution_all_29")}, indent=2))


if __name__ == "__main__":
    main()
