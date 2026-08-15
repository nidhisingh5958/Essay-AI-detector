"""
Result types for the production detector service (Phase B). Structured
data only -- no natural-language explanation text is generated here
(that is Phase D's deterministic evidence-mapper's job, per DEC-017).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EssayDetectionResult:
    """Output of the frozen EXP-003A essay-level detector.

    `score` is the frozen classifier's estimated probability of the
    positive class ("machine") under the EXP-003A combined model --
    NOT "probability AI definitely wrote this," not an "AI-assistance"
    probability, not a universal AI-detection probability. See
    docs/production-detector.md "Score semantics" for the exact,
    reviewed wording this must never be presented without.

    No confidence band is included: the three-state UI banding proposed
    in the product audit was never calibrated by any research protocol
    (no validation-score band edges exist anywhere in EXP-003A's
    results) -- see docs/production-detector.md for the explicit
    STOP-and-report on this point. Only the raw score and the
    already-frozen threshold decision are returned; banding is a Phase D
    decision, not invented here.
    """

    score: float
    label_at_threshold: str  # "machine" or "human", using the frozen 0.47 threshold -- nothing else
    threshold: float
    model_version: str
    source_experiment: str
    feature_vector: dict[str, float | None]
    missing_fields: tuple[str, ...]


@dataclass(frozen=True)
class SentenceScore:
    sentence_index: int
    text: str
    char_start: int
    char_end: int
    score: float  # the frozen sentence-localization model's P(ai_assisted) for this sentence
    rank: int  # 1-indexed; see SentenceRankingResult's docstring for the exact tie-break rule
    feature_vector: dict[str, float]  # this sentence's 29-feature values -- consumed by evidence_mapper.py (Phase D), never exposed as-is to an end user


@dataclass(frozen=True)
class SkippedSentence:
    sentence_index: int
    text: str
    char_start: int
    char_end: int
    reason: str  # e.g. "missing LM-derived features (no scorable tokens)"


@dataclass(frozen=True)
class SentenceRankingResult:
    """Output of the frozen EXP-003B sentence-localization model.

    `ranked` is sorted by score, descending, for EVERY sentence that
    could be scored -- NOT capped to a fixed top-K. How many to surface
    in a UI (K) was never fixed by any approved product specification
    (the product audit only proposed "K=1-3, tunable in UI copy") -- see
    docs/production-detector.md for the explicit STOP-and-report on this
    point. Truncating to a specific K is a Phase D/UI decision, not made
    here.

    This is a RANKING signal only. No per-sentence threshold exists or
    should be invented -- EXP-003B's own raw 0.34 threshold was shown to
    be degenerate (near-universal positive prediction) and must never be
    used to produce a per-sentence binary "AI-written" label.

    Tie-break rule (deterministic, Phase C item 5): sorted by `score`
    descending; sentences with an exactly equal score are ordered by
    `sentence_index` ascending (i.e. their original position in the
    essay). This is a presentation-stability rule, not a research
    finding -- it only matters for the (rare, floating-point-exact) case
    of two sentences scoring identically.

    `normalized_text` is the exact string every `char_start`/`char_end`
    offset in `ranked`/`skipped` refers to -- callers (a future API/UI)
    must highlight against THIS string, never the caller's original
    pre-normalization input, since normalization (line-ending
    canonicalization, control-character stripping, Unicode NFC) can
    change string length and would silently invalidate offsets computed
    against a different representation (Phase C item 4).

    `has_scorable_evidence` is an explicit, checkable signal for "no
    sentence-level evidence available" (Phase C item 3) -- true iff
    `ranked` is non-empty. Checking `len(ranked) == 0` directly also
    works; this property exists so callers don't have to remember to.
    """

    ranked: list[SentenceScore]
    skipped: list[SkippedSentence]
    model_version: str
    source_experiment: str
    normalized_text: str

    @property
    def has_scorable_evidence(self) -> bool:
        return len(self.ranked) > 0
