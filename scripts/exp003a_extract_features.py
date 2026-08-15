"""
EXP-003A -- feature extraction (Stage 1). Computes the pre-registered
29-feature vector (DEC-014: 23 stylometric + 6 LM-derived) for every
`human`/`full_ai` record in PRIMARY-DATASET-v1's inclusion manifest.
No new features are computed beyond what feature-inventory.md already
lists as IMPLEMENTED -- see the "Essay-level aggregation" note below for
the one necessary, documented shape transformation (sentence-level ->
essay-level pooling), which is not a new feature, just making existing
per-sentence measurements usable for an essay-level classification task.

Essay-level aggregation (documented, not a new feature, per DEC-014):
- The 13 fields of EssayFeatures are already essay-level -- used as-is.
- The 10 fields of SentenceFeatures (word_count, char_count,
  punctuation_count, avg_word_length, noun/verb/adj/adv/pronoun_ratio,
  dependency_depth) are computed per sentence, then MEAN-POOLED across
  all sentences in the essay -- the single most standard aggregation,
  chosen to keep exactly 23 stylometric features total (10 + 13), matching
  DEC-014's pre-registered count.
- The 5 fields of SentenceLMFeatures (mean_log_prob, median_log_prob,
  log_prob_variance, perplexity, token_count) are MEAN-POOLED across all
  sentences with a scored value (None sentences skipped, not imputed).
- predictability_delta (one per sentence, None for the first sentence and
  any sentence with no scored tokens on either side) is MEAN-POOLED
  across non-None values -- the "neighboring-sentence predictability
  change" essay-level summary. Together with the 5 above: 6 LM-derived
  features total, matching DEC-014's pre-registered count.

Resumable: writes one JSON record per line, checks for already-computed
sample_ids at startup.
"""

import json
import sys
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.feature_extractor import extract_essay_features, extract_sentence_features  # noqa: E402
from app.services.language_model import (  # noqa: E402
    compute_predictability_deltas,
    compute_sentence_lm_features,
    compute_token_log_probs,
)
from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402

from exp003_data_prep import load_included_records  # noqa: E402

MANIFEST_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "inclusion_manifest.json"
SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
OUTPUT_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"

SENTENCE_FIELDS = (
    "word_count", "char_count", "punctuation_count", "avg_word_length",
    "noun_ratio", "verb_ratio", "adj_ratio", "adv_ratio", "pronoun_ratio", "dependency_depth",
)
ESSAY_FIELDS = (
    "sentence_count", "sentence_length_mean", "sentence_length_std", "sentence_length_cv",
    "short_sentence_ratio", "medium_sentence_ratio", "long_sentence_ratio",
    "type_token_ratio", "moving_average_ttr", "rare_word_ratio",
    "repeated_bigram_ratio", "repeated_trigram_ratio", "repeated_sentence_opening_ratio",
)
LM_SENTENCE_FIELDS = ("mean_log_prob", "median_log_prob", "log_prob_variance", "perplexity", "token_count")


def extract_features_for_essay(text: str) -> dict:
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc)

    essay_feats = extract_essay_features(doc, sentences)
    features = {f"stylo_{f}": getattr(essay_feats, f) for f in ESSAY_FIELDS}

    sent_feats_list = [extract_sentence_features(s.span) for s in sentences]
    for f in SENTENCE_FIELDS:
        values = [getattr(sf, f) for sf in sent_feats_list]
        features[f"stylo_mean_{f}"] = mean(values) if values else None

    token_log_probs = compute_token_log_probs(text)
    lm_sent_feats = [compute_sentence_lm_features(s, token_log_probs) for s in sentences]
    for f in LM_SENTENCE_FIELDS:
        values = [getattr(lf, f) for lf in lm_sent_feats if lf is not None]
        features[f"lm_mean_{f}"] = mean(values) if values else None

    deltas = compute_predictability_deltas(lm_sent_feats)
    non_none_deltas = [d for d in deltas if d is not None]
    features["lm_mean_predictability_delta"] = mean(non_none_deltas) if non_none_deltas else None

    features["n_sentences_scored_by_lm"] = sum(1 for lf in lm_sent_feats if lf is not None)
    features["n_sentences_total"] = len(sentences)
    return features


def main() -> None:
    records = load_included_records(str(MANIFEST_PATH), str(SAMPLES_PATH))
    records = [r for r in records if r["transformation_type"] in ("original", "full_ai")]
    print(f"EXP-003A essay-level records to featurize: {len(records)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    already_done = set()
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH) as f:
            for line in f:
                if line.strip():
                    already_done.add(json.loads(line)["sample_id"])
        print(f"Resuming: {len(already_done)} already featurized")

    with open(OUTPUT_PATH, "a") as f:
        for i, r in enumerate(records):
            if r["sample_id"] in already_done:
                continue
            print(f"[{i+1}/{len(records)}] {r['sample_id']}")
            feats = extract_features_for_essay(r["text"])
            out = {
                "sample_id": r["sample_id"],
                "family_id": r["family_id"],
                "split": r["split"],
                "label": r["label"],  # "human" or "machine"
                "transformation_type": r["transformation_type"],
                **feats,
            }
            f.write(json.dumps(out) + "\n")
            f.flush()

    print(f"Done. Wrote features to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
