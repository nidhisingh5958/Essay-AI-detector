"""
Deterministic evidence mapper (Phase D, DEC-017). Converts the frozen
detector's measured feature values and coefficients into cautious,
traceable, human-readable evidence statements.

Architecture (exactly, no shortcuts):

    feature (raw extracted value)
      -> observed value
      -> reference interpretation (vs. the human-population reference
         statistics computed once, offline, from EXP-003A's frozen
         TRAIN-split human essays -- see scripts/build_feature_reference_stats.py)
      -> fixed template (FEATURE_LABELS + _build_statement below)
      -> evidence statement

This module NEVER calls an LLM, a chat API, or any generative model --
no network access of any kind. Every statement is a pure function of
(feature name, observed value, reference mean/std, coefficient). Two
identical inputs always produce an identical output (verified by test).
"""

from functools import lru_cache
from pathlib import Path

import json

from app.models.detector_results import EssayDetectionResult, SentenceRankingResult
from app.models.evidence_results import (
    EssayEvidenceResult,
    EssayResultState,
    EvidenceItem,
    SentenceEvidenceResult,
    SentenceLocalizationResult,
)
from app.services.detector import FeatureVectorIncompleteError, _load_essay_artifact, _load_sentence_artifact, predict_essay, rank_sentences
from app.services.feature_spec import ALL_FIELDS

REFERENCE_STATS_PATH = Path(__file__).resolve().parent.parent / "ml" / "feature_reference_stats.json"

# ---- Presentation-only defaults (Phase C/D: NOT experimentally
# calibrated, NOT research thresholds -- see docs/production-detector.md
# and docs/evidence-mapping.md for the disclosed reasoning). Callers may
# override either without touching any model. ----
DEFAULT_TOP_K_SENTENCES = 3
DEFAULT_TOP_N_EVIDENCE = 3

CONTRIBUTION_FORMULA_DOC = (
    "contribution[i] = model.coef_[i] * standardized_value[i], where "
    "standardized_value[i] = (observed_value[i] - scaler.mean_[i]) / scaler.scale_[i] "
    "-- i.e. exactly the per-feature term the frozen LogisticRegression sums (plus "
    "intercept) to produce its decision-function logit. This is a deterministic "
    "linear decomposition of the frozen, already-fit model -- not a new "
    "computation, not retraining, not a causal-importance measure."
)

ESSAY_SCORE_EXPLANATION = (
    "This score reflects the detector's learned distinction between the human-written "
    "and AI-generated essays in its reference data (PRIMARY-DATASET-v1, EXP-003A) -- "
    "it is not a universal probability that AI wrote this specific essay."
)

SENTENCE_DISCLAIMER = (
    "The highlighted passages indicate statistical patterns associated with the "
    "detector's reference data. They are not proof that AI wrote the passage."
)

ESSAY_LIMITATION_NOTE = (
    "This result is scoped to full-essay AI generation as tested against this "
    "detector's reference data (PERSUADE-derived human essays; Qwen2.5-1.5B-Instruct "
    "and Phi-3.5-mini-instruct generated essays). It does not assess lighter AI "
    "assistance or editing, and does not establish authorship with certainty."
)

FEATURE_LABELS: dict[str, str] = {
    "stylo_sentence_count": "number of sentences",
    "stylo_sentence_length_mean": "average sentence length",
    "stylo_sentence_length_std": "variation in sentence length",
    "stylo_sentence_length_cv": "relative variation in sentence length",
    "stylo_short_sentence_ratio": "proportion of short sentences",
    "stylo_medium_sentence_ratio": "proportion of medium-length sentences",
    "stylo_long_sentence_ratio": "proportion of long sentences",
    "stylo_type_token_ratio": "vocabulary diversity",
    "stylo_moving_average_ttr": "vocabulary diversity (windowed measure)",
    "stylo_rare_word_ratio": "use of uncommon words",
    "stylo_repeated_bigram_ratio": "repeated two-word phrases",
    "stylo_repeated_trigram_ratio": "repeated three-word phrases",
    "stylo_repeated_sentence_opening_ratio": "repeated sentence openings",
    "stylo_mean_word_count": "average words per sentence",
    "stylo_mean_char_count": "average characters per sentence",
    "stylo_mean_punctuation_count": "punctuation density",
    "stylo_mean_avg_word_length": "average word length",
    "stylo_mean_noun_ratio": "proportion of nouns",
    "stylo_mean_verb_ratio": "proportion of verbs",
    "stylo_mean_adj_ratio": "proportion of adjectives",
    "stylo_mean_adv_ratio": "proportion of adverbs",
    "stylo_mean_pronoun_ratio": "proportion of pronouns",
    "stylo_mean_dependency_depth": "sentence structural complexity",
    "lm_mean_mean_log_prob": "average predictability under the language-model instrument",
    "lm_mean_median_log_prob": "median predictability under the language-model instrument",
    "lm_mean_log_prob_variance": "variability of predictability under the language-model instrument",
    "lm_mean_perplexity": "perplexity under the language-model instrument",
    # Explicitly NOT called "predictability" -- EXP-003B-R1 found this is a length/count
    # proxy, not genuine LM-predictability evidence. The label reflects that finding.
    "lm_mean_token_count": "average token count (a length measure, not a predictability measure)",
    "lm_mean_predictability_delta": "change in predictability between neighboring sentences",
}
assert set(FEATURE_LABELS) == set(ALL_FIELDS), "every one of the 29 features must have a label -- none silently unlabeled"


