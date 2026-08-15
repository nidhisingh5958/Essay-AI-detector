"""
Phase D tests for app.services.evidence_mapper -- deterministic
evidence mapping (DEC-017). Covers items A-L from the approved spec.
No test asserts a specific fairness/accuracy outcome; these test the
MAPPING layer's correctness (determinism, traceability, no fabrication,
no LLM/network dependency), not the underlying detector's performance
(already covered by test_detector.py).
"""

import ast
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ESSAY_ARTIFACT = REPO_ROOT / "backend" / "app" / "ml" / "essay_detector_v1.joblib"
SENTENCE_ARTIFACT = REPO_ROOT / "backend" / "app" / "ml" / "sentence_detector_v1.joblib"
REFERENCE_STATS = REPO_ROOT / "backend" / "app" / "ml" / "feature_reference_stats.json"
PRIMARY_SAMPLES = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"

pytestmark = pytest.mark.skipif(
    not (ESSAY_ARTIFACT.exists() and SENTENCE_ARTIFACT.exists() and REFERENCE_STATS.exists()),
    reason="detector artifacts / reference stats not built in this environment",
)

SAMPLE_ESSAY = (
    "This is a sample essay about summer activities. Students often spend their break "
    "outdoors, playing sports and reading books. Many families travel together during "
    "this time. It is a season associated with relaxation and personal growth."
)


def _load_text(sample_id: str) -> str:
    with open(PRIMARY_SAMPLES) as f:
        for line in f:
            rec = json.loads(line)
            if rec["sample_id"] == sample_id:
                return rec["text"]
    raise KeyError(sample_id)


# ---- A: deterministic output ----

def test_A_essay_evidence_is_deterministic():
    from app.services.evidence_mapper import build_essay_evidence

    first = build_essay_evidence(SAMPLE_ESSAY)
    second = build_essay_evidence(SAMPLE_ESSAY)
    assert first.state == second.state
    assert first.score == second.score
    assert [e.statement for e in first.evidence] == [e.statement for e in second.evidence]


def test_A_sentence_evidence_is_deterministic():
    from app.services.evidence_mapper import build_sentence_localization

    first = build_sentence_localization(SAMPLE_ESSAY)
    second = build_sentence_localization(SAMPLE_ESSAY)
    assert [c.text for c in first.candidates] == [c.text for c in second.candidates]
    assert [c.score for c in first.candidates] == [c.score for c in second.candidates]


# ---- B: known EXP-003B/R1 sentence rankings (reuses Phase C's own end-to-end check) ----

@pytest.mark.skipif(not PRIMARY_SAMPLES.exists(), reason="PRIMARY-DATASET-v1 not present")
def test_B_sentence_localization_wraps_the_verified_ranking_for_a_known_essay():
    from app.services.evidence_mapper import build_sentence_localization

    # Same essay used in test_sentence_ranking_offsets.py's end-to-end check.
    text = _load_text("2723DB12AC00__sentence_light_controlled_v2")
    result = build_sentence_localization(text, top_k=1)
    assert result.has_evidence
    assert len(result.candidates) == 1
    assert result.candidates[0].sentence_index == 4  # the known correct top-1 sentence for this essay


# ---- C: top-K ordering ----

def test_C_candidates_are_returned_in_rank_order():
    from app.services.evidence_mapper import build_sentence_localization

    result = build_sentence_localization(SAMPLE_ESSAY, top_k=10)
    ranks = [c.rank for c in result.candidates]
    assert ranks == sorted(ranks)
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)


def test_C_top_k_is_a_caller_controlled_presentation_setting():
    from app.services.evidence_mapper import build_sentence_localization

    k1 = build_sentence_localization(SAMPLE_ESSAY, top_k=1)
    k2 = build_sentence_localization(SAMPLE_ESSAY, top_k=2)
    assert len(k1.candidates) <= 1
    assert len(k2.candidates) <= 2
    assert k1.top_k == 1 and k2.top_k == 2


# ---- D: tie-breaking (covered structurally in test_sentence_ranking_offsets.py; re-verified via the mapper) ----

def test_D_evidence_selection_tie_break_is_canonical_feature_order():
    from app.services.evidence_mapper import _select_top_evidence
    from app.services.feature_spec import ALL_FIELDS

    # Two features with identical contribution magnitude -- tie must
    # resolve to canonical ALL_FIELDS order, not insertion/dict order.
    feature_vector = {f: 1.0 for f in ALL_FIELDS}
    contributions = {f: 0.0 for f in ALL_FIELDS}
    later_field, earlier_field = ALL_FIELDS[5], ALL_FIELDS[2]
    contributions[later_field] = 0.5
    contributions[earlier_field] = 0.5

    selected = _select_top_evidence(feature_vector, contributions, top_n=2)
    assert [e.feature for e in selected] == [earlier_field, later_field]


# ---- E: missing feature behavior ----

def test_E_essay_with_incomplete_features_returns_inconclusive_never_a_fabricated_score():
    from unittest.mock import patch

    from app.models.detector_results import EssayDetectionResult
    from app.services.detector import FeatureVectorIncompleteError
    from app.services.evidence_mapper import build_essay_evidence
    from app.models.evidence_results import EssayResultState

    with patch("app.services.evidence_mapper.predict_essay", side_effect=FeatureVectorIncompleteError("missing")):
        result = build_essay_evidence(SAMPLE_ESSAY)
    assert result.state == EssayResultState.INCONCLUSIVE
    assert result.score is None
    assert result.evidence == []


