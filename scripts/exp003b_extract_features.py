"""
EXP-003B -- feature extraction (Stage 1). Two separate feature files,
for two separate evaluations (never combined, per explicit instruction):

1. Essay-level: human (150) + ai_assisted (127) essays, using the exact
   same essay-level aggregation as EXP-003A
   (exp003a_extract_features.extract_features_for_essay) -- reuses
   EXP-003A's already-computed human feature vectors verbatim (same
   text, same deterministic function) rather than recomputing them, and
   extracts the 127 ai_assisted essays fresh.

2. Sentence-level (localization): every sentence of every included
   ai_assisted essay, labeled via the exact `modified_spans` provenance
   (DEC-016, exp003_data_prep.build_sentence_localization_labels) --
   never inferred by similarity. Uses the SAME pre-registered 29-feature
   inventory (DEC-014), but at its natural per-sentence granularity
   instead of essay-mean-pooled: the 10 SentenceFeatures + 5
   SentenceLMFeatures + 1 predictability_delta fields are the sentence's
   own values (not pooled); the 13 EssayFeatures fields are the
   sentence's essay's values (shared across all sentences in that
   essay, providing essay-level context). This is the minimal,
   documented adaptation needed for a sentence-level task -- not a new
   feature, the same 29 dimensions at a different, task-appropriate
   granularity (mirrors EXP-003A's own documented mean-pooling
   adaptation for the essay-level task).

Missing-value handling (documented, not silent): a sentence's
`predictability_delta` is undefined for the first sentence of an essay
(no preceding sentence to compare against) -- consistent with
language_model.py's existing "insufficient evidence, not a fabricated
delta" philosophy, these rows are EXCLUDED from the sentence-level
dataset, not imputed. The exact count excluded is reported at the end
of this script's run, and again in reports/EXP-003B.md.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.feature_extractor import extract_sentence_features  # noqa: E402
from app.services.language_model import (  # noqa: E402
    compute_predictability_deltas,
    compute_sentence_lm_features,
    compute_token_log_probs,
)
from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402

from exp003_data_prep import load_included_records  # noqa: E402
from exp003a_extract_features import (  # noqa: E402
    ESSAY_FIELDS,
    LM_SENTENCE_FIELDS,
    SENTENCE_FIELDS,
    extract_features_for_essay,
)

MANIFEST_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "inclusion_manifest.json"
SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
EXP003A_FEATURES_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
OUT_DIR = REPO_ROOT / "experiments" / "EXP-003B"
ESSAY_OUT_PATH = OUT_DIR / "features_essay.jsonl"
SENTENCE_OUT_PATH = OUT_DIR / "features_sentence.jsonl"


def build_essay_level_features() -> None:
    print("=== Essay-level feature extraction ===")
    cached_human = {}
    if EXP003A_FEATURES_PATH.exists():
        with open(EXP003A_FEATURES_PATH) as f:
            for line in f:
                rec = json.loads(line)
                if rec["label"] == "human":
                    cached_human[rec["sample_id"]] = rec
    print(f"Reusing {len(cached_human)} cached human essay feature vectors from EXP-003A")

    records = load_included_records(str(MANIFEST_PATH), str(SAMPLES_PATH))
    human_records = [r for r in records if r["transformation_type"] == "original"]
    ai_records = [r for r in records if r["transformation_type"] == "sentence_light_controlled_v2"]
    print(f"human essays: {len(human_records)}, ai_assisted essays: {len(ai_records)}")

    already_done = set()
    if ESSAY_OUT_PATH.exists():
        with open(ESSAY_OUT_PATH) as f:
            for line in f:
                if line.strip():
                    already_done.add(json.loads(line)["sample_id"])
        print(f"Resuming: {len(already_done)} already written")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(ESSAY_OUT_PATH, "a") as f:
        for r in human_records:
            if r["sample_id"] in already_done:
                continue
            cached = cached_human.get(r["sample_id"])
            if cached is None:
                raise RuntimeError(f"no cached EXP-003A features for {r['sample_id']} -- run exp003a_extract_features.py first")
            out = {
                "sample_id": r["sample_id"], "family_id": r["family_id"], "split": r["split"],
                "label": "human", "transformation_type": r["transformation_type"],
                **{k: v for k, v in cached.items() if k not in ("sample_id", "family_id", "split", "label", "transformation_type")},
            }
            f.write(json.dumps(out) + "\n")
            f.flush()

        for i, r in enumerate(ai_records):
            if r["sample_id"] in already_done:
                continue
            print(f"  [{i+1}/{len(ai_records)}] {r['sample_id']}")
            feats = extract_features_for_essay(r["text"])
            out = {
                "sample_id": r["sample_id"], "family_id": r["family_id"], "split": r["split"],
                "label": "ai_assisted", "transformation_type": r["transformation_type"], **feats,
            }
            f.write(json.dumps(out) + "\n")
            f.flush()
    print(f"Wrote essay-level features to {ESSAY_OUT_PATH}")


def build_sentence_level_features() -> None:
    print("\n=== Sentence-level (localization) feature extraction ===")
    from exp003_data_prep import build_sentence_localization_labels

    manifest = json.load(open(MANIFEST_PATH))
    all_records = {
        json.loads(line)["sample_id"]: json.loads(line)
        for line in SAMPLES_PATH.read_text().splitlines() if line.strip()
    }
    by_family: dict[str, dict] = {}
    for r in all_records.values():
        by_family.setdefault(r["family_id"], {})[r["transformation_type"]] = r

    ai_entries = [e for e in manifest["included"] if e["category"] == "ai_assisted"]
    print(f"ai_assisted essays for localization: {len(ai_entries)}")

    already_done_essays = set()
    if SENTENCE_OUT_PATH.exists():
        with open(SENTENCE_OUT_PATH) as f:
            for line in f:
                if line.strip():
                    already_done_essays.add(json.loads(line)["essay_sample_id"])
        print(f"Resuming: {len(already_done_essays)} essays already processed")

    n_excluded_missing_delta = 0
    n_total_sentences = 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(SENTENCE_OUT_PATH, "a") as f:
        for i, entry in enumerate(ai_entries):
            sid = entry["sample_id"]
            if sid in already_done_essays:
                continue
            rec = all_records[sid]
            human = by_family[rec["family_id"]]["original"]
            print(f"  [{i+1}/{len(ai_entries)}] {sid}")

            labels = build_sentence_localization_labels(human, rec)
            text = rec["text"]
            doc = parse_document(text)
            sentences = segment_sentences(text, doc=doc)
            assert len(sentences) == len(labels)

            essay_feats_obj = None
            from app.services.feature_extractor import extract_essay_features

            essay_feats_obj = extract_essay_features(doc, sentences)
            essay_level_shared = {f"stylo_{f}": getattr(essay_feats_obj, f) for f in ESSAY_FIELDS}

            token_log_probs = compute_token_log_probs(text)
            lm_sent_feats = [compute_sentence_lm_features(s, token_log_probs) for s in sentences]
            deltas = compute_predictability_deltas(lm_sent_feats)

            for sent_idx, (sent, (sent_text, label)) in enumerate(zip(sentences, labels)):
                n_total_sentences += 1
                sent_feats = extract_sentence_features(sent.span)
                lm_feats = lm_sent_feats[sent_idx]
                delta = deltas[sent_idx]

                if lm_feats is None or delta is None:
                    n_excluded_missing_delta += 1
                    continue

                row = {
                    "essay_sample_id": sid, "family_id": rec["family_id"], "split": rec["split"],
                    "sentence_index": sent_idx, "label": label,
                    **essay_level_shared,
                    **{f"stylo_mean_{fld}": getattr(sent_feats, fld) for fld in SENTENCE_FIELDS},
                    **{f"lm_mean_{fld}": getattr(lm_feats, fld) for fld in LM_SENTENCE_FIELDS},
                    "lm_mean_predictability_delta": delta,
                }
                f.write(json.dumps(row) + "\n")
                f.flush()

    print(f"Wrote sentence-level features to {SENTENCE_OUT_PATH}")
    print(f"Sentences seen this run: {n_total_sentences}, excluded for missing predictability_delta: {n_excluded_missing_delta}")


if __name__ == "__main__":
    build_essay_level_features()
    build_sentence_level_features()
