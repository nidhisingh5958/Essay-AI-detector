"""
Protocol/configuration-correctness checks for the FAIR-001 and GEN-001
DESIGN documents (DEC-018/DEC-019) -- verifies the factual claims those
designs are built on remain true, not the experiments themselves (which
have not been implemented or run). Skipped if the underlying data isn't
present in this environment.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PERSUADE_PATH = REPO_ROOT / "data" / "raw" / "persuade_2.0" / "persuade_2.0_human_scores_demo_id_github.csv"
SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
EXP003A_RESULTS_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "results.json"

pytestmark = pytest.mark.skipif(
    not (PERSUADE_PATH.exists() and SAMPLES_PATH.exists()),
    reason="PRIMARY-DATASET-v1 / PERSUADE source not present in this environment",
)


def test_fair001_ell_status_feasibility_claim_holds():
    # DEC-018's central rationale: only 1/23 test families have
    # ell_status=Yes, but 10/150 across the full dataset. If this ever
    # changes (e.g. PRIMARY-DATASET-v1 is superseded), DEC-018's design
    # response (score all 150 families, not just test) should be
    # revisited -- this test exists to catch that drift, not to assert
    # a result that shouldn't be allowed to change.
    df = pd.read_csv(PERSUADE_PATH, dtype={"essay_id_comp": str})
    ell_by_id = df.set_index("essay_id_comp")["ell_status"].to_dict()

    records = [json.loads(line) for line in SAMPLES_PATH.read_text().splitlines() if line.strip()]
    families = sorted({r["family_id"] for r in records})
    assert len(families) == 150

    from collections import Counter

    counts = Counter(ell_by_id.get(f) for f in families)
    assert counts["Yes"] == 10
    assert counts["No"] == 132

    if EXP003A_RESULTS_PATH.exists():
        a = json.loads(EXP003A_RESULTS_PATH.read_text())
        test_families = {p["family_id"] for p in a["test_predictions"]}
        assert len(test_families) == 23
        test_counts = Counter(ell_by_id.get(f) for f in test_families)
        assert test_counts["Yes"] == 1, "DEC-018's feasibility finding (1 Yes in test) no longer holds"


def test_fair001_no_demographic_field_reaches_any_feature_file():
    # DEC-018's hard rule, checked directly against real generated
    # output rather than only asserted in prose.
    sensitive_fields = {"gender", "race_ethnicity", "economically_disadvantaged", "student_disability_status", "ell_status"}
    records = [json.loads(line) for line in SAMPLES_PATH.read_text().splitlines()[:5] if line.strip()]
    for r in records:
        assert not (sensitive_fields & set(r.keys())), f"sensitive field leaked into sample record: {r['sample_id']}"

    for features_path in (
        REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl",
        REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl",
    ):
        if not features_path.exists():
            continue
        rec = json.loads(features_path.read_text().splitlines()[0])
        assert not (sensitive_fields & set(rec.keys())), f"sensitive field leaked into {features_path}"


def test_gen001_proposed_reuse_set_matches_exp003a_test_split_exactly():
    # GEN-001's design proposes reusing EXP-003A's exact 23 test-split
    # human essays. Verify that claim against the real, frozen artifact.
    if not EXP003A_RESULTS_PATH.exists():
        pytest.skip("EXP-003A results not present in this environment")
    a = json.loads(EXP003A_RESULTS_PATH.read_text())
    human_test_ids = {p["family_id"] for p in a["test_predictions"] if p["true_label"] == "human"}
    assert len(human_test_ids) == 23