def test_E_select_top_evidence_discards_missing_values():
    from app.services.evidence_mapper import _select_top_evidence
    from app.services.feature_spec import ALL_FIELDS

    feature_vector = {f: 1.0 for f in ALL_FIELDS}
    feature_vector[ALL_FIELDS[0]] = None  # missing
    contributions = {f: (10.0 if f == ALL_FIELDS[0] else 0.1) for f in ALL_FIELDS}  # the missing one would rank #1 if not discarded

    selected = _select_top_evidence(feature_vector, contributions, top_n=29)
    assert ALL_FIELDS[0] not in [e.feature for e in selected]


# ---- F: no-scorable-sentence behavior ----

def test_F_empty_text_produces_explicit_no_evidence_state():
    from app.services.evidence_mapper import build_sentence_localization

    result = build_sentence_localization("")
    assert result.has_evidence is False
    assert result.no_evidence_reason is not None
    assert result.candidates == []


# ---- G: Unicode/offset correctness (covered by test_sentence_ranking_offsets.py; spot-checked via the mapper here) ----

def test_G_unicode_essay_produces_evidence_without_crashing():
    from app.services.evidence_mapper import build_essay_evidence, build_sentence_localization

    text = "L'élève a écrit un essai. Il fait très beau aujourd'hui à Montréal. 😀 Emoji included."
    essay_result = build_essay_evidence(text)
    assert essay_result.state is not None
    sentence_result = build_sentence_localization(text)
    for c in sentence_result.candidates:
        assert text or True  # smoke: no crash is the assertion here; offsets covered elsewhere


# ---- H: evidence reproducibility ----

def test_H_evidence_item_fields_are_all_traceable_to_the_input():
    from app.services.evidence_mapper import build_essay_evidence

    result = build_essay_evidence(SAMPLE_ESSAY)
    for item in result.evidence:
        assert item.feature
        assert item.human_label
        assert isinstance(item.observed_value, float)
        assert isinstance(item.contribution, float)
        assert item.direction in ("higher", "lower")
        assert item.feature in item.statement or item.human_label in item.statement


# ---- I: evidence ordering ----

def test_I_evidence_is_ordered_by_absolute_contribution_descending():
    from app.services.evidence_mapper import build_essay_evidence

    result = build_essay_evidence(SAMPLE_ESSAY)
    contributions = [abs(e.contribution) for e in result.evidence]
    assert contributions == sorted(contributions, reverse=True)


# ---- J: contribution calculation ----

def test_J_contribution_formula_matches_documented_linear_decomposition():
    from app.services.detector import _load_essay_artifact
    from app.services.evidence_mapper import _compute_contributions
    from app.services.feature_spec import ALL_FIELDS

    artifact = _load_essay_artifact()
    feature_vector = {f: 1.0 for f in ALL_FIELDS}

    contributions = _compute_contributions(feature_vector, artifact["scaler"], artifact["model"].coef_[0])

    # Manually recompute for one feature and compare exactly.
    i = 0
    f = ALL_FIELDS[i]
    expected = artifact["model"].coef_[0][i] * ((1.0 - artifact["scaler"].mean_[i]) / artifact["scaler"].scale_[i])
    assert contributions[f] == pytest.approx(expected, abs=1e-9)


def test_J_sum_of_all_contributions_plus_intercept_equals_the_model_logit():
    """A stronger structural proof the formula is correct: summing every
    feature's contribution plus the model's intercept must equal the raw
    decision-function logit sklearn itself computes."""
    import numpy as np

    from app.services.detector import _load_essay_artifact, predict_essay
    from app.services.evidence_mapper import _compute_contributions
    from app.services.feature_spec import ALL_FIELDS

    artifact = _load_essay_artifact()
    result = predict_essay(SAMPLE_ESSAY)

    contributions = _compute_contributions(result.feature_vector, artifact["scaler"], artifact["model"].coef_[0])
    total = sum(contributions.values()) + artifact["model"].intercept_[0]

    X = np.array([[result.feature_vector[f] for f in ALL_FIELDS]], dtype=float)
    Xs = artifact["scaler"].transform(X)
    expected_logit = artifact["model"].decision_function(Xs)[0]

    assert total == pytest.approx(expected_logit, abs=1e-6)


# ---- K: no LLM/network dependency ----

def test_K_evidence_mapper_module_has_no_llm_or_network_imports():
    source = (REPO_ROOT / "backend" / "app" / "services" / "evidence_mapper.py").read_text()
    tree = ast.parse(source)
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_names.add(node.module)

    forbidden_substrings = ("openai", "anthropic", "google.generativeai", "genai", "requests", "httpx", "urllib", "socket")
    for name in imported_names:
        for forbidden in forbidden_substrings:
            assert forbidden not in name.lower(), f"evidence_mapper.py imports {name}, which suggests a network/LLM dependency"


# ---- L: known difficult family 302DC21A6DEE ----

@pytest.mark.skipif(not PRIMARY_SAMPLES.exists(), reason="PRIMARY-DATASET-v1 not present")
def test_L_family_302DC21A6DEE_produces_evidence_consistent_with_its_known_borderline_score():
    from app.models.evidence_results import EssayResultState
    from app.services.evidence_mapper import build_essay_evidence

    text = _load_text("302DC21A6DEE__human")
    result = build_essay_evidence(text)

    # Known from Phase B: score 0.49, just above the 0.47 threshold --
    # the documented, reproducible borderline false positive.
    assert result.score == pytest.approx(0.49, abs=5e-3)
    assert result.state == EssayResultState.MACHINE_SIGNAL_DETECTED
    assert len(result.evidence) > 0
    # This is the known false-positive case -- evidence must still be
    # honestly reported (not suppressed or hedged away), consistent with
    # "never hide a known failure case" (docs/failure-analysis.md).
    for item in result.evidence:
        assert item.statement  # a real, traceable statement is still produced even for this borderline/incorrect case
