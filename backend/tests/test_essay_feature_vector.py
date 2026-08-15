"""
Proves app.services.essay_feature_vector.extract_essay_feature_vector
is byte-for-byte equivalent to
scripts/exp003a_extract_features.py::extract_features_for_essay -- the
research function every EXP-003A/EXP-003B/EXP-003C/GEN-001 feature file
was built with. This production copy must never silently drift from
that computation (Phase B item 4: "Do not rewrite research feature
calculations merely for code style. If refactoring is necessary, first
prove equivalence with tests.") -- this file is that proof.

Skips cleanly if PRIMARY-DATASET-v1 / the cached EXP-003A features file
are not present in this environment (both gitignored).
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRIMARY_SAMPLES = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
EXP003A_FEATURES = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"


def _load_record(path: Path, sample_id: str) -> dict:
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            if rec["sample_id"] == sample_id:
                return rec
    raise KeyError(sample_id)


@pytest.mark.skipif(
    not (PRIMARY_SAMPLES.exists() and EXP003A_FEATURES.exists()),
    reason="PRIMARY-DATASET-v1 / EXP-003A features not present in this environment",
)
@pytest.mark.parametrize(
    "sample_id",
    ["1E9F7661E8EA__human", "1E9F7661E8EA__full_ai", "302DC21A6DEE__human", "302DC21A6DEE__full_ai"],
)
def test_production_essay_feature_vector_matches_recorded_exp003a_features(sample_id):
    from app.services.essay_feature_vector import extract_essay_feature_vector
    from app.services.feature_spec import ALL_FIELDS

    sample = _load_record(PRIMARY_SAMPLES, sample_id)
    recorded = _load_record(EXP003A_FEATURES, sample_id)

    fv = extract_essay_feature_vector(sample["text"])
    assert fv.is_complete(), f"unexpected missing fields for {sample_id}: {fv.missing_fields}"

    for field in ALL_FIELDS:
        produced = fv.values[field]
        expected = recorded[field]
        assert produced == pytest.approx(expected, abs=1e-9), f"{sample_id}.{field}: {produced} != {expected}"


def test_extract_essay_feature_vector_handles_empty_text_without_crashing():
    from app.services.essay_feature_vector import extract_essay_feature_vector

    fv = extract_essay_feature_vector("")
    assert not fv.is_complete()
    assert len(fv.missing_fields) == 29
