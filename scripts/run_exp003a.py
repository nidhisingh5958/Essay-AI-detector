"""
EXP-003A -- human vs full_ai (Stage 2: modeling). Reads
experiments/EXP-003A/features.jsonl (Stage 1 output) and runs the full,
pre-registered protocol (DEC-014/DEC-015, EXP-003.md):

  baselines (majority, stylometric-only, LM-only)
  -> primary model (combined, L2 logistic regression)
  -> secondary comparison (random forest)
  -> threshold selection on VALIDATION only
  -> freeze
  -> single TEST evaluation
  -> feature ablation (TRAIN+VALIDATION only)
  -> interpretability (standardized coefficients)
  -> confidently-wrong examples (from the frozen test run)

TEST is touched exactly once, after every other decision is frozen.
All results are written to experiments/EXP-003A/results.json for the
report to read verbatim -- no number in reports/EXP-003A.md should be
retyped by hand from a different source.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "results.json"

STYLO_FIELDS = [
    "stylo_sentence_count", "stylo_sentence_length_mean", "stylo_sentence_length_std",
    "stylo_sentence_length_cv", "stylo_short_sentence_ratio", "stylo_medium_sentence_ratio",
    "stylo_long_sentence_ratio", "stylo_type_token_ratio", "stylo_moving_average_ttr",
    "stylo_rare_word_ratio", "stylo_repeated_bigram_ratio", "stylo_repeated_trigram_ratio",
    "stylo_repeated_sentence_opening_ratio", "stylo_mean_word_count", "stylo_mean_char_count",
    "stylo_mean_punctuation_count", "stylo_mean_avg_word_length", "stylo_mean_noun_ratio",
    "stylo_mean_verb_ratio", "stylo_mean_adj_ratio", "stylo_mean_adv_ratio",
    "stylo_mean_pronoun_ratio", "stylo_mean_dependency_depth",
]
LM_WITHIN_SENTENCE_FIELDS = [
    "lm_mean_mean_log_prob", "lm_mean_median_log_prob", "lm_mean_log_prob_variance",
    "lm_mean_perplexity", "lm_mean_token_count",
]
LM_NEIGHBOR_FIELD = ["lm_mean_predictability_delta"]
LM_FIELDS = LM_WITHIN_SENTENCE_FIELDS + LM_NEIGHBOR_FIELD
ALL_FIELDS = STYLO_FIELDS + LM_FIELDS
assert len(STYLO_FIELDS) == 23 and len(LM_FIELDS) == 6 and len(ALL_FIELDS) == 29

RANDOM_SEED = 42


def load_features() -> list[dict]:
    return [json.loads(line) for line in FEATURES_PATH.read_text().splitlines() if line.strip()]


def to_xy(records: list[dict], fields: list[str]):
    import numpy as np

    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([1 if r["label"] == "machine" else 0 for r in records], dtype=int)  # 1 = full_ai
    return X, y


def check_missingness(records: list[dict]) -> dict:
    missing = {}
    for f in ALL_FIELDS:
        n_missing = sum(1 for r in records if r.get(f) is None)
        if n_missing:
            missing[f] = n_missing
    return missing


def fit_logreg_cv(X_train, y_train, seed=RANDOM_SEED):
    from sklearn.linear_model import LogisticRegressionCV
    from sklearn.model_selection import StratifiedKFold

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    model = LogisticRegressionCV(
        Cs=10, cv=cv, penalty="l2", solver="lbfgs", max_iter=2000, scoring="f1", random_state=seed
    )
    model.fit(X_train, y_train)
    return model


def metrics_at_threshold(y_true, scores, threshold: float) -> dict:
    from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

    preds = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, preds, labels=[0, 1]).ravel()
    n = len(y_true)
    correct = int(tp + tn)
    return {
        "threshold": threshold,
        "n": int(n),
        "correct": correct,
        "accuracy": correct / n,
        "precision_machine": precision_score(y_true, preds, pos_label=1, zero_division=0),
        "recall_machine": recall_score(y_true, preds, pos_label=1, zero_division=0),
        "f1_machine": f1_score(y_true, preds, pos_label=1, zero_division=0),
        "precision_human": precision_score(y_true, preds, pos_label=0, zero_division=0),
        "recall_human": recall_score(y_true, preds, pos_label=0, zero_division=0),
        "f1_human": f1_score(y_true, preds, pos_label=0, zero_division=0),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def select_threshold_on_validation(y_val, scores_val) -> dict:
    import numpy as np
    from sklearn.metrics import f1_score

    candidates = np.linspace(0.01, 0.99, 99)
    best_t, best_f1 = 0.5, -1.0
    sweep = []
    for t in candidates:
        preds = (scores_val >= t).astype(int)
        f1 = f1_score(y_val, preds, zero_division=0)
        sweep.append({"threshold": round(float(t), 2), "f1_macro_proxy": round(float(f1), 4)})
        if f1 > best_f1:
            best_f1, best_t = f1, t
    at_default = metrics_at_threshold(y_val, scores_val, 0.5)
    at_best = metrics_at_threshold(y_val, scores_val, float(best_t))
    return {
        "candidate_procedure": "sweep threshold 0.01-0.99 in 0.01 steps, maximize F1 (positive class = full_ai) on VALIDATION",
        "chosen_threshold": round(float(best_t), 2),
        "chosen_threshold_validation_f1": round(float(best_f1), 4),
        "default_threshold_0.5_validation_metrics": at_default,
        "chosen_threshold_validation_metrics": at_best,
    }


def main() -> None:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    records = load_features()
    print(f"Loaded {len(records)} feature records")

    missing = check_missingness(records)
    print("Missingness check:", missing if missing else "none")

    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    test = [r for r in records if r["split"] == "test"]
    print(f"train={len(train)} validation={len(val)} test={len(test)}")

    results = {"n_records": len(records), "missingness": missing,
               "split_counts": {"train": len(train), "validation": len(val), "test": len(test)}}

    # Class balance per split
    for name, split in (("train", train), ("validation", val), ("test", test)):
        n_human = sum(1 for r in split if r["label"] == "human")
        n_machine = sum(1 for r in split if r["label"] == "machine")
        results.setdefault("class_balance", {})[name] = {"human": n_human, "full_ai": n_machine}

    # ---- Baseline A: majority class ----
    y_train_all = to_xy(train, ALL_FIELDS)[1]
    majority_class = int(round(y_train_all.mean())) if len(y_train_all) else 0
    majority_label = "machine" if majority_class == 1 else "human"

    def majority_metrics(split_records):
        y = to_xy(split_records, ALL_FIELDS)[1]
        preds = np.full_like(y, majority_class)
        n = len(y)
        correct = int((preds == y).sum())
        return {"n": int(n), "correct": correct, "accuracy": correct / n if n else 0.0}

    results["baseline_A_majority"] = {
        "majority_class_in_train": majority_label,
        "train_class_counts": {"human": int((y_train_all == 0).sum()), "machine": int((y_train_all == 1).sum())},
        "validation": majority_metrics(val),
        "test": majority_metrics(test),
    }

    # ---- Fit scaler on TRAIN only, for ALL_FIELDS (used by all logreg variants) ----
    X_train_all, y_train = to_xy(train, ALL_FIELDS)
    X_val_all, y_val = to_xy(val, ALL_FIELDS)
    X_test_all, y_test = to_xy(test, ALL_FIELDS)

    scaler = StandardScaler().fit(X_train_all)
    Xs_train_all = scaler.transform(X_train_all)
    Xs_val_all = scaler.transform(X_val_all)
    Xs_test_all = scaler.transform(X_test_all)

    field_idx = {f: i for i, f in enumerate(ALL_FIELDS)}

    def subset(X, fields):
        idx = [field_idx[f] for f in fields]
        return X[:, idx]

    # ---- Baseline B: stylometric-only ----
    Xb_train = subset(Xs_train_all, STYLO_FIELDS)
    Xb_val = subset(Xs_val_all, STYLO_FIELDS)
    model_B = fit_logreg_cv(Xb_train, y_train)
    scores_B_val = model_B.predict_proba(Xb_val)[:, 1]
    results["baseline_B_stylometric_only"] = {
        "n_features": len(STYLO_FIELDS), "chosen_C": float(model_B.C_[0]),
        "validation_at_0.5": metrics_at_threshold(y_val, scores_B_val, 0.5),
    }

    # ---- Baseline C: LM-only ----
    Xc_train = subset(Xs_train_all, LM_FIELDS)
    Xc_val = subset(Xs_val_all, LM_FIELDS)
    model_C = fit_logreg_cv(Xc_train, y_train)
    scores_C_val = model_C.predict_proba(Xc_val)[:, 1]
    results["baseline_C_lm_only"] = {
        "n_features": len(LM_FIELDS), "chosen_C": float(model_C.C_[0]),
        "validation_at_0.5": metrics_at_threshold(y_val, scores_C_val, 0.5),
    }

    # ---- Primary: combined logistic regression ----
    model_primary = fit_logreg_cv(Xs_train_all, y_train)
    scores_primary_val = model_primary.predict_proba(Xs_val_all)[:, 1]
    results["primary_combined_logreg"] = {
        "n_features": len(ALL_FIELDS), "chosen_C": float(model_primary.C_[0]),
        "validation_at_0.5": metrics_at_threshold(y_val, scores_primary_val, 0.5),
    }

    # ---- Secondary: random forest (fixed config, not tuned, comparison only) ----
    rf = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=RANDOM_SEED)
    rf.fit(Xs_train_all, y_train)
    scores_rf_val = rf.predict_proba(Xs_val_all)[:, 1]
    results["secondary_random_forest"] = {
        "n_features": len(ALL_FIELDS), "config": {"n_estimators": 200, "max_depth": 5},
        "validation_at_0.5": metrics_at_threshold(y_val, scores_rf_val, 0.5),
    }

    # ---- Threshold selection on VALIDATION for the PRIMARY model ----
    results["threshold_selection"] = select_threshold_on_validation(y_val, scores_primary_val)
    chosen_threshold = results["threshold_selection"]["chosen_threshold"]

    # ---- FREEZE: primary model + scaler + threshold are now fixed. ----
    # ---- Single TEST evaluation ----
    scores_primary_test = model_primary.predict_proba(Xs_test_all)[:, 1]
    results["test_evaluation"] = {
        "note": "SINGLE evaluation, performed once, after freeze. Not repeated.",
        "metrics_at_frozen_threshold": metrics_at_threshold(y_test, scores_primary_test, chosen_threshold),
        "metrics_at_0.5_for_reference_only": metrics_at_threshold(y_test, scores_primary_test, 0.5),
    }

    # Per-sample test predictions (for confidently-wrong-examples + audit trail)
    test_predictions = []
    for i, r in enumerate(test):
        score = float(scores_primary_test[i])
        pred_label = "machine" if score >= chosen_threshold else "human"
        test_predictions.append({
            "sample_id": r["sample_id"], "family_id": r["family_id"],
            "true_label": r["label"], "predicted_label": pred_label,
            "score": round(score, 4), "correct": pred_label == r["label"],
        })
    results["test_predictions"] = test_predictions

    # ---- Feature ablation: TRAIN + VALIDATION only, never test ----
    ablations = {
        "all_29_features": ALL_FIELDS,
        "stylometric_only_23": STYLO_FIELDS,
        "lm_only_6": LM_FIELDS,
        "combined_minus_lm_within_sentence_5": STYLO_FIELDS + LM_NEIGHBOR_FIELD,
        "combined_minus_neighboring_sentence_predictability_1": STYLO_FIELDS + LM_WITHIN_SENTENCE_FIELDS,
    }
    ablation_results = {}
    for name, fields in ablations.items():
        Xa_train = subset(Xs_train_all, fields)
        Xa_val = subset(Xs_val_all, fields)
        m = fit_logreg_cv(Xa_train, y_train)
        scores = m.predict_proba(Xa_val)[:, 1]
        ablation_results[name] = {
            "n_features": len(fields), "chosen_C": float(m.C_[0]),
            "validation_at_0.5": metrics_at_threshold(y_val, scores, 0.5),
        }
    results["feature_ablation_train_validation_only"] = ablation_results

    # ---- Interpretability: standardized coefficients of the FROZEN primary model ----
    coefs = model_primary.coef_[0]
    coef_table = sorted(
        [{"feature": f, "standardized_coefficient": round(float(c), 4)} for f, c in zip(ALL_FIELDS, coefs)],
        key=lambda d: abs(d["standardized_coefficient"]), reverse=True,
    )
    results["primary_model_coefficients"] = coef_table

    # ---- Reproducibility record ----
    import platform

    import sklearn

    results["reproducibility"] = {
        "dataset": "PRIMARY-DATASET-v1",
        "manifest_path": "data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json",
        "feature_extraction_script": "scripts/exp003a_extract_features.py",
        "modeling_script": "scripts/run_exp003a.py",
        "random_seed": RANDOM_SEED,
        "sklearn_version": sklearn.__version__,
        "python_version": platform.python_version(),
        "primary_model_class": "sklearn.linear_model.LogisticRegression (via LogisticRegressionCV, L2, 5-fold StratifiedKFold on TRAIN, scoring=f1)",
        "secondary_model_class": "sklearn.ensemble.RandomForestClassifier(n_estimators=200, max_depth=5, random_state=42), not tuned",
        "scaler": "sklearn.preprocessing.StandardScaler fit on TRAIN only",
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")
    print(json.dumps({k: v for k, v in results.items() if k not in ("test_predictions", "primary_model_coefficients")}, indent=2))


if __name__ == "__main__":
    main()
