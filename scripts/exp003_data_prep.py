"""
EXP-003 data-preparation utilities (DEC-014/DEC-016) -- pure data-layer
helpers only. Does NOT train, fit, or evaluate any model; that work is
explicitly not authorized in this design phase. This module exists so
the manifest-loading and sentence-localization-label logic EXP-003A/B/C
will need is itself already correct and tested before any modeling code
is written on top of it.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_manifest(manifest_path: str | Path) -> dict:
    """Load an inclusion manifest (e.g.
    data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json)."""
    return json.loads(Path(manifest_path).read_text())


def load_included_records(manifest_path: str | Path, samples_path: str | Path) -> list[dict]:
    """Return only the sample records the manifest actually includes --
    never assume every record in samples.jsonl is valid (per explicit
    instruction, this is the one sanctioned way to build a working
    dataframe from the raw sample store)."""
    manifest = load_manifest(manifest_path)
    included_ids = {r["sample_id"] for r in manifest["included"]}
    records = [json.loads(line) for line in Path(samples_path).read_text().splitlines() if line.strip()]
    return [r for r in records if r["sample_id"] in included_ids]


def verify_manifest_integrity(manifest_path: str | Path, samples_path: str | Path) -> dict:
    """Cross-check the manifest against the raw samples file. Returns a
    dict of problems found (empty values = no problem). Meant to be run
    before any experiment trusts the manifest, and exercised by tests
    against the frozen PRIMARY-DATASET-v1 manifest specifically."""
    manifest = load_manifest(manifest_path)
    all_records = {
        json.loads(line)["sample_id"]: json.loads(line)
        for line in Path(samples_path).read_text().splitlines()
        if line.strip()
    }
    included_ids = [r["sample_id"] for r in manifest["included"]]
    excluded_ids = [r["sample_id"] for r in manifest["excluded"]]

    problems = {
        "included_ids_missing_from_samples_file": [sid for sid in included_ids if sid not in all_records],
        "excluded_ids_missing_from_samples_file": [sid for sid in excluded_ids if sid not in all_records],
        "ids_in_both_included_and_excluded": sorted(set(included_ids) & set(excluded_ids)),
        "duplicate_included_ids": [sid for sid in included_ids if included_ids.count(sid) > 1],
    }
    return problems


def build_sentence_localization_labels(human_record: dict, ai_assisted_record: dict) -> list[tuple[str, str]]:
    """DEC-016: sentence-level ground truth for EXP-003B's localization
    task, built from the exact `modified_spans` provenance field -- never
    inferred by similarity (that mechanism was already rejected once,
    DEC-011's Post-Pilot Methodology Redesign).

    Returns a list of (sentence_text, label) for every sentence in
    ai_assisted_record's text, where label is "human" or "ai_assisted".
    Requires ai_assisted_record to have a resolvable, non-empty
    `modified_spans` -- callers should skip QC-rejected records (empty/
    None modified_spans) before calling this, same as
    apply_automated_screen.extract_span_pair does.
    """
    import sys

    sys.path.insert(0, str(REPO_ROOT / "backend"))
    from app.services.sentence_segmenter import segment_sentences  # noqa: E402

    modified_spans = ai_assisted_record.get("modified_spans")
    if not modified_spans:
        raise ValueError(
            f"{ai_assisted_record['sample_id']} has no resolvable modified_spans -- "
            "exclude QC-rejected records before calling build_sentence_localization_labels"
        )

    text = ai_assisted_record["text"]
    sentences = segment_sentences(text)

    modified_char_ranges = [(s["char_start"], s["char_end"]) for s in modified_spans]

    labels = []
    for sent in sentences:
        is_modified = any(
            sent.start_char < end and start < sent.end_char for start, end in modified_char_ranges
        )
        labels.append((sent.text, "ai_assisted" if is_modified else "human"))
    return labels
