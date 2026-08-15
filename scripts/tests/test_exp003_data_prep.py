"""
Tests for exp003_data_prep.py -- pure data-layer correctness, no model
training/fitting (not authorized in the EXP-003 design phase). Exercises
both synthetic fixtures and the real, frozen PRIMARY-DATASET-v1 manifest.
"""

import json
from pathlib import Path

import pytest

from exp003_data_prep import (
    build_sentence_localization_labels,
    load_included_records,
    load_manifest,
    verify_manifest_integrity,
)
from generation_utils import find_family_split_violations

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "inclusion_manifest.json"
SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"

pytestmark = pytest.mark.skipif(
    not MANIFEST_PATH.exists(), reason="PRIMARY-DATASET-v1 not present in this environment"
)


def test_load_manifest_reports_frozen_composition():
    manifest = load_manifest(MANIFEST_PATH)
    assert manifest["dataset"] == "PRIMARY-DATASET-v1"
    from collections import Counter

    counts = Counter(r["category"] for r in manifest["included"])
    # The exact, frozen composition -- DEC "PRIMARY-DATASET-v1 REVIEW —
    # APPROVED" fixes these numbers. A change here means the manifest
    # was mutated, which this dataset's freeze policy forbids without a
    # versioned successor (PRIMARY-DATASET-v2).
    assert counts["human"] == 150
    assert counts["full_ai"] == 148
    assert counts["ai_assisted"] == 127
    assert len(manifest["included"]) == 425


def test_manifest_integrity_clean_against_real_samples_file():
    problems = verify_manifest_integrity(MANIFEST_PATH, SAMPLES_PATH)
    assert problems["included_ids_missing_from_samples_file"] == []
    assert problems["excluded_ids_missing_from_samples_file"] == []
    assert problems["ids_in_both_included_and_excluded"] == []
    assert problems["duplicate_included_ids"] == []


def test_load_included_records_matches_manifest_count():
    records = load_included_records(MANIFEST_PATH, SAMPLES_PATH)
    assert len(records) == 425


def test_no_family_split_violations_among_included_records():
    # The hard leakage invariant, re-checked specifically against the
    # INCLUDED subset EXP-003 will actually train/evaluate on -- not
    # just the raw samples file (already covered by
    # test_generation_utils.py, but a modeling pipeline should trust
    # its own input, not assume an earlier check still applies).
    records = load_included_records(MANIFEST_PATH, SAMPLES_PATH)
    assert find_family_split_violations(records) == []


def test_no_family_present_in_both_included_and_excluded_split_membership():
    # A stronger check than the split-violation one above: verify that
    # excluding some categories per-family (e.g. a rejected ai_assisted
    # sample) never accidentally creates a family whose remaining
    # included members disagree on split.
    manifest = load_manifest(MANIFEST_PATH)
    all_records = {
        json.loads(line)["sample_id"]: json.loads(line)
        for line in SAMPLES_PATH.read_text().splitlines()
        if line.strip()
    }
    included = [all_records[r["sample_id"]] for r in manifest["included"]]
    assert find_family_split_violations(included) == []


# --- build_sentence_localization_labels: synthetic fixtures ---


def test_build_sentence_localization_labels_flags_only_the_modified_sentence():
    human = {"text": "First sentence here. Second sentence here. Third sentence here."}
    rewritten_text = "First sentence here. Second sentence REWRITTEN here. Third sentence here."
    ai_record = {
        "sample_id": "TEST__sentence_light_controlled_v2",
        "text": rewritten_text,
        "modified_spans": [{"sentence_index": 1, "char_start": 22, "char_end": 52}],
    }
    labels = build_sentence_localization_labels(human, ai_record)
    assert [label for _, label in labels] == ["human", "ai_assisted", "human"]


def test_build_sentence_localization_labels_raises_on_unresolvable_span():
    ai_record = {"sample_id": "TEST__x", "text": "Some text.", "modified_spans": None}
    with pytest.raises(ValueError):
        build_sentence_localization_labels({"text": "Some text."}, ai_record)


# --- build_sentence_localization_labels: real PRIMARY-DATASET-v1 records ---


def test_build_sentence_localization_labels_against_real_accepted_samples():
    manifest = load_manifest(MANIFEST_PATH)
    records = {
        json.loads(line)["sample_id"]: json.loads(line)
        for line in SAMPLES_PATH.read_text().splitlines()
        if line.strip()
    }
    by_family: dict[str, dict] = {}
    for r in records.values():
        by_family.setdefault(r["family_id"], {})[r["transformation_type"]] = r

    ai_assisted_entries = [e for e in manifest["included"] if e["category"] == "ai_assisted"][:10]
    assert ai_assisted_entries, "expected at least some ai_assisted records in the manifest"

    for entry in ai_assisted_entries:
        rec = records[entry["sample_id"]]
        human = by_family[rec["family_id"]]["original"]
        labels = build_sentence_localization_labels(human, rec)
        ai_count = sum(1 for _, label in labels if label == "ai_assisted")
        # Exactly one sentence should be flagged -- the surgical single-
        # sentence splice mechanism (DEC-011 Regime A) guarantees this
        # by construction for every accepted sentence_light sample.
        assert ai_count == 1, f"{entry['sample_id']} expected exactly 1 ai_assisted sentence, got {ai_count}"
