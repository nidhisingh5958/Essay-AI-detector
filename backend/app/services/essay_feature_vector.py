"""
Essay-level 29-feature vector extraction for the production detector
(Phase B). This is the production copy of the exact computation
scripts/exp003a_extract_features.py::extract_features_for_essay has used,
unchanged, since EXP-003A -- every essay-level experiment (EXP-003A,
EXP-003B's human rows, EXP-003C, GEN-001) computed its feature vectors
this way. Reproduced here (not imported from scripts/) because
production code must never import research/experiment-runner modules
(research/production separation, Phase B item 14) -- the two copies are
verified byte-for-byte equivalent by
backend/tests/test_essay_feature_vector.py, which recomputes features
for real PRIMARY-DATASET-v1 essay text and compares against the
already-recorded values in experiments/EXP-003A/features.jsonl.

Essay-level aggregation (documented, not a new feature, per DEC-014):
- The 13 EssayFeatures fields are already essay-level -- used as-is.
- The 10 SentenceFeatures fields are computed per sentence, then
  mean-pooled across all sentences in the essay.
- The 5 SentenceLMFeatures fields are mean-pooled across all sentences
  with a scored value (a sentence with no scorable tokens is skipped,
  never imputed).
- predictability_delta is mean-pooled across sentences where it is
  defined (undefined for the first sentence, or a sentence with no
  scorable tokens on either side).

Missing-value behavior (never fabricated, per the standing project
rule): if EVERY sentence in the essay has no LM-scorable tokens, the
five LM-within-sentence fields and predictability_delta are explicitly
marked missing (None) rather than defaulting to 0.0 -- 0.0 is not a
semantically valid "no information" value for a log-probability/
perplexity feature. Downstream (detector.py), a feature vector with any
missing field cannot be scored by the frozen model and must produce a
structured error, never a fabricated prediction.
"""

from statistics import mean

from app.services.feature_extractor import extract_essay_features, extract_sentence_features
from app.services.feature_spec import ESSAY_LEVEL_FIELDS, FeatureVectorResult, LM_SENTENCE_FIELDS, SENTENCE_LEVEL_FIELDS
from app.services.language_model import compute_predictability_deltas, compute_sentence_lm_features, compute_token_log_probs
from app.services.sentence_segmenter import parse_document, segment_sentences
from app.services.text_normalizer import normalize_text


def extract_essay_feature_vector(text: str) -> FeatureVectorResult:
    # normalize_text is idempotent (verified: backend/tests/test_text_normalizer.py) --
    # safe to call here even if the caller already normalized. Ensures this
    # function is correct standalone, not just when called from detector.py.
    text = normalize_text(text)
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)

    values: dict[str, float | None] = {}

    if not sentences:
        # No sentences at all -- every field is undefined; validation.py
        # should reject empty/too-short input before this is ever
        # reached, but this function must never crash or fabricate a
        # value if it somehow is.
        missing = tuple(
            [f"stylo_{f}" for f in ESSAY_LEVEL_FIELDS]
            + [f"stylo_mean_{f}" for f in SENTENCE_LEVEL_FIELDS]
            + [f"lm_mean_{f}" for f in LM_SENTENCE_FIELDS]
            + ["lm_mean_predictability_delta"]
        )
        return FeatureVectorResult(values=dict.fromkeys(missing), missing_fields=missing)

    essay_feats = extract_essay_features(doc, sentences)
    for f in ESSAY_LEVEL_FIELDS:
        values[f"stylo_{f}"] = getattr(essay_feats, f)

    sent_feats_list = [extract_sentence_features(s.span) for s in sentences]
    for f in SENTENCE_LEVEL_FIELDS:
        vals = [getattr(sf, f) for sf in sent_feats_list]
        values[f"stylo_mean_{f}"] = mean(vals) if vals else None

    token_log_probs = compute_token_log_probs(text)
    lm_sent_feats = [compute_sentence_lm_features(s, token_log_probs) for s in sentences]
    for f in LM_SENTENCE_FIELDS:
        vals = [getattr(lf, f) for lf in lm_sent_feats if lf is not None]
        values[f"lm_mean_{f}"] = mean(vals) if vals else None

    deltas = compute_predictability_deltas(lm_sent_feats)
    non_none_deltas = [d for d in deltas if d is not None]
    values["lm_mean_predictability_delta"] = mean(non_none_deltas) if non_none_deltas else None

    missing = tuple(sorted(f for f, v in values.items() if v is None))
    return FeatureVectorResult(values=values, missing_fields=missing)
