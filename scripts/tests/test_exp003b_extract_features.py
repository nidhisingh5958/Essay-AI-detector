"""
Regression checks for exp003b_extract_features.py's real output --
verifies the documented missing-value handling (EXP-003B §4) actually
holds in the generated data, not just in prose. Skipped if the
experiment hasn't been run in this environment.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ESSAY_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl"
SENTENCE_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_sentence.jsonl"

pytestmark = pytest.mark.skipif(
    not (ESSAY_PATH.exists() and SENTENCE_PATH.exists()), reason="EXP-003B features not present in this environment"
)


def _load(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_essay_level_features_cover_all_human_and_ai_assisted_essays():
    records = _load(ESSAY_PATH)
    from collections import Counter

    counts = Counter(r["label"] for r in records)
    assert counts["human"] == 150
    assert counts["ai_assisted"] == 127
    assert len(records) == 277


def test_essay_level_features_have_no_missing_values():
    records = _load(ESSAY_PATH)
    from run_exp003a import ALL_FIELDS

    for r in records:
        for f in ALL_FIELDS:
            assert r.get(f) is not None, f"{r['sample_id']} missing {f}"


def test_sentence_level_features_every_row_has_a_defined_predictability_delta():
    # The documented exclusion (EXP-003B §4): any row present in this
    # file must have a real, non-None predictability_delta -- rows
    # without one are excluded upstream, never written with a fabricated value.
    records = _load(SENTENCE_PATH)
    assert len(records) > 0
    for r in records:
        assert r["lm_mean_predictability_delta"] is not None


def test_sentence_level_features_cover_119_of_127_essays_with_a_locatable_positive():
    # 8 of 127 ai_assisted essays have their AI-edited sentence at index
    # 0 (undefined predictability_delta) and so contribute zero
    # ai_assisted-labeled rows -- documented, not silent, EXP-003B §2/§4.
    records = _load(SENTENCE_PATH)
    essays_with_positive = {r["essay_sample_id"] for r in records if r["label"] == "ai_assisted"}
    all_essays = {r["essay_sample_id"] for r in records}
    assert len(all_essays) == 127
    assert len(essays_with_positive) == 119
