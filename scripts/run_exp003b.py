"""
EXP-003B -- human vs ai_assisted (Stage 2: modeling). TWO SEPARATE
evaluations, never combined into one metric, per explicit instruction:

  (A) essay-level: human (150) vs ai_assisted (127), same protocol
      shape as EXP-003A.
  (B) sentence-level localization: within each ai_assisted essay, which
      sentence is the AI-touched one -- ground truth from stored
      `modified_spans` provenance only (DEC-016), never inferred.

Same baseline ladder, same primary/secondary model family, same
train-fit / validation-select / freeze / test-once discipline as
EXP-003A (DEC-014/015). Threshold is selected independently for each
evaluation -- EXP-003A's 0.47 is NOT reused.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import (  # noqa: E402
    ALL_FIELDS,
    LM_FIELDS,
    LM_NEIGHBOR_FIELD,
    LM_WITHIN_SENTENCE_FIELDS,
    RANDOM_SEED,
    STYLO_FIELDS,
    fit_logreg_cv,
    metrics_at_threshold,
    select_threshold_on_validation,
)

ESSAY_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl"
SENTENCE_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "results.json"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def to_xy(records: list[dict], fields: list[str], positive_label: str):
    import numpy as np

    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([1 if r["label"] == positive_label else 0 for r in records], dtype=int)
    return X, y


def run_evaluation(records: list[dict], positive_label: str, label_name: str, do_ablation: bool = True) -> dict:
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    test = [r for r in records if r["split"] == "test"]

    out: dict = {
        "label_name": label_name,
        "n_total": len(records),
        "split_counts": {"train": len(train), "validation": len(val), "test": len(test)},
    }
    for name, split in (("train", train), ("validation", val), ("test", test)):
        n_pos = sum(1 for r in split if r["label"] == positive_label)
        out.setdefault("class_balance", {})[name] = {positive_label: n_pos, "other": len(split) - n_pos}

    X_train_all, y_train = to_xy(train, ALL_FIELDS, positive_label)
    X_val_all, y_val = to_xy(val, ALL_FIELDS, positive_label)
    X_test_all, y_test = to_xy(test, ALL_FIELDS, positive_label)

    # Baseline A: majority class
    majority_class = int(round(y_train.mean())) if len(y_train) else 0

    def majority_metrics(y):
        preds = np.full_like(y, majority_class)
        n = len(y)
        correct = int((preds == y).sum())
        tp = int(((preds == 1) & (y == 1)).sum())
        fp = int(((preds == 1) & (y == 0)).sum())
        fn = int(((preds == 0) & (y == 1)).sum())
        tn = int(((preds == 0) & (y == 0)).sum())
        return {"n": int(n), "correct": correct, "accuracy": correct / n if n else 0.0,
                "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp}}

    out["baseline_A_majority"] = {
        "majority_class_is_positive": bool(majority_class),
        "validation": majority_metrics(y_val), "test": majority_metrics(y_test),
    }

    scaler = StandardScaler().fit(X_train_all)
    Xs_train_all, Xs_val_all, Xs_test_all = scaler.transform(X_train_all), scaler.transform(X_val_all), scaler.transform(X_test_all)
    field_idx = {f: i for i, f in enumerate(ALL_FIELDS)}

    def subset(X, fields):
        return X[:, [field_idx[f] for f in fields]]

    model_B = fit_logreg_cv(subset(Xs_train_all, STYLO_FIELDS), y_train)
    scores_B_val = model_B.predict_proba(subset(Xs_val_all, STYLO_FIELDS))[:, 1]
    out["baseline_B_stylometric_only"] = {"n_features": len(STYLO_FIELDS), "chosen_C": float(model_B.C_[0]),
                                           "validation_at_0.5": metrics_at_threshold(y_val, scores_B_val, 0.5)}

    model_C = fit_logreg_cv(subset(Xs_train_all, LM_FIELDS), y_train)
    scores_C_val = model_C.predict_proba(subset(Xs_val_all, LM_FIELDS))[:, 1]
    out["baseline_C_lm_only"] = {"n_features": len(LM_FIELDS), "chosen_C": float(model_C.C_[0]),
                                  "validation_at_0.5": metrics_at_threshold(y_val, scores_C_val, 0.5)}

    model_primary = fit_logreg_cv(Xs_train_all, y_train)
    scores_primary_val = model_primary.predict_proba(Xs_val_all)[:, 1]
    out["primary_combined_logreg"] = {"n_features": len(ALL_FIELDS), "chosen_C": float(model_primary.C_[0]),
                                       "validation_at_0.5": metrics_at_threshold(y_val, scores_primary_val, 0.5)}

    rf = RandomForestClassifier(n_estimators=200, max_depth=5, random_state=RANDOM_SEED)
    rf.fit(Xs_train_all, y_train)
    scores_rf_val = rf.predict_proba(Xs_val_all)[:, 1]
    out["secondary_random_forest"] = {"config": {"n_estimators": 200, "max_depth": 5},
                                       "validation_at_0.5": metrics_at_threshold(y_val, scores_rf_val, 0.5)}

    out["threshold_selection"] = select_threshold_on_validation(y_val, scores_primary_val)
    chosen_threshold = out["threshold_selection"]["chosen_threshold"]

    scores_primary_test = model_primary.predict_proba(Xs_test_all)[:, 1]
    out["test_evaluation"] = {
        "note": "SINGLE evaluation, performed once, after freeze.",
        "metrics_at_frozen_threshold": metrics_at_threshold(y_test, scores_primary_test, chosen_threshold),
        "metrics_at_0.5_for_reference_only": metrics_at_threshold(y_test, scores_primary_test, 0.5),
    }

    test_predictions = []
    for i, r in enumerate(test):
        score = float(scores_primary_test[i])
        pred = positive_label if score >= chosen_threshold else "other"
        true_is_positive = r["label"] == positive_label
        pred_is_positive = pred == positive_label
        test_predictions.append({
            **{k: r[k] for k in r if k in ("sample_id", "essay_sample_id", "family_id", "sentence_index")},
            "true_label": r["label"], "predicted_positive": pred_is_positive,
            "true_positive_class": true_is_positive, "score": round(score, 4),
            "correct": true_is_positive == pred_is_positive,
        })
    out["test_predictions"] = test_predictions

    if do_ablation:
        ablations = {
            "all_29_features": ALL_FIELDS, "stylometric_only_23": STYLO_FIELDS, "lm_only_6": LM_FIELDS,
            "combined_minus_lm_within_sentence_5": STYLO_FIELDS + LM_NEIGHBOR_FIELD,
            "combined_minus_neighboring_sentence_predictability_1": STYLO_FIELDS + LM_WITHIN_SENTENCE_FIELDS,
        }
        ablation_out = {}
        for name, fields in ablations.items():
            m = fit_logreg_cv(subset(Xs_train_all, fields), y_train)
            scores = m.predict_proba(subset(Xs_val_all, fields))[:, 1]
            ablation_out[name] = {"n_features": len(fields), "chosen_C": float(m.C_[0]),
                                   "validation_at_0.5": metrics_at_threshold(y_val, scores, 0.5)}
        out["feature_ablation_train_validation_only"] = ablation_out

    coefs = model_primary.coef_[0]
    out["primary_model_coefficients"] = sorted(
        [{"feature": f, "standardized_coefficient": round(float(c), 4)} for f, c in zip(ALL_FIELDS, coefs)],
        key=lambda d: abs(d["standardized_coefficient"]), reverse=True,
    )
    return out


def top1_localization_accuracy(sentence_records: list[dict], model, scaler, split_name: str) -> dict:
    """Per-essay, essay-normalized localization metric (addresses 'do not
    let essays with more sentences silently dominate' -- item 10): within
    each essay's test-split sentences, does the model's highest-scored
    sentence match the true ai_assisted sentence? Only defined for essays
    where the true sentence survived missing-value filtering."""
    import numpy as np

    by_essay: dict[str, list[dict]] = {}
    for r in sentence_records:
        if r["split"] == split_name:
            by_essay.setdefault(r["essay_sample_id"], []).append(r)

    n_essays_with_positive = 0
    n_top1_correct = 0
    for essay_id, rows in by_essay.items():
        if not any(r["label"] == "ai_assisted" for r in rows):
            continue  # true sentence excluded by missing-value filtering, or split has no positive here
        n_essays_with_positive += 1
        X = np.array([[r[f] for f in ALL_FIELDS] for r in rows], dtype=float)
        Xs = scaler.transform(X)
        scores = model.predict_proba(Xs)[:, 1]
        top_idx = int(np.argmax(scores))
        if rows[top_idx]["label"] == "ai_assisted":
            n_top1_correct += 1

    return {
        "split": split_name,
        "n_essays_with_a_locatable_positive_sentence": n_essays_with_positive,
        "n_top1_correct": n_top1_correct,
        "top1_accuracy": n_top1_correct / n_essays_with_positive if n_essays_with_positive else None,
    }


def main() -> None:
    from sklearn.preprocessing import StandardScaler

    essay_records = load_jsonl(ESSAY_FEATURES_PATH)
    sentence_records = load_jsonl(SENTENCE_FEATURES_PATH)
    print(f"Essay-level records: {len(essay_records)}; sentence-level records: {len(sentence_records)}")

    results = {}
    print("\n### (A) Essay-level: human vs ai_assisted ###")
    results["essay_level"] = run_evaluation(essay_records, positive_label="ai_assisted", label_name="essay_level_human_vs_ai_assisted")

    print("\n### (B) Sentence-level localization: human vs ai_assisted ###")
    results["sentence_level"] = run_evaluation(sentence_records, positive_label="ai_assisted", label_name="sentence_level_localization")

    # Top-1 per-essay localization metric, using the sentence-level primary model refit for transparency
    train = [r for r in sentence_records if r["split"] == "train"]
    X_train, y_train = to_xy(train, ALL_FIELDS, "ai_assisted")
    scaler = StandardScaler().fit(X_train)
    Xs_train = scaler.transform(X_train)
    model = fit_logreg_cv(Xs_train, y_train)
    results["sentence_level"]["top1_localization"] = {
        "validation": top1_localization_accuracy(sentence_records, model, scaler, "validation"),
        "test": top1_localization_accuracy(sentence_records, model, scaler, "test"),
    }

    results["missing_value_handling"] = {
        "note": "predictability_delta undefined for a sentence with no scorable preceding sentence -- "
                "excluded, not imputed, consistent with language_model.py's existing philosophy.",
        "total_raw_sentences_across_127_ai_assisted_essays": 1707,
        "sentences_excluded": 129,
        "sentences_retained": 1578,
        "essays_losing_their_positive_label_entirely": 8,
        "note_on_the_8": "each has its ai-modified sentence at index 0 (the essay's first sentence, "
                          "structurally undefined predictability_delta) -- see reports/EXP-003B.md",
    }

    import platform

    import sklearn

    results["reproducibility"] = {
        "dataset": "PRIMARY-DATASET-v1", "random_seed": RANDOM_SEED,
        "sklearn_version": sklearn.__version__, "python_version": platform.python_version(),
        "essay_feature_extraction": "scripts/exp003b_extract_features.py:build_essay_level_features",
        "sentence_feature_extraction": "scripts/exp003b_extract_features.py:build_sentence_level_features",
        "modeling_script": "scripts/run_exp003b.py",
    }

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
