"""
Tests for exp003a_extract_features.py's essay-level aggregation logic
(the one necessary shape transformation this experiment adds -- see
that module's docstring; not a new feature per DEC-014).
"""

from exp003a_extract_features import (
    ESSAY_FIELDS,
    LM_SENTENCE_FIELDS,
    SENTENCE_FIELDS,
    extract_features_for_essay,
)

SAMPLE_ESSAY = (
    "Dear Principal, I believe students should be allowed to use phones at school. "
    "Many students need to contact their parents during the day. "
    "This policy would help students stay safe and connected. "
    "Some teachers worry about distraction, but rules can address that concern. "
    "In conclusion, a balanced phone policy benefits everyone."
)


def test_extract_features_for_essay_returns_all_29_pre_registered_fields():
    feats = extract_features_for_essay(SAMPLE_ESSAY)
    for f in ESSAY_FIELDS:
        assert f"stylo_{f}" in feats
    for f in SENTENCE_FIELDS:
        assert f"stylo_mean_{f}" in feats
    for f in LM_SENTENCE_FIELDS:
        assert f"lm_mean_{f}" in feats
    assert "lm_mean_predictability_delta" in feats
    n_stylo = len(ESSAY_FIELDS) + len(SENTENCE_FIELDS)
    n_lm = len(LM_SENTENCE_FIELDS) + 1
    assert n_stylo == 23 and n_lm == 6


def test_extract_features_for_essay_no_missing_values_on_a_normal_essay():
    feats = extract_features_for_essay(SAMPLE_ESSAY)
    missing = [k for k, v in feats.items() if v is None and k not in ("n_sentences_scored_by_lm", "n_sentences_total")]
    assert missing == [], f"unexpected missing features: {missing}"


def test_extract_features_for_essay_sentence_count_matches_scored_count():
    feats = extract_features_for_essay(SAMPLE_ESSAY)
    assert feats["n_sentences_total"] == 5
    # every sentence in this normal-length essay should have scorable LM tokens
    assert feats["n_sentences_scored_by_lm"] == feats["n_sentences_total"]
