"""
Tests for run_exp003b.py's B-specific logic. Verifies pipeline
correctness (grouping, aggregation, exclusion behavior), not expected
detector performance -- no test here asserts a particular accuracy
number.
"""

from run_exp003a import ALL_FIELDS
from run_exp003b import top1_localization_accuracy


class _StubModel:
    """Duck-typed stand-in for a fitted sklearn classifier: returns a
    fixed score per row index, in call order, so the aggregation logic
    (not the model fit) is what's under test."""

    def __init__(self, scores):
        self._scores = scores
        self._call_count = 0

    def predict_proba(self, X):
        import numpy as np

        n = X.shape[0]
        batch = self._scores[self._call_count : self._call_count + n]
        self._call_count += n
        return np.array([[1 - s, s] for s in batch])


class _IdentityScaler:
    def transform(self, X):
        return X


def _row(essay_id, split, label, value):
    return {"essay_sample_id": essay_id, "split": split, "label": label, **{f: value for f in ALL_FIELDS}}


def test_top1_localization_accuracy_correct_when_true_sentence_scores_highest():
    records = [
        _row("essayA", "test", "human", 1.0),
        _row("essayA", "test", "ai_assisted", 1.0),
        _row("essayA", "test", "human", 1.0),
    ]
    # scores assigned in the order rows are grouped/iterated: essayA's 3 rows
    model = _StubModel([0.1, 0.9, 0.2])  # the ai_assisted row (index 1) scores highest
    result = top1_localization_accuracy(records, model, _IdentityScaler(), "test")
    assert result["n_essays_with_a_locatable_positive_sentence"] == 1
    assert result["n_top1_correct"] == 1
    assert result["top1_accuracy"] == 1.0


def test_top1_localization_accuracy_incorrect_when_a_human_sentence_scores_highest():
    records = [
        _row("essayA", "test", "human", 1.0),
        _row("essayA", "test", "ai_assisted", 1.0),
        _row("essayA", "test", "human", 1.0),
    ]
    model = _StubModel([0.9, 0.1, 0.2])  # a human row scores highest, not the ai_assisted one
    result = top1_localization_accuracy(records, model, _IdentityScaler(), "test")
    assert result["n_top1_correct"] == 0
    assert result["top1_accuracy"] == 0.0


def test_top1_localization_accuracy_skips_essays_with_no_locatable_positive():
    # An essay with only human-labeled rows in this split (its true
    # positive sentence was excluded upstream, e.g. missing predictability_delta)
    # must not be counted -- this exercises the exact scenario that
    # produced 119 (not 127) locatable essays in the real EXP-003B run.
    records = [
        _row("essayA", "test", "human", 1.0),
        _row("essayA", "test", "human", 1.0),
    ]
    model = _StubModel([0.5, 0.5])
    result = top1_localization_accuracy(records, model, _IdentityScaler(), "test")
    assert result["n_essays_with_a_locatable_positive_sentence"] == 0
    assert result["top1_accuracy"] is None


def test_top1_localization_accuracy_only_considers_the_requested_split():
    records = [
        _row("essayA", "train", "ai_assisted", 1.0),
        _row("essayB", "test", "ai_assisted", 1.0),
        _row("essayB", "test", "human", 1.0),
    ]
    model = _StubModel([0.9, 0.2])  # only essayB's 2 test rows are scored
    result = top1_localization_accuracy(records, model, _IdentityScaler(), "test")
    assert result["n_essays_with_a_locatable_positive_sentence"] == 1


def test_top1_localization_accuracy_handles_multiple_essays_independently():
    records = [
        _row("essayA", "test", "human", 1.0),
        _row("essayA", "test", "ai_assisted", 1.0),
        _row("essayB", "test", "ai_assisted", 1.0),
        _row("essayB", "test", "human", 1.0),
    ]
    # essayA: correct (ai_assisted scores higher); essayB: wrong (human scores higher)
    model = _StubModel([0.2, 0.8, 0.3, 0.7])
    result = top1_localization_accuracy(records, model, _IdentityScaler(), "test")
    assert result["n_essays_with_a_locatable_positive_sentence"] == 2
    assert result["n_top1_correct"] == 1
    assert result["top1_accuracy"] == 0.5
