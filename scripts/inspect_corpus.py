"""
Reusable inspection utilities used to produce reports/dataset-inspection.md.

Pure functions operating on pandas Series, so they're testable against small
fixtures (scripts/tests/test_inspect_corpus.py) without needing the real
downloaded corpus files. Re-running these against the actual acquired files
(data/raw/persuade_2.0/, data/raw/ellipse_corpus/) reproduces the numbers in
the inspection report -- see that report for the actual invocation and
results.
"""

import re
from collections import Counter

_PARAGRAPH_MARKER_RE = re.compile(r"(\r\n\r\n|\n\n)")
_WHITESPACE_RE = re.compile(r"\s+")


def recompute_word_counts(text_series):
    """Whitespace-split word count per row -- our own definition, used
    because corpus-provided word-count columns were found to disagree
    with this significantly for a meaningful fraction of rows (see
    reports/dataset-inspection.md)."""
    return text_series.apply(lambda t: len(str(t).split()))


def word_count_discrepancy(provided, recomputed):
    """Summarize how far a corpus-provided word-count column is from our
    own recomputed one. Returns counts in three buckets plus the worst
    single discrepancy, rather than just a mean (which one huge outlier
    can dominate)."""
    diff = (recomputed - provided).abs()
    n = len(diff)
    return {
        "n": n,
        "median_abs_diff": float(diff.median()) if n else 0.0,
        "close_match_pct": float((diff <= 2).mean() * 100) if n else 0.0,
        "minor_diff_pct": float(((diff > 2) & (diff <= 20)).mean() * 100) if n else 0.0,
        "major_diff_pct": float((diff > 20).mean() * 100) if n else 0.0,
        "max_abs_diff": float(diff.max()) if n else 0.0,
    }


def paragraph_marker_coverage(text_series):
    """Fraction of rows containing a blank-line paragraph marker (either
    \\n\\n or \\r\\n\\r\\n). This is a detection heuristic, not proof that
    every paragraph break in the original writing survived -- see
    Limitations in the inspection report."""
    if len(text_series) == 0:
        return 0.0
    has_marker = text_series.apply(lambda t: bool(_PARAGRAPH_MARKER_RE.search(str(t))))
    return float(has_marker.mean())


def near_duplicate_groups(text_series, prefix_len=80, suffix_len=80):
    """Cheap near-duplicate heuristic: normalize whitespace/case, then
    group by (first N chars, last N chars, length). Rows sharing a
    signature are flagged as a near-duplicate group. This is a heuristic,
    not exhaustive pairwise similarity -- it catches near-identical
    essays (e.g. copy-paste with minor edits at neither end) but can miss
    ones that differ only in the middle. Returns (num_groups,
    num_rows_involved)."""
    normalized = text_series.apply(lambda t: _WHITESPACE_RE.sub(" ", str(t).strip().lower()))
    signatures = normalized.apply(lambda t: (t[:prefix_len], t[-suffix_len:], len(t)))
    counts = Counter(signatures)
    groups = [c for c in counts.values() if c > 1]
    return len(groups), sum(groups)


def duplicate_id_report(id_series):
    """Report on non-unique identifiers -- distinct from duplicate
    *content*. A duplicate ID with different text under it (checked by
    the caller) indicates a data-quality issue in the source corpus, not
    a real duplicate essay."""
    counts = id_series.value_counts()
    dupes = counts[counts > 1]
    return {
        "n_unique": int(id_series.nunique()),
        "n_total": int(len(id_series)),
        "n_duplicate_id_values": int(len(dupes)),
        "duplicate_ids": list(dupes.index),
    }
