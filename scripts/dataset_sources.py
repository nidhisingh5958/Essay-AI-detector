"""
Configuration for human-writing dataset sources selected in DEC-009
(docs/decisions/DEC-009-human-dataset-source.md).

The Kaggle refs below were found via web research (see
docs/dataset-source-comparison.md) and have NOT been independently
downloaded or verified yet. `acquire_dataset.py` checks `expected_licenses`
against Kaggle's live metadata before downloading anything, precisely
because DEC-009 found the PERSUADE license framing inconsistent across
sources (CC BY-NC-SA 4.0 on GitHub vs. CC BY 4.0 on the Learning Agency
Lab's own site) -- this config intentionally accepts either recorded
framing so the check fails loudly only on a genuinely unexpected license,
not because we picked the "wrong" one of two sources that already
disagreed. Whatever value is actually returned must still be recorded in
DEC-009 to resolve the discrepancy, not silently accepted and forgotten.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetSource:
    name: str
    kaggle_ref: str  # "<owner>/<dataset-slug>"
    expected_licenses: tuple[str, ...]  # any one of these is acceptable
    decision_record: str
    notes: str


PERSUADE_2_0 = DatasetSource(
    name="persuade_2.0",
    kaggle_ref="nbroad/persaude-corpus-2",
    expected_licenses=("CC BY-NC-SA 4.0", "CC-BY-NC-SA-4.0", "CC BY 4.0", "CC-BY-4.0"),
    decision_record="docs/decisions/DEC-009-human-dataset-source.md",
    notes=(
        "This Kaggle ref is a community-uploaded mirror found via research, "
        "not confirmed to be an official Learning Agency Lab Kaggle listing. "
        "Re-verify it is the intended full PERSUADE 2.0 corpus (not a subset "
        "from one of the individual Feedback Prize competitions) before "
        "treating a successful download as sufficient -- inspect row/essay "
        "counts against the ~25,000 figure documented in DEC-009."
    ),
)

ELLIPSE_CORPUS = DatasetSource(
    name="ellipse_corpus",
    kaggle_ref="mpware/ellipse-corpus",
    expected_licenses=("CC BY-NC-SA 4.0", "CC-BY-NC-SA-4.0"),
    decision_record="docs/decisions/DEC-009-human-dataset-source.md",
    notes=(
        "Reserved for the Phase 12 fairness analysis specifically (genuine "
        "ELL proficiency labels), not for general reference-distribution "
        "construction -- see DEC-009."
    ),
)

ALL_SOURCES: tuple[DatasetSource, ...] = (PERSUADE_2_0, ELLIPSE_CORPUS)
