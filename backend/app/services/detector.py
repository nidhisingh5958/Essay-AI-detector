"""
Production detector service (Phase B). Loads the frozen, pre-built
model artifacts (backend/app/ml/*.joblib -- see
scripts/build_essay_detector_artifact.py / build_sentence_detector_artifact.py
for how they were produced and verified against EXP-003A/EXP-003B's
recorded results) and exposes inference-only scoring.

Hard rules, enforced by this module:
- No training code, no data-fitting code, anywhere in this file.
- Each artifact is loaded once per process (lru_cache) and reused for
  every request -- never reloaded per call.
- If an artifact is missing or malformed, loading fails loudly at first
  use (an explicit RuntimeError), never silently falls back to a
  different model or an untrained one.
- Feature order is read from the artifact itself (`feature_order`), not
  hardcoded a second time here -- the artifact and
  app.services.feature_spec.ALL_FIELDS are asserted equal at load time,
  so a future accidental reordering in either place fails immediately
  rather than silently scoring against the wrong column.
- No natural-language explanation is produced here -- see
  app/models/detector_results.py's docstrings for what IS and is not in
  scope for this phase.
"""

from functools import lru_cache
from pathlib import Path

import joblib

from app.models.detector_results import EssayDetectionResult, SentenceRankingResult, SentenceScore, SkippedSentence
from app.services.essay_feature_vector import extract_essay_feature_vector
from app.services.feature_spec import ALL_FIELDS
from app.services.sentence_feature_vectors import extract_sentence_feature_vectors
from app.services.text_normalizer import normalize_text

ML_DIR = Path(__file__).resolve().parent.parent / "ml"
ESSAY_ARTIFACT_PATH = ML_DIR / "essay_detector_v1.joblib"
SENTENCE_ARTIFACT_PATH = ML_DIR / "sentence_detector_v1.joblib"


class DetectorArtifactMissingError(RuntimeError):
    """Raised when a required model artifact file does not exist.
    Callers (API startup) should treat this as fatal -- never serve
    requests with a partially-loaded or absent detector."""


class FeatureVectorIncompleteError(RuntimeError):
    """Raised when a feature vector has one or more missing fields and
    cannot be safely scored. Never caught silently to substitute a
    fabricated score."""


def _load_artifact(path: Path) -> dict:
    if not path.exists():
        raise DetectorArtifactMissingError(
            f"Model artifact not found at {path}. Run the corresponding "
            f"scripts/build_*_detector_artifact.py script first -- this service never trains a replacement."
        )
    artifact = joblib.load(path)
    if list(artifact["feature_order"]) != list(ALL_FIELDS):
        raise RuntimeError(
            f"Artifact feature order at {path} does not match app.services.feature_spec.ALL_FIELDS -- "
            "refusing to score with a mismatched feature ordering. Rebuild the artifact."
        )
    return artifact


@lru_cache(maxsize=1)
def _load_essay_artifact() -> dict:
    return _load_artifact(ESSAY_ARTIFACT_PATH)


@lru_cache(maxsize=1)
def _load_sentence_artifact() -> dict:
    return _load_artifact(SENTENCE_ARTIFACT_PATH)


def predict_essay(text: str) -> EssayDetectionResult:
    """Score `text` with the frozen EXP-003A essay-level detector.

    Raises FeatureVectorIncompleteError if any of the 29 features could
    not be computed (e.g. no LM-scorable tokens anywhere in the essay)
    -- never substitutes a value and never returns a score computed from
    an incomplete vector.
    """
    artifact = _load_essay_artifact()
    fv = extract_essay_feature_vector(text)
    if not fv.is_complete():
        raise FeatureVectorIncompleteError(
            f"Cannot score essay: missing features {fv.missing_fields}. "
            "This essay has no scorable content for the LM instrument (or is otherwise degenerate) -- "
            "no fabricated score will be produced."
        )

    import numpy as np

    X = np.array([fv.as_ordered_vector()], dtype=float)
    Xs = artifact["scaler"].transform(X)
    score = float(artifact["model"].predict_proba(Xs)[0, 1])
    label = "machine" if score >= artifact["threshold"] else "human"

    return EssayDetectionResult(
        score=round(score, 4),
        label_at_threshold=label,
        threshold=artifact["threshold"],
        model_version=artifact["model_version"],
        source_experiment=artifact["source_experiment"],
        feature_vector=fv.values,
        missing_fields=fv.missing_fields,
    )


def rank_sentences(text: str) -> SentenceRankingResult:
    """Score every scorable sentence in `text` with the frozen EXP-003B
    sentence-localization detector and return them sorted by score,
    descending -- NOT truncated to a fixed top-K (top-K is a Phase D
    presentation decision, see evidence_mapper.py's
    DEFAULT_TOP_K_SENTENCES). Sentences that cannot be scored (missing
    LM-derived features) are returned separately in `skipped`, never
    silently dropped or assigned a fabricated score.

    Text is normalized once, here, and the exact normalized string is
    returned as `normalized_text` -- every offset in `ranked`/`skipped`
    refers to THIS string (Phase C item 4). Never re-derive/re-normalize
    separately downstream and apply these offsets to a different string.
    """
    artifact = _load_sentence_artifact()
    normalized = normalize_text(text)
    candidates = extract_sentence_feature_vectors(normalized)  # idempotent re-normalize inside -- no-op here

    ranked: list[SentenceScore] = []
    skipped: list[SkippedSentence] = []

    import numpy as np

    for c in candidates:
        if not c.feature_vector.is_complete():
            skipped.append(
                SkippedSentence(
                    sentence_index=c.sentence_index, text=c.text,
                    char_start=c.char_start, char_end=c.char_end,
                    reason=f"missing features: {c.feature_vector.missing_fields}",
                )
            )
            continue
        X = np.array([c.feature_vector.as_ordered_vector()], dtype=float)
        Xs = artifact["scaler"].transform(X)
        score = float(artifact["model"].predict_proba(Xs)[0, 1])
        ranked.append(
            SentenceScore(
                sentence_index=c.sentence_index, text=c.text,
                char_start=c.char_start, char_end=c.char_end,
                score=round(score, 4),
                rank=0,  # placeholder, assigned below after the deterministic sort
                feature_vector=dict(c.feature_vector.values),
            )
        )

    # Deterministic tie-break (Phase C item 5): score descending, then
    # sentence_index ascending. Explicit, not relying on sort stability
    # + insertion order (which happens to already be index-ascending,
    # but stating the rule explicitly avoids depending on that
    # incidental fact).
    ranked.sort(key=lambda s: (-s.score, s.sentence_index))
    ranked = [
        SentenceScore(
            sentence_index=s.sentence_index, text=s.text, char_start=s.char_start, char_end=s.char_end,
            score=s.score, rank=i + 1, feature_vector=s.feature_vector,
        )
        for i, s in enumerate(ranked)
    ]

    return SentenceRankingResult(
        ranked=ranked,
        skipped=skipped,
        model_version=artifact["model_version"],
        source_experiment=artifact["source_experiment"],
        normalized_text=normalized,
    )
