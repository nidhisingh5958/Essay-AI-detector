"""
Sentence-level 29-feature vector extraction for the production
sentence-localization detector (Phase B). Production copy of the exact
per-sentence feature construction
scripts/exp003b_extract_features.py::build_sentence_level_features used
(the feature-computation portion only -- ground-truth labeling via
modified_spans has no meaning here since production essays have no
known AI-touched span).

Same 29 field names as essay_feature_vector.py, at a different,
task-appropriate granularity (documented adaptation, not a new feature
set, per DEC-014): the 13 essay-level fields are the WHOLE ESSAY's
values, shared as context across every sentence in it; the 10
sentence-own fields + 5 LM-within-sentence fields + 1 predictability
delta are THIS SENTENCE's own value, not pooled.

Missing-value behavior: a sentence whose LM-within-sentence features or
predictability_delta cannot be computed (no scorable tokens, or -- for
delta -- no preceding scored sentence) is marked missing, exactly
mirroring EXP-003B's own dataset-construction rule (129/1707 sentences
excluded, not imputed, in that experiment). The sentence-localization
model was fit on data that already excludes these rows -- scoring one
with fabricated values would be an out-of-distribution input, not a
neutral one.
"""

from dataclasses import dataclass

from app.services.feature_extractor import extract_essay_features, extract_sentence_features
from app.services.feature_spec import ESSAY_LEVEL_FIELDS, LM_SENTENCE_FIELDS, SENTENCE_LEVEL_FIELDS, FeatureVectorResult
from app.services.language_model import compute_predictability_deltas, compute_sentence_lm_features, compute_token_log_probs
from app.services.sentence_segmenter import parse_document, segment_sentences
from app.services.text_normalizer import normalize_text


@dataclass(frozen=True)
class SentenceCandidate:
    sentence_index: int
    text: str
    char_start: int
    char_end: int
    feature_vector: FeatureVectorResult


def extract_sentence_feature_vectors(text: str) -> list[SentenceCandidate]:
    """`char_start`/`char_end` in every returned candidate are offsets
    into `normalize_text(text)` -- NOT necessarily into the caller's
    original `text` if it wasn't already normalized (normalize_text can
    change string length: CRLF -> LF, control-character stripping).
    Callers needing to highlight these offsets against a displayed
    string MUST display `normalize_text(text)` (or, more directly, use
    detector.rank_sentences()'s `normalized_text` field, which is
    exactly this same string, guaranteed)."""
    text = normalize_text(text)  # idempotent -- safe even if the caller already normalized
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)
    if not sentences:
        return []

    essay_feats = extract_essay_features(doc, sentences)
    essay_level_shared = {f"stylo_{f}": getattr(essay_feats, f) for f in ESSAY_LEVEL_FIELDS}

    token_log_probs = compute_token_log_probs(text)
    lm_sent_feats = [compute_sentence_lm_features(s, token_log_probs) for s in sentences]
    deltas = compute_predictability_deltas(lm_sent_feats)

    candidates = []
    for idx, sent in enumerate(sentences):
        sent_feats = extract_sentence_features(sent.span)
        lm_feats = lm_sent_feats[idx]
        delta = deltas[idx]

        values: dict[str, float | None] = dict(essay_level_shared)
        for f in SENTENCE_LEVEL_FIELDS:
            values[f"stylo_mean_{f}"] = getattr(sent_feats, f)

        if lm_feats is not None:
            for f in LM_SENTENCE_FIELDS:
                values[f"lm_mean_{f}"] = getattr(lm_feats, f)
        else:
            for f in LM_SENTENCE_FIELDS:
                values[f"lm_mean_{f}"] = None
        values["lm_mean_predictability_delta"] = delta

        missing = tuple(sorted(f for f, v in values.items() if v is None))
        candidates.append(
            SentenceCandidate(
                sentence_index=idx,
                text=sent.text,
                char_start=sent.start_char,
                char_end=sent.end_char,
                feature_vector=FeatureVectorResult(values=values, missing_fields=missing),
            )
        )
    return candidates
