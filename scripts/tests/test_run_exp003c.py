"""
Tests for run_exp003c.py's multiclass evaluation logic and
exp003c_merge_features.py's dataset-merge correctness. Pipeline
correctness, not expected performance -- no test asserts a particular
accuracy/F1 number.
"""

import numpy as np

from run_exp003c import CLASS_DISPLAY, CLASSES, multiclass_metrics


def test_classes_and_display_names_are_consistent():
    assert CLASSES == ["human", "machine", "ai_assisted"]
    assert CLASS_DISPLAY["machine"] == "full_ai"
    assert set(CLASS_DISPLAY.values()) == {"human", "full_ai", "ai_assisted"}


def test_multiclass_metrics_perfect_predictions():
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 0, 1, 1, 2, 2])
    m = multiclass_metrics(y_true, y_pred)
    assert m["accuracy"] == 1.0
    assert m["macro_f1"] == 1.0
    assert m["correct"] == 6
    for cls_name in ("human", "full_ai", "ai_assisted"):
        assert m["per_class"][cls_name]["f1"] == 1.0
    for pair, count in m["pairwise_confusion_counts"].items():
        assert count == 0


def test_multiclass_metrics_confusion_matrix_and_pairwise_counts_agree():
    # 2 human, 2 full_ai, 2 ai_assisted; both ai_assisted misclassified as human
    y_true = np.array([0, 0, 1, 1, 2, 2])
    y_pred = np.array([0, 0, 1, 1, 0, 0])
    m = multiclass_metrics(y_true, y_pred)
    assert m["pairwise_confusion_counts"]["ai_assisted_to_human"] == 2
    assert m["pairwise_confusion_counts"]["ai_assisted_to_full_ai"] == 0
    assert m["per_class"]["ai_assisted"]["recall"] == 0.0
    assert m["per_class"]["human"]["recall"] == 1.0  # both true humans still correctly predicted
    # confusion matrix row for ai_assisted (index 2) should show 2 in the human (index 0) column
    assert m["confusion_matrix"]["matrix"][2][0] == 2
    assert m["confusion_matrix"]["matrix"][2][2] == 0


def test_multiclass_metrics_reports_weighted_f1_distinct_from_macro_when_imbalanced():
    # Heavily imbalanced: 10 human (all correct), 1 full_ai (wrong), 1 ai_assisted (wrong)
    y_true = np.array([0] * 10 + [1, 2])
    y_pred = np.array([0] * 10 + [0, 0])
    m = multiclass_metrics(y_true, y_pred)
    assert m["macro_f1"] < 1.0
    assert m["weighted_f1"] > m["macro_f1"]  # weighted favors the majority class, which is perfect here


def test_exp003c_merged_features_file_has_no_duplicate_sample_ids():
    import json
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent.parent / "experiments" / "EXP-003C" / "features_essay.jsonl"
    if not path.exists():
        import pytest

        pytest.skip("EXP-003C features not present in this environment")
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ids = [r["sample_id"] for r in records]
    assert len(ids) == len(set(ids)) == 425
