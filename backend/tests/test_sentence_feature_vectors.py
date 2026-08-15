"""
Proves app.services.sentence_feature_vectors.extract_sentence_feature_vectors
computes the same per-sentence feature values as
scripts/exp003b_extract_features.py::build_sentence_level_features did
for EXP-003B's sentence-localization dataset -- same design intent as
test_essay_feature_vector.py (Phase B item 4).

One disclosed, deliberate difference: the research script SKIPS writing
a row entirely for a sentence with missing LM-derived features (129/1707
excluded in EXP-003B). The production version returns a candidate for
EVERY sentence, explicitly marking missing fields on the ones that would
have been skipped -- "never silently drop a value" (Phase B item 11) is
a stricter production standard than the research file format needed.
This test therefore only compares sentences that DO have a recorded row
(by essay_sample_id + sentence_index), and additionally confirms the
production function still returns a (explicitly-marked) candidate for
sentences that don't.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRIMARY_SAMPLES = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
EXP003B_SENTENCE_FEATURES = REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl"

TEST_ESSAY_SAMPLE_ID = "016B35EDC7B8__sentence_light_controlled_v2"


def _load_text(sample_id: str) -> str:
    with open(PRIMARY_SAMPLES) as f:
        for line in f:
            rec = json.loads(line)
            if rec["sample_id"] == sample_id:
                return rec["text"]
    raise KeyError(sample_id)


@pytest.mark.skipif(
    not (PRIMARY_SAMPLES.exists() and EXP003B_SENTENCE_FEATURES.exists()),
    reason="PRIMARY-DATASET-v1 / EXP-003B sentence features not present in this environment",
)
def test_production_sentence_feature_vectors_match_recorded_exp003b_rows():
    from app.services.feature_spec import ALL_FIELDS
    from app.services.sentence_feature_vectors import extract_sentence_feature_vectors

    text = _load_text(TEST_ESSAY_SAMPLE_ID)
    candidates = extract_sentence_feature_vectors(text)
    by_index = {c.sentence_index: c for c in candidates}

    recorded_rows = [
        json.loads(line)
        for line in EXP003B_SENTENCE_FEATURES.read_text().splitlines()
        if line.strip() and json.loads(line)["essay_sample_id"] == TEST_ESSAY_SAMPLE_ID
    ]
    assert recorded_rows, "expected at least one recorded row for this essay"

    checked = 0
    for row in recorded_rows:
        idx = row["sentence_index"]
        candidate = by_index[idx]
        assert candidate.feature_vector.is_complete(), (
            f"sentence {idx} has a recorded row (meaning research kept it) but production marked it missing"
        )
        for field in ALL_FIELDS:
            produced = candidate.feature_vector.values[field]
            expected = row[field]
            assert produced == pytest.approx(expected, abs=1e-9), f"sentence {idx}.{field}: {produced} != {expected}"
        checked += 1

    assert checked == len(recorded_rows)


@pytest.mark.skipif(not PRIMARY_SAMPLES.exists(), reason="PRIMARY-DATASET-v1 not present in this environment")
def test_production_returns_a_candidate_for_every_sentence_including_ones_research_would_have_skipped():
    from app.services.sentence_feature_vectors import extract_sentence_feature_vectors

    text = _load_text(TEST_ESSAY_SAMPLE_ID)
    candidates = extract_sentence_feature_vectors(text)

    recorded_indices = {
        json.loads(line)["sentence_index"]
        for line in EXP003B_SENTENCE_FEATURES.read_text().splitlines()
        if line.strip() and json.loads(line)["essay_sample_id"] == TEST_ESSAY_SAMPLE_ID
    }
    all_indices = {c.sentence_index for c in candidates}

    # Production must never have FEWER candidates than research had rows
    # for -- it may have MORE (the ones research silently excluded).
    assert recorded_indices.issubset(all_indices)

    # The candidates NOT in recorded_indices (if any) are exactly the ones
    # research excluded for missing predictability_delta/LM features --
    # production must mark them explicitly missing, never fabricate them.
    for c in candidates:
        if c.sentence_index not in recorded_indices:
            assert not c.feature_vector.is_complete()


def test_extract_sentence_feature_vectors_handles_empty_text():
    from app.services.sentence_feature_vectors import extract_sentence_feature_vectors

    assert extract_sentence_feature_vectors("") == []
