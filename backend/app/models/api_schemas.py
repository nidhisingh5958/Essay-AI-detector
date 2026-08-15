"""
Public API request/response schemas for POST /api/analyze (Phase E).

These are the ONLY objects ever serialized to a client -- internal
service objects (EssayDetectionResult, SentenceRankingResult,
EssayEvidenceResult, SentenceLocalizationResult) are converted here, not
returned directly, so internal fields never accidentally leak (Phase E
item 5: "Do not expose internal implementation objects directly").

Deliberately NOT exposed to the client, per explicit instruction (item
3/18): the frozen model's C, its raw numeric threshold, the full
29-feature vector, model artifact file paths, or any other
implementation/configuration detail beyond a human-readable version
label. `state` alone conveys the threshold relationship qualitatively.
"""

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., description="The essay text to analyze.")


class EvidenceItemResponse(BaseModel):
    feature: str
    human_label: str
    observed_value: float
    reference_mean: float
    reference_std: float
    direction: str
    contribution: float
    statement: str


class EssayResultResponse(BaseModel):
    state: str  # "machine_signal_detected" | "no_strong_signal_detected" | "inconclusive"
    score: float | None
    state_explanation: str
    evidence: list[EvidenceItemResponse]
    limitation_note: str


class SentenceCandidateResponse(BaseModel):
    sentence_index: int
    rank: int
    text: str
    char_start: int
    char_end: int
    score: float
    label: str  # always "potentially_ai_assisted"
    evidence: list[EvidenceItemResponse]


class SkippedSentenceResponse(BaseModel):
    sentence_index: int
    text: str
    char_start: int
    char_end: int
    reason: str


class SentenceResultResponse(BaseModel):
    candidates: list[SentenceCandidateResponse]
    skipped: list[SkippedSentenceResponse]
    top_k: int
    total_scorable_sentences: int
    has_evidence: bool
    no_evidence_reason: str | None
    disclaimer: str


class AnalysisMetadata(BaseModel):
    essay_model_version: str
    essay_source_experiment: str
    sentence_model_version: str
    sentence_source_experiment: str


class AnalyzeResponse(BaseModel):
    """`analysis_id` is an opaque request identifier only -- it is NOT
    part of the analysis result and must be excluded from any
    determinism comparison (same text -> same everything else, but a
    fresh, different analysis_id every call is expected and correct)."""

    analysis_id: str
    normalized_text: str
    essay: EssayResultResponse
    sentences: SentenceResultResponse
    metadata: AnalysisMetadata


class ErrorResponse(BaseModel):
    detail: str
