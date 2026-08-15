"""
EXP-003C -- three-class (human / full_ai / ai_assisted), essay-level
only (Stage 2: modeling). Reads experiments/EXP-003C/features_essay.jsonl
(Stage 1, merged from cached EXP-003A/B vectors -- no new feature
extraction) and runs the approved protocol: baseline -> three feature
groups (stylometric-only, LM-only, combined) -> primary model
(multinomial L2 logistic regression) -> validation-only model
comparison -> freeze -> single TEST evaluation.

Multiclass adaptation from DEC-015's binary procedure (necessary, not a
methodology change): CV scoring uses "f1_macro" instead of "f1" (the
binary-only scorer used in EXP-003A/B) -- macro-F1 is EXP-003C's own
headline metric (Section 7 of the approved protocol), so using it as
the model-selection criterion too is the direct, justified extension,
not a new choice invented for this script. Decision rule is `argmax`
over the three predicted class probabilities (Section 6 of the
protocol) -- no per-class threshold is introduced.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_exp003a import ALL_FIELDS, LM_FIELDS, RANDOM_SEED, STYLO_FIELDS  # noqa: E402

FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003C" / "features_essay.jsonl"
RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003C" / "results.json"

CLASSES = ["human", "machine", "ai_assisted"]  # "machine" = full_ai, matches the label already stored in feature files
CLASS_DISPLAY = {"human": "human", "machine": "full_ai", "ai_assisted": "ai_assisted"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def to_xy(records: list[dict], fields: list[str]):
    import numpy as np

    X = np.array([[r[f] for f in fields] for r in records], dtype=float)
    y = np.array([CLASSES.index(r["label"]) for r in records], dtype=int)
    return X, y


def fit_multinomial_logreg_cv(X_train, y_train, seed=RANDOM_SEED):
    from sklearn.linear_model import LogisticRegressionCV
    from sklearn.model_selection import StratifiedKFold

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    model = LogisticRegressionCV(
        Cs=10, cv=cv, penalty="l2", solver="lbfgs", max_iter=2000, scoring="f1_macro", random_state=seed
    )
    model.fit(X_train, y_train)
    return model


def multiclass_metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score

    n = len(y_true)
    correct = int((y_true == y_pred).sum())
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    per_class = {}
    for i, cls in enumerate(CLASSES):
        per_class[CLASS_DISPLAY[cls]] = {
            "precision": precision_score(y_true, y_pred, labels=[i], average="macro", zero_division=0),
            "recall": recall_score(y_true, y_pred, labels=[i], average="macro", zero_division=0),
            "f1": f1_score(y_true, y_pred, labels=[i], average="macro", zero_division=0),
        }

    pairwise = {}
    for i, src in enumerate(CLASSES):
        for j, dst in enumerate(CLASSES):
            if i != j:
                pairwise[f"{CLASS_DISPLAY[src]}_to_{CLASS_DISPLAY[dst]}"] = int(cm[i, j])

    return {
        "n": int(n),
        "correct": correct,
        "accuracy": correct / n if n else 0.0,
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
        "weighted_f1": f1_score(y_true, y_pred, average="weighted", zero_division=0),
        "per_class": per_class,
        "confusion_matrix": {"labels": [CLASS_DISPLAY[c] for c in CLASSES], "matrix": cm.tolist()},
        "pairwise_confusion_counts": pairwise,
    }


def main() -> None:
    import numpy as np
    from sklearn.preprocessing import StandardScaler

    records = load_jsonl(FEATURES_PATH)
    print(f"Loaded {len(records)} essay-level records")

    missing = [r["sample_id"] for r in records if any(r.get(f) is None for f in ALL_FIELDS)]
    if missing:
        raise RuntimeError(f"STOP: samples with missing feature values, not silently excluding: {missing}")
    print("Missingness check: none")

    train = [r for r in records if r["split"] == "train"]
    val = [r for r in records if r["split"] == "validation"]
    test = [r for r in records if r["split"] == "test"]
    print(f"train={len(train)} validation={len(val)} test={len(test)}")

    from collections import Counter

    results = {
        "dataset_version": "PRIMARY-DATASET-v1 (frozen manifest, unmodified)",
        "manifest_path": "data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json",
        "source_features": ["experiments/EXP-003A/features.jsonl", "experiments/EXP-003B/features_essay.jsonl"],
        "n_records": len(records),
        "split_counts": {name: dict(Counter(CLASS_DISPLAY[r["label"]] for r in split))
                          for name, split in (("train", train), ("validation", val), ("test", test))},
    }

    X_train_all, y_train = to_xy(train, ALL_FIELDS)
    X_val_all, y_val = to_xy(val, ALL_FIELDS)
    X_test_all, y_test = to_xy(test, ALL_FIELDS)

    # Baseline: majority class
    majority_idx = int(Counter(y_train).most_common(1)[0][0])
    val_pred_majority = np.full_like(y_val, majority_idx)
    test_pred_majority = np.full_like(y_test, majority_idx)
    results["baseline_majority"] = {
        "majority_class": CLASS_DISPLAY[CLASSES[majority_idx]],
        "validation": multiclass_metrics(y_val, val_pred_majority),
        "test_for_reference_only": multiclass_metrics(y_test, test_pred_majority),
    }

    scaler = StandardScaler().fit(X_train_all)
    Xs_train_all, Xs_val_all, Xs_test_all = scaler.transform(X_train_all), scaler.transform(X_val_all), scaler.transform(X_test_all)
    field_idx = {f: i for i, f in enumerate(ALL_FIELDS)}

    def subset(X, fields):
        return X[:, [field_idx[f] for f in fields]]

    # Feature groups, compared on VALIDATION only
    groups = {"stylometric_only": STYLO_FIELDS, "lm_only": LM_FIELDS, "combined": ALL_FIELDS}
    group_results = {}
    fitted_models = {}
    for name, fields in groups.items():
        m = fit_multinomial_logreg_cv(subset(Xs_train_all, fields), y_train)
        val_pred = m.predict(subset(Xs_val_all, fields))
        group_results[name] = {
            "n_features": len(fields), "chosen_C": float(m.C_[0]) if hasattr(m, "C_") else None,
            "validation": multiclass_metrics(y_val, val_pred),
        }
        fitted_models[name] = m
    results["feature_group_comparison_validation_only"] = group_results

    # Primary model is "combined" per DEC-014 -- pre-registered, not chosen by validation score
    primary_model = fitted_models["combined"]
    results["primary_model"] = {
        "feature_group": "combined (pre-registered primary, DEC-014 -- not selected by validation score)",
        "n_features": len(ALL_FIELDS), "chosen_C": float(primary_model.C_[0]),
    }

    # FREEZE. Single TEST evaluation.
    test_pred = primary_model.predict(Xs_test_all)
    test_proba = primary_model.predict_proba(Xs_test_all)
    results["test_evaluation"] = {
        "note": "SINGLE evaluation, performed once, after freeze. Decision rule: argmax over class probabilities.",
        "metrics": multiclass_metrics(y_test, test_pred),
    }

    test_predictions = []
    for i, r in enumerate(test):
        pred_idx = int(test_pred[i])
        true_idx = CLASSES.index(r["label"])
        test_predictions.append({
            "sample_id": r["sample_id"], "family_id": r["family_id"],
            "true_label": CLASS_DISPLAY[r["label"]], "predicted_label": CLASS_DISPLAY[CLASSES[pred_idx]],
            "class_probabilities": {CLASS_DISPLAY[c]: round(float(p), 4) for c, p in zip(CLASSES, test_proba[i])},
            "correct": pred_idx == true_idx,
        })
    results["test_predictions"] = test_predictions

    # Coefficients (multinomial: one row per class)
    coefs = primary_model.coef_  # shape (3, 29)
    coef_table = {}
    for i, cls in enumerate(CLASSES):
        coef_table[CLASS_DISPLAY[cls]] = sorted(
            [{"feature": f, "standardized_coefficient": round(float(c), 4)} for f, c in zip(ALL_FIELDS, coefs[i])],
            key=lambda d: abs(d["standardized_coefficient"]), reverse=True,
        )
    results["primary_model_coefficients_per_class"] = coef_table

    import platform

    import sklearn

    results["reproducibility"] = {
        "random_seed": RANDOM_SEED, "sklearn_version": sklearn.__version__, "python_version": platform.python_version(),
        "primary_model_class": "sklearn.linear_model.LogisticRegression via LogisticRegressionCV "
                                "(L2, 5-fold StratifiedKFold on TRAIN, scoring=f1_macro, multinomial)",
        "scaler": "sklearn.preprocessing.StandardScaler fit on TRAIN only",
        "decision_rule": "argmax over predicted class probabilities (no per-class threshold)",
        "merge_script": "scripts/exp003c_merge_features.py", "modeling_script": "scripts/run_exp003c.py",
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"\nWrote results to {RESULTS_PATH}")
    print("\nValidation macro-F1 by group:")
    for name, g in group_results.items():
        print(f"  {name}: {g['validation']['macro_f1']:.3f}")
    print(f"\nFrozen TEST: accuracy={results['test_evaluation']['metrics']['accuracy']:.3f} "
          f"macro_f1={results['test_evaluation']['metrics']['macro_f1']:.3f} "
          f"weighted_f1={results['test_evaluation']['metrics']['weighted_f1']:.3f}")


if __name__ == "__main__":
    main()
