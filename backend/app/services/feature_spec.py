"""
Canonical 29-feature specification for the production detector (Phase
B). This is the SINGLE source of truth for feature name/order used by
the frozen EXP-003A (essay-level) and EXP-003B (sentence-level) models
-- every other module in this codebase (production or research) must
reference these lists rather than maintaining a second copy.

The names, order, and count (23 stylometric + 6 LM-derived = 29) are
copied verbatim from scripts/run_exp003a.py's STYLO_FIELDS/LM_FIELDS/
ALL_FIELDS -- the pre-registered feature set (DEC-014), unchanged since
before any experiment ran. This is a frozen, immutable list: adding,
removing, or reordering a field here would silently invalidate every
frozen model artifact built from it.
"""

from dataclasses import dataclass

STYLO_FIELDS: tuple[str, ...] = (
    "stylo_sentence_count", "stylo_sentence_length_mean", "stylo_sentence_length_std",
    "stylo_sentence_length_cv", "stylo_short_sentence_ratio", "stylo_medium_sentence_ratio",
    "stylo_long_sentence_ratio", "stylo_type_token_ratio", "stylo_moving_average_ttr",
    "stylo_rare_word_ratio", "stylo_repeated_bigram_ratio", "stylo_repeated_trigram_ratio",
    "stylo_repeated_sentence_opening_ratio", "stylo_mean_word_count", "stylo_mean_char_count",
    "stylo_mean_punctuation_count", "stylo_mean_avg_word_length", "stylo_mean_noun_ratio",
    "stylo_mean_verb_ratio", "stylo_mean_adj_ratio", "stylo_mean_adv_ratio",
    "stylo_mean_pronoun_ratio", "stylo_mean_dependency_depth",
)
LM_WITHIN_SENTENCE_FIELDS: tuple[str, ...] = (
    "lm_mean_mean_log_prob", "lm_mean_median_log_prob", "lm_mean_log_prob_variance",
    "lm_mean_perplexity", "lm_mean_token_count",
)
LM_NEIGHBOR_FIELD: tuple[str, ...] = ("lm_mean_predictability_delta",)
LM_FIELDS: tuple[str, ...] = LM_WITHIN_SENTENCE_FIELDS + LM_NEIGHBOR_FIELD
ALL_FIELDS: tuple[str, ...] = STYLO_FIELDS + LM_FIELDS

assert len(STYLO_FIELDS) == 23 and len(LM_FIELDS) == 6 and len(ALL_FIELDS) == 29
assert len(set(ALL_FIELDS)) == 29, "duplicate field name in ALL_FIELDS"

# Field position lookup -- used to enforce "any mismatch between
# extracted feature order and model input order must produce an
# explicit error" (Phase B spec, item 3).
FIELD_INDEX: dict[str, int] = {f: i for i, f in enumerate(ALL_FIELDS)}


# Essay-level (EssayFeatures) fields used as-is, and the SentenceFeatures/
# SentenceLMFeatures field names mean-pooled (essay-level) or read
# per-sentence (sentence-level) -- documented once here, matching
# exp003a_extract_features.py / exp003b_extract_features.py exactly.
ESSAY_LEVEL_FIELDS: tuple[str, ...] = (
    "sentence_count", "sentence_length_mean", "sentence_length_std", "sentence_length_cv",
    "short_sentence_ratio", "medium_sentence_ratio", "long_sentence_ratio",
    "type_token_ratio", "moving_average_ttr", "rare_word_ratio",
    "repeated_bigram_ratio", "repeated_trigram_ratio", "repeated_sentence_opening_ratio",
)
SENTENCE_LEVEL_FIELDS: tuple[str, ...] = (
    "word_count", "char_count", "punctuation_count", "avg_word_length",
    "noun_ratio", "verb_ratio", "adj_ratio", "adv_ratio", "pronoun_ratio", "dependency_depth",
)
LM_SENTENCE_FIELDS: tuple[str, ...] = ("mean_log_prob", "median_log_prob", "log_prob_variance", "perplexity", "token_count")

assert len(ESSAY_LEVEL_FIELDS) == 13 and len(SENTENCE_LEVEL_FIELDS) == 10 and len(LM_SENTENCE_FIELDS) == 5


@dataclass(frozen=True)
class FeatureVectorResult:
    """A 29-value feature vector plus explicit missing-value bookkeeping.
    `values` uses None (never 0.0 or a fabricated number) for any field
    that could not be computed -- callers must check `missing_fields`
    before scoring; a model must never silently receive a None."""

    values: dict[str, float | None]
    missing_fields: tuple[str, ...]

    def is_complete(self) -> bool:
        return len(self.missing_fields) == 0

    def as_ordered_vector(self) -> list[float]:
        """Raises if any field is missing -- callers must check
        is_complete() first; this never substitutes a value."""
        if not self.is_complete():
            raise ValueError(f"cannot build a model input vector: missing fields {self.missing_fields}")
        return [self.values[f] for f in ALL_FIELDS]
