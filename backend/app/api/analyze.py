"""
POST /api/analyze -- Phase E.

Orchestration and serialization ONLY. No detection logic lives here --
every number in the response is produced by the already-frozen Phase B/
C/D pipeline (app.services.detector, app.services.evidence_mapper).
This module's only jobs are: validate the request, call the existing
pipeline, convert its internal result objects into the public API
schema, and translate exceptions into HTTP responses. See
docs/api.md for the full contract.

Privacy (item 18): essay text is processed in memory only. It is never
written to disk, a database, or any persistent store by this module,
and the only thing logged is the essay's length -- never its content.
"""

import logging
import uuid

from fastapi import APIRouter, HTTPException

from app.models.api_schemas import (
    AnalysisMetadata,
    AnalyzeRequest,
    AnalyzeResponse,
    EssayResultResponse,
    EvidenceItemResponse,
    SentenceCandidateResponse,
    SentenceResultResponse,
    SkippedSentenceResponse,
)
from app.models.evidence_results import EvidenceItem
from app.services.detector import DetectorArtifactMissingError, _load_essay_artifact, _load_sentence_artifact
from app.services.evidence_mapper import DEFAULT_TOP_K_SENTENCES, build_essay_evidence, build_sentence_localization
from app.services.validation import EssayValidationError, validate_essay_text
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _evidence_to_response(items: list[EvidenceItem]) -> list[EvidenceItemResponse]:
    return [
        EvidenceItemResponse(
            feature=e.feature, human_label=e.human_label, observed_value=e.observed_value,
            reference_mean=e.reference_mean, reference_std=e.reference_std,
            direction=e.direction, contribution=e.contribution, statement=e.statement,
        )
        for e in items
    ]


@router.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    text = request.text

    try:
        validate_essay_text(text)
    except EssayValidationError as exc:
        if len(text) > settings.max_essay_chars:
            # 413: request exceeds the explicitly documented limit (config.py's
            # max_essay_chars, already enforced/tested since Phase 1 -- not a
            # new arbitrary maximum invented here).
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        # Empty / whitespace-only text -- a client-input validation failure.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    logger.info("Analyzing essay: %d characters", len(text))

    try:
        essay_evidence = build_essay_evidence(text)
        sentence_localization = build_sentence_localization(text, top_k=DEFAULT_TOP_K_SENTENCES)
    except DetectorArtifactMissingError as exc:
        # The frozen model artifact is missing/unloadable -- a service
        # readiness problem, not a bad request. Never returned as a
        # fake/successful analysis.
        logger.error("Detector artifact unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Analysis service is not ready. Please try again shortly.") from exc
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any unexpected failure must become a clean 500, never a fabricated result
        # Never leak file paths, model internals, or a raw stack trace to the client.
        logger.exception("Unexpected error during essay analysis")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while analyzing this essay.") from exc

    essay_response = EssayResultResponse(
        state=essay_evidence.state.value,
        score=essay_evidence.score,
        state_explanation=essay_evidence.state_explanation,
        evidence=_evidence_to_response(essay_evidence.evidence),
        limitation_note=essay_evidence.limitation_note,
    )

    sentence_response = SentenceResultResponse(
        candidates=[
            SentenceCandidateResponse(
                sentence_index=c.sentence_index, rank=c.rank, text=c.text,
                char_start=c.char_start, char_end=c.char_end, score=c.score,
                label=c.label, evidence=_evidence_to_response(c.evidence),
            )
            for c in sentence_localization.candidates
        ],
        skipped=[
            SkippedSentenceResponse(sentence_index=s.sentence_index, text=s.text, char_start=s.char_start, char_end=s.char_end, reason=s.reason)
            for s in sentence_localization.skipped
        ],
        top_k=sentence_localization.top_k,
        total_scorable_sentences=sentence_localization.total_scorable_sentences,
        has_evidence=sentence_localization.has_evidence,
        no_evidence_reason=sentence_localization.no_evidence_reason,
        disclaimer=sentence_localization.disclaimer,
    )

    essay_artifact = _load_essay_artifact()
    sentence_artifact = _load_sentence_artifact()

    return AnalyzeResponse(
        analysis_id=str(uuid.uuid4()),
        normalized_text=sentence_localization.normalized_text,
        essay=essay_response,
        sentences=sentence_response,
        metadata=AnalysisMetadata(
            essay_model_version=essay_artifact["model_version"],
            essay_source_experiment=essay_artifact["source_experiment"],
            sentence_model_version=sentence_artifact["model_version"],
            sentence_source_experiment=sentence_artifact["source_experiment"],
        ),
    )
