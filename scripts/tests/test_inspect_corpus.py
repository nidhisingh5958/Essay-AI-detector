"""
Tests for inspect_corpus.py against small synthetic fixtures -- never the
real downloaded corpus files (per the requirement to keep unit tests
independent of live/large data).
"""

import pandas as pd

from inspect_corpus import (
    duplicate_id_report,
    near_duplicate_groups,
    paragraph_marker_coverage,
    recompute_word_counts,
    word_count_discrepancy,
)


def test_recompute_word_counts_matches_simple_split():
    series = pd.Series(["one two three", "a b", ""])
    result = recompute_word_counts(series)
    assert list(result) == [3, 2, 0]


def test_word_count_discrepancy_flags_a_major_outlier():
    provided = pd.Series([10, 20, 5000])
    recomputed = pd.Series([10, 21, 50])
    report = word_count_discrepancy(provided, recomputed)
    assert report["n"] == 3
    assert report["max_abs_diff"] == 4950
    assert report["major_diff_pct"] > 0


def test_word_count_discrepancy_all_close():
    provided = pd.Series([100, 200])
    recomputed = pd.Series([101, 199])
    report = word_count_discrepancy(provided, recomputed)
    assert report["close_match_pct"] == 100.0
    assert report["major_diff_pct"] == 0.0


def test_paragraph_marker_coverage_detects_both_line_ending_styles():
    series = pd.Series(
        [
            "Para one.\n\nPara two.",
            "Para one.\r\n\r\nPara two.",
            "Single block, no paragraph break at all.",
        ]
    )
    coverage = paragraph_marker_coverage(series)
    assert coverage == 2 / 3


def test_paragraph_marker_coverage_empty_series_is_zero():
    assert paragraph_marker_coverage(pd.Series([], dtype=str)) == 0.0


def test_near_duplicate_groups_detects_identical_normalized_text():
    series = pd.Series(
        [
            "This is an essay about cats.",
            "this is an essay about cats.",  # same modulo case
            "A completely different essay about dogs and rivers and mountains.",
        ]
    )
    n_groups, n_rows = near_duplicate_groups(series)
    assert n_groups == 1
    assert n_rows == 2


def test_near_duplicate_groups_none_when_all_distinct():
    series = pd.Series(["Essay one is about the ocean.", "Essay two is about the mountains and hiking trails."])
    n_groups, n_rows = near_duplicate_groups(series)
    assert n_groups == 0
    assert n_rows == 0


def test_duplicate_id_report_flags_repeated_ids():
    ids = pd.Series(["a", "b", "a", "c"])
    report = duplicate_id_report(ids)
    assert report["n_unique"] == 3
    assert report["n_total"] == 4
    assert report["n_duplicate_id_values"] == 1
    assert report["duplicate_ids"] == ["a"]


def test_duplicate_id_report_no_duplicates():
    ids = pd.Series(["a", "b", "c"])
    report = duplicate_id_report(ids)
    assert report["n_duplicate_id_values"] == 0
    assert report["duplicate_ids"] == []
