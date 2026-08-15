"""
Result types for the deterministic evidence-mapping layer (Phase D,
DEC-017). No natural-language generation model is involved anywhere in
producing these -- every string is built from a fixed template plus a
measured value.
"""

from dataclasses import dataclass
from enum import Enum


class EssayResultState(str, Enum):
    """Three states, but NOT derived from an invented numerical score
    band (Phase D item 14): MACHINE_SIGNAL_DETECTED / NO_STRONG_SIGNAL_DETECTED
    map directly from the single already-frozen 0.47 threshold (the
    only experimentally-selected cutpoint that exists); INCONCLUSIVE is
    reserved exclusively for an explicitly-defined evidence-availability
    failure (the 29-feature vector could not be completed -- e.g. no
    LM-scorable tokens in the essay), never for a score falling in some
    invented "ambiguous" numeric range."""

    MACHINE_SIGNAL_DETECTED = "machine_signal_detected"
    NO_STRONG_SIGNAL_DETECTED = "no_strong_signal_detected"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class EvidenceItem:
    """One deterministic evidence statement, fully traceable (Phase D
    item 8): `feature` + `observed_value` + `contribution` are the raw
    numbers; `statement` is the fixed-template sentence built from them.
    Two identical inputs always produce an identical EvidenceItem."""

    feature: str
    human_label: str
    observed_value: float
    reference_mean: float
    reference_std: float
    direction: str  # "higher" or "lower", relative to reference_mean
    contribution: float  # coefficient * standardized_value -- see evidence_mapper.CONTRIBUTION_FORMULA_DOC
    statement: str


@dataclass(frozen=True)
class EssayEvidenceResult:
    state: EssayResultState
    score: float | None  # None only when state is INCONCLUSIVE (no score to show -- would be misleading to display one from an incomplete vector)
    threshold: float
    state_explanation: str  # fixed disclaimer text -- see evidence_mapper.ESSAY_SCORE_EXPLANATION
    evidence: list[EvidenceItem]
    limitation_note: str


@dataclass(frozen=True)
class SentenceEvidenceResult:
    sentence_index: int
    rank: int
    text: str
    char_start: int
    char_end: int
    score: float
    label: str  # always "potentially_ai_assisted" -- never "ai_written"/"ai_generated" (Phase C item 2)
    evidence: list[EvidenceItem]


@dataclass(frozen=True)
class SentenceLocalizationResult:
    """Presentation-layer wrapper around detector.SentenceRankingResult:
    applies the top-K limit (a documented UI default, not a research
    threshold -- Phase C item 2) and attaches evidence to each surfaced
    candidate. `top_k` is always recorded on the result so it's visible
    downstream that this is a configurable presentation setting, not a
    fixed model property.

    `normalized_text` and `skipped` are passed through unchanged from
    the single underlying `rank_sentences()` call this result was built
    from (never a second, separate call) -- so a caller (the API layer)
    never needs to re-run sentence ranking just to report offsets or
    skipped sentences."""

    candidates: list[SentenceEvidenceResult]
    top_k: int
    total_scorable_sentences: int
    has_evidence: bool
    no_evidence_reason: str | None  # set only when has_evidence is False
    disclaimer: str
    normalized_text: str
    skipped: list  # list[SkippedSentence] (from app.models.detector_results) -- passed through as-is