@lru_cache(maxsize=1)
def _load_reference_stats() -> dict:
    if not REFERENCE_STATS_PATH.exists():
        raise RuntimeError(
            f"Feature reference stats not found at {REFERENCE_STATS_PATH}. "
            "Run scripts/build_feature_reference_stats.py first."
        )
    return json.loads(REFERENCE_STATS_PATH.read_text())


def _compute_contributions(feature_vector: dict[str, float], scaler, coef_row) -> dict[str, float]:
    """Returns {feature_name: contribution}, per CONTRIBUTION_FORMULA_DOC.
    Deterministic: a pure function of the already-frozen scaler/model
    and the observed feature values."""
    contributions = {}
    for i, f in enumerate(ALL_FIELDS):
        standardized = (feature_vector[f] - scaler.mean_[i]) / scaler.scale_[i]
        contributions[f] = float(coef_row[i] * standardized)
    return contributions


def _build_evidence_item(feature: str, observed: float, contribution: float, ref_stats: dict) -> EvidenceItem:
    ref = ref_stats["fields"][feature]
    ref_mean, ref_std = ref["mean"], ref["std"]
    direction = "higher" if observed > ref_mean else "lower"
    label = FEATURE_LABELS[feature]
    statement = (
        f"This shows a {direction} level of {label} than the reference range used by the detector "
        f"(observed {observed:.3f} vs. a human-reference average of {ref_mean:.3f})."
    )
    return EvidenceItem(
        feature=feature, human_label=label, observed_value=round(observed, 4),
        reference_mean=round(ref_mean, 4), reference_std=round(ref_std, 4),
        direction=direction, contribution=round(contribution, 6), statement=statement,
    )


def _select_top_evidence(feature_vector: dict[str, float], contributions: dict[str, float], top_n: int) -> list[EvidenceItem]:
    """Deterministic selection rule (Phase D item 12), documented exactly:
    1. discard any feature with a missing (None) observed value
    2. rank remaining features by absolute contribution, descending
    3. NO experimentally-established contribution floor exists -- none invented
    4. take the top `top_n`
    5. deterministic tie-break: canonical feature order (ALL_FIELDS index), ascending
    """
    ref_stats = _load_reference_stats()
    available = [f for f in ALL_FIELDS if feature_vector.get(f) is not None]
    field_index = {f: i for i, f in enumerate(ALL_FIELDS)}
    ranked = sorted(available, key=lambda f: (-abs(contributions[f]), field_index[f]))
    return [_build_evidence_item(f, feature_vector[f], contributions[f], ref_stats) for f in ranked[:top_n]]


def build_essay_evidence(text: str, top_n_evidence: int = DEFAULT_TOP_N_EVIDENCE) -> EssayEvidenceResult:
    artifact = _load_essay_artifact()
    try:
        result: EssayDetectionResult = predict_essay(text)
    except FeatureVectorIncompleteError:
        return EssayEvidenceResult(
            state=EssayResultState.INCONCLUSIVE,
            score=None,
            threshold=artifact["threshold"],
            state_explanation=(
                "Not enough scorable content was found in this essay (e.g. no language-model-scorable "
                "tokens) to produce a reliable result -- no score is reported rather than an unreliable one."
            ),
            evidence=[],
            limitation_note=ESSAY_LIMITATION_NOTE,
        )

    contributions = _compute_contributions(result.feature_vector, artifact["scaler"], artifact["model"].coef_[0])
    evidence = _select_top_evidence(result.feature_vector, contributions, top_n_evidence)

    state = EssayResultState.MACHINE_SIGNAL_DETECTED if result.label_at_threshold == "machine" else EssayResultState.NO_STRONG_SIGNAL_DETECTED

    return EssayEvidenceResult(
        state=state, score=result.score, threshold=result.threshold,
        state_explanation=ESSAY_SCORE_EXPLANATION, evidence=evidence, limitation_note=ESSAY_LIMITATION_NOTE,
    )


def build_sentence_localization(text: str, top_k: int = DEFAULT_TOP_K_SENTENCES, top_n_evidence: int = DEFAULT_TOP_N_EVIDENCE) -> SentenceLocalizationResult:
    artifact = _load_sentence_artifact()
    ranking: SentenceRankingResult = rank_sentences(text)

    if not ranking.has_scorable_evidence:
        reason = (
            "no scorable sentences (no sentences with sufficient language-model-scorable content)"
            if ranking.skipped or len(ranking.ranked) == 0
            else "no sentences found in the submitted text"
        )
        return SentenceLocalizationResult(
            candidates=[], top_k=top_k, total_scorable_sentences=0,
            has_evidence=False, no_evidence_reason=reason, disclaimer=SENTENCE_DISCLAIMER,
            normalized_text=ranking.normalized_text, skipped=ranking.skipped,
        )

    candidates = []
    for s in ranking.ranked[:top_k]:
        contributions = _compute_contributions(s.feature_vector, artifact["scaler"], artifact["model"].coef_[0])
        evidence = _select_top_evidence(s.feature_vector, contributions, top_n_evidence)
        candidates.append(
            SentenceEvidenceResult(
                sentence_index=s.sentence_index, rank=s.rank, text=s.text,
                char_start=s.char_start, char_end=s.char_end, score=s.score,
                label="potentially_ai_assisted", evidence=evidence,
            )
        )

    return SentenceLocalizationResult(
        candidates=candidates, top_k=top_k, total_scorable_sentences=len(ranking.ranked),
        has_evidence=True, no_evidence_reason=None, disclaimer=SENTENCE_DISCLAIMER,
        normalized_text=ranking.normalized_text, skipped=ranking.skipped,
    )
