"""
Tests for GEN-001 (held-out cross-generator generalization, DEC-019).
Methodology tests only -- provenance, no-train-on-held-out-data,
feature-schema compatibility, split-value hygiene, and detector-freeze
reproduction. No test asserts a specific accuracy/F1 number: GEN-001's
result (strong transfer, collapse, or mixed) is a finding to report, not
a target to hit.

Tests that require the actual generated/evaluated GEN-001 artifacts skip
cleanly if those files are absent (e.g. running in an environment that
hasn't downloaded Phi-3.5-mini-instruct).
"""

import hashlib
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

GEN001_SAMPLES = REPO_ROOT / "data" / "generated" / "GEN-001" / "samples.jsonl"
GEN001_FEATURES = REPO_ROOT / "experiments" / "GEN-001" / "features_phi.jsonl"
GEN001_RESULTS = REPO_ROOT / "experiments" / "GEN-001" / "results.json"
PRIMARY_SAMPLES = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
PRIMARY_MANIFEST = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "inclusion_manifest.json"


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_primary_dataset_v1_unchanged_by_gen001():
    """The hard invariant this whole experiment depends on: PRIMARY-DATASET-v1
    must remain byte-identical to its frozen state, regardless of whether
    GEN-001 has run in this environment."""
    from run_gen001_generate import EXPECTED_MANIFEST_MD5, EXPECTED_SAMPLES_MD5

    assert _md5(PRIMARY_SAMPLES) == EXPECTED_SAMPLES_MD5
    assert _md5(PRIMARY_MANIFEST) == EXPECTED_MANIFEST_MD5


def test_gen001_held_out_split_value_is_distinct_from_primary_dataset_splits():
    """GEN-001 records must never be mistakable for a PRIMARY-DATASET-v1
    train/validation/test record by anything that filters on `split`."""
    from run_gen001_generate import make_gen001_record

    rec = make_gen001_record(
        sample_id="X__phi_full_ai", family_id="X", source_sample_id="X__human", text="a b c",
        target_length_words=3, generation_config={}, prompt_template_id="t",
        qc_status="passed", qc_notes=[], instruction_leakage_flagged=False, ai_self_reference_flagged=False,
    )
    assert rec["split"] not in ("train", "validation", "test")


def test_gen001_generated_samples_have_required_provenance():
    if not GEN001_SAMPLES.exists():
        pytest.skip("GEN-001 samples not present in this environment")
    records = [json.loads(line) for line in GEN001_SAMPLES.read_text().splitlines() if line.strip()]
    assert len(records) == 23
    for r in records:
        assert r["source_sample_id"] is not None and r["source_sample_id"].endswith("__human")
        assert r["generation_model"] == "microsoft/Phi-3.5-mini-instruct"
        assert r["generation_model_revision"]
        assert r["family_id"] == r["source_sample_id"].removesuffix("__human")
        assert r["label"] == "machine"
        assert r["transformation_type"] == "full_ai"


def test_gen001_sample_ids_disjoint_from_primary_dataset_v1():
    """GEN-001 must never be mergeable-by-accident into PRIMARY-DATASET-v1
    -- their sample_id namespaces must not collide."""
    if not GEN001_SAMPLES.exists():
        pytest.skip("GEN-001 samples not present in this environment")
    gen001_ids = {json.loads(line)["sample_id"] for line in GEN001_SAMPLES.read_text().splitlines() if line.strip()}
    primary_ids = {json.loads(line)["sample_id"] for line in PRIMARY_SAMPLES.read_text().splitlines() if line.strip()}
    assert gen001_ids.isdisjoint(primary_ids)


def test_gen001_source_essays_are_exactly_the_frozen_test_split_humans():
    if not GEN001_SAMPLES.exists():
        pytest.skip("GEN-001 samples not present in this environment")
    primary_records = [json.loads(line) for line in PRIMARY_SAMPLES.read_text().splitlines() if line.strip()]
    frozen_test_human_ids = {r["sample_id"] for r in primary_records if r["label"] == "human" and r["split"] == "test"}

    gen001_records = [json.loads(line) for line in GEN001_SAMPLES.read_text().splitlines() if line.strip()]
    gen001_source_ids = {r["source_sample_id"] for r in gen001_records}

    assert gen001_source_ids == frozen_test_human_ids


def test_gen001_features_use_the_same_29_field_schema_as_exp003a():
    if not GEN001_FEATURES.exists():
        pytest.skip("GEN-001 Phi features not present in this environment")
    from run_exp003a import ALL_FIELDS

    records = [json.loads(line) for line in GEN001_FEATURES.read_text().splitlines() if line.strip()]
    assert len(records) == 23
    for r in records:
        for f in ALL_FIELDS:
            assert f in r, f"missing feature {f} in Phi feature record {r['sample_id']}"
            assert r[f] is not None, f"unexpected missing value for {f} in {r['sample_id']}"


def test_gen001_evaluation_did_not_alter_the_frozen_exp003a_model():
    """The reproduction_check in results.json is the concrete evidence that
    refitting the model against the exact same train split/seed reproduces
    EXP-003A's frozen chosen_C values exactly -- i.e. nothing about the
    model was fit, tuned, or influenced by Phi data."""
    if not GEN001_RESULTS.exists():
        pytest.skip("GEN-001 results not present in this environment")
    results = json.loads(GEN001_RESULTS.read_text())
    assert all(results["reproduction_check"].values())
    assert results["frozen_threshold"] == 0.47


def test_gen001_evaluation_set_is_23_human_plus_23_phi_not_touching_train_or_validation():
    if not GEN001_RESULTS.exists():
        pytest.skip("GEN-001 results not present in this environment")
    results = json.loads(GEN001_RESULTS.read_text())
    assert results["phi_evaluation"]["n"] == 46
    assert results["phi_evaluation"]["class_counts"] == {"human": 23, "phi_full_ai": 23}
