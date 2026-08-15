"""
Tests for run_exp003b_r1.py: feature-group definitions (disjointness,
exact composition, the documented C==F equivalence) and the group-scoped
top-1 aggregation helper. Pipeline correctness, not expected performance.
"""

from run_exp003a import ALL_FIELDS
from run_exp003b_r1 import (
    GROUPS,
    LENGTH_COUNT,
    LM_PREDICTABILITY_NON_COUNT,
    STYLO_NON_LENGTH,
    _top1_for_group,
)


def test_three_base_sets_are_disjoint_and_cover_all_29_fields():
    base_union = set(LENGTH_COUNT) | set(STYLO_NON_LENGTH) | set(LM_PREDICTABILITY_NON_COUNT)
    assert base_union == set(ALL_FIELDS)
    assert len(LENGTH_COUNT) + len(STYLO_NON_LENGTH) + len(LM_PREDICTABILITY_NON_COUNT) == len(ALL_FIELDS)


def test_group_sizes_match_the_documented_design():
    assert len(GROUPS["A_all_29"]) == 29
    assert len(GROUPS["B_length_count_only"]) == 11
    assert len(GROUPS["C_non_length_combined"]) == 18
    assert len(GROUPS["D_lm_only"]) == 6
    assert len(GROUPS["E_stylo_non_length_only"]) == 13
    assert len(GROUPS["F_combined_non_length"]) == 18


def test_c_and_f_are_the_documented_identical_set():
    assert set(GROUPS["C_non_length_combined"]) == set(GROUPS["F_combined_non_length"])


def test_lm_mean_token_count_is_classified_as_length_count_not_predictability():
    # The specific, explicitly-instructed reclassification this
    # experiment exists to apply.
    assert "lm_mean_token_count" in LENGTH_COUNT
    assert "lm_mean_token_count" not in LM_PREDICTABILITY_NON_COUNT
    assert "lm_mean_token_count" not in GROUPS["C_non_length_combined"]
    assert "lm_mean_token_count" in GROUPS["D_lm_only"]  # D matches EXP-003B's original lm_only definition exactly


def test_d_lm_only_matches_exp003b_original_six_lm_fields():
    from run_exp003a import LM_FIELDS

    assert set(GROUPS["D_lm_only"]) == set(LM_FIELDS)


class _StubModel:
    def __init__(self, scores):
        self._scores = scores
        self._i = 0

    def predict_proba(self, X):
        import numpy as np

        n = X.shape[0]
        batch = self._scores[self._i : self._i + n]
        self._i += n
        return np.array([[1 - s, s] for s in batch])


class _IdentityScaler:
    def transform(self, X):
        return X


def _row(essay_id, split, label, fields, value):
    return {"essay_sample_id": essay_id, "split": split, "label": label, **{f: value for f in fields}}


def test_top1_for_group_uses_only_the_specified_feature_columns():
    fields = ["stylo_type_token_ratio", "stylo_mean_avg_word_length"]
    records = [
        _row("essayA", "test", "human", fields, 1.0),
        _row("essayA", "test", "ai_assisted", fields, 1.0),
    ]
    model = _StubModel([0.1, 0.9])
    result = _top1_for_group(records, model, _IdentityScaler(), fields)
    assert result["test"]["top1_accuracy"] == 1.0
