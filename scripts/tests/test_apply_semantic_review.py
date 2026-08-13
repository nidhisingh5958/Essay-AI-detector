import json

import pytest

from apply_semantic_review import apply_review


def _write_samples(tmp_path, records):
    path = tmp_path / "samples.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return path


def test_apply_review_updates_matching_records(tmp_path):
    path = _write_samples(
        tmp_path,
        [
            {"sample_id": "a", "semantic_preservation": "not_yet_reviewed"},
            {"sample_id": "b", "semantic_preservation": "not_yet_reviewed"},
        ],
    )
    summary = apply_review(str(path), {"a": ("preserved", "no change in meaning")})
    assert summary == {"updated": 1, "total_records": 2}

    records = [json.loads(line) for line in path.read_text().splitlines()]
    by_id = {r["sample_id"]: r for r in records}
    assert by_id["a"]["semantic_preservation"] == "preserved"
    assert by_id["a"]["semantic_preservation_notes"] == "no change in meaning"
    assert by_id["b"]["semantic_preservation"] == "not_yet_reviewed"


def test_apply_review_rejects_invalid_value(tmp_path):
    path = _write_samples(tmp_path, [{"sample_id": "a", "semantic_preservation": "not_yet_reviewed"}])
    with pytest.raises(ValueError, match="Invalid semantic_preservation"):
        apply_review(str(path), {"a": ("mostly_fine", "note")})


def test_apply_review_rejects_unknown_sample_id(tmp_path):
    path = _write_samples(tmp_path, [{"sample_id": "a", "semantic_preservation": "not_yet_reviewed"}])
    with pytest.raises(ValueError, match="not found"):
        apply_review(str(path), {"nonexistent": ("preserved", "note")})
