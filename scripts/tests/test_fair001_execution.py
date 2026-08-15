"""
Tests for FAIR-001 execution (run_fair001_score_all.py,
run_fair001_fairness_analysis.py). Methodology/implementation
correctness only -- subgroup joins, the n<10 threshold rule, FP/FN
calculation correctness, score aggregation, and no-demographic-leakage.
No test asserts a specific fairness outcome (no disparity / disparity
found) -- that is a finding to report, not a target to hit.

Tests requiring actual FAIR-001 execution artifacts skip cleanly if
those files are absent.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FAIR001_DIR = REPO_ROOT / "experiments" / "FAIR-001"

import sys  # noqa: E402

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from run_fair001_fairness_analysis import (  # noqa: E402
    DEMOGRAPHIC_FIELDS,
    MIN_SUBGROUP_N,
    ellipse_secondary_analysis,
    score_summary,
    subgroup_report,
    verify_no_demographic_leakage,
    wilson_interval,
)


def test_min_subgroup_n_threshold_is_10_per_dec018():
    assert MIN_SUBGROUP_N == 10


def test_verify_no_demographic_leakage_passes_on_real_feature_files():
    leaks = verify_no_demographic_leakage()
    assert leaks == {}


def test_subgroup_report_applies_insufficient_data_below_threshold():
    records = [
        {"family_id": f"fam{i}", "false_positive": False, "false_negative": False, "score": 0.1}
        for i in range(9)
    ]  # n=9, below MIN_SUBGROUP_N=10
    ell_status = {f"fam{i}": "Yes" for i in range(9)}
    report = subgroup_report(records, ell_status, "human_false_positive")
    assert report["Yes"]["n"] == 9
    assert report["Yes"]["sufficient_data"] is False
    assert report["Yes"]["error_rate_95ci"] is None
    assert "INSUFFICIENT DATA" in report["Yes"]["note"]


def test_subgroup_report_computes_rate_at_exactly_10():
    records = [
        {"family_id": f"fam{i}", "false_positive": (i < 2), "false_negative": False, "score": 0.1}
        for i in range(10)
    ]  # n=10, exactly at threshold -- DEC-018 says "fewer than 10", so 10 itself is sufficient
    ell_status = {f"fam{i}": "Yes" for i in range(10)}
    report = subgroup_report(records, ell_status, "human_false_positive")
    assert report["Yes"]["n"] == 10
    assert report["Yes"]["sufficient_data"] is True
    assert report["Yes"]["error_count"] == 2
    assert report["Yes"]["error_rate"] == 0.2
    assert report["Yes"]["error_rate_95ci"] is not None


def test_subgroup_report_false_positive_vs_false_negative_role_selects_correct_field():
    records = [
        {"family_id": "fam0", "false_positive": True, "false_negative": False, "score": 0.9},
    ] * 10
    ell_status = {"fam0": "No"}
    fp_report = subgroup_report(records, ell_status, "human_false_positive")
    fn_report = subgroup_report(records, ell_status, "ai_false_negative")
    assert fp_report["No"]["error_count"] == 10
    assert fn_report["No"]["error_count"] == 0


def test_wilson_interval_contains_point_estimate():
    lo, hi = wilson_interval(5, 10)
    assert lo <= 0.5 <= hi
    assert 0 <= lo <= hi <= 1


def test_wilson_interval_zero_n_is_nan():
    lo, hi = wilson_interval(0, 0)
    assert lo != lo  # NaN != NaN
    assert hi != hi


def test_score_summary_basic_stats():
    summary = score_summary([0.1, 0.2, 0.3, 0.4, 0.5])
    assert summary["n"] == 5
    assert summary["mean"] == 0.3
    assert summary["median"] == 0.3
    assert summary["min"] == 0.1
    assert summary["max"] == 0.5


def test_score_summary_empty_list():
    assert score_summary([]) == {"n": 0}


def test_ellipse_secondary_analysis_flags_insufficient_data_and_no_statistic():
    exp003a_scored = [{"family_id": "fam0", "true_label": "human", "score": 0.2}]
    ell_status = {"fam0": "Yes"}
    ellipse = {"fam0": {"Overall": 3.5}}
    result = ellipse_secondary_analysis(exp003a_scored, ell_status, ellipse)
    assert result["n"] == 1
    assert result["sufficient_data"] is False
    assert "INSUFFICIENT DATA" in result["note"]
    assert "correlation" not in json.dumps(result).lower().replace("no correlation statistic computed or claimed", "")


def test_demographic_fields_list_matches_dec018():
    assert set(DEMOGRAPHIC_FIELDS) == {
        "gender", "race_ethnicity", "economically_disadvantaged", "student_disability_status", "ell_status",
    }


# ---- Execution-artifact tests (skip if FAIR-001 has not been run) ----

def test_exp003a_scored_covers_all_150_families():
    path = FAIR001_DIR / "scored_exp003a_all_families.jsonl"
    if not path.exists():
        pytest.skip("FAIR-001 scoring artifacts not present in this environment")
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len({r["family_id"] for r in records}) == 150
    assert len(records) == 298  # 150 human + 148 machine


def test_exp003b_scored_covers_all_150_families():
    path = FAIR001_DIR / "scored_exp003b_essay_all_families.jsonl"
    if not path.exists():
        pytest.skip("FAIR-001 scoring artifacts not present in this environment")
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    assert len({r["family_id"] for r in records}) == 150
    assert len(records) == 277  # 150 human + 127 ai_assisted


def test_fair001_results_reproduction_thresholds_match_frozen_values():
    path = FAIR001_DIR / "results.json"
    if not path.exists():
        pytest.skip("FAIR-001 results not present in this environment")
    results = json.loads(path.read_text())
    assert results["reproducibility"]["exp003a_frozen_threshold"] == 0.47
    assert results["reproducibility"]["exp003b_essay_frozen_threshold"] == 0.34
    assert results["no_demographic_leakage_verified"] is True


def test_fair001_ell_status_distribution_matches_design_phase_feasibility_finding():
    path = FAIR001_DIR / "results.json"
    if not path.exists():
        pytest.skip("FAIR-001 results not present in this environment")
    results = json.loads(path.read_text())
    dist = results["ell_status_distribution_all_families"]
    assert dist == {"Yes": 10, "No": 132, "unlabeled": 8}
