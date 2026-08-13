"""
Merge a manual semantic-preservation review into a samples.jsonl file.

Per explicit project instruction: semantic_preservation is assigned by
human review, never by an LLM call within this pipeline (that would be
exactly the LLM-as-ground-truth-judge pattern this project avoids
everywhere else -- DEC-004). This script only performs the mechanical
merge; the review dict it's given must come from an actual human reading
the original-vs-transformed text pairs.

Usage (as a library, not a CLI -- the review dict is written by hand,
not generated):

    from apply_semantic_review import apply_review
    apply_review(
        "data/generated/EXP-DATA-001-R1-confirmation/samples.jsonl",
        {
            "3AF8147D6DB0__sentence_light_controlled": ("preserved", "Meaning unchanged, only phrasing."),
            ...
        },
    )
"""

import json
from pathlib import Path

from generation_utils import validate_semantic_preservation


def apply_review(samples_path: str, review: dict[str, tuple[str, str]]) -> dict:
    """`review` maps sample_id -> (semantic_preservation, notes).
    Returns a summary of how many records were updated / skipped."""
    path = Path(samples_path)
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    updated = 0
    unknown_ids = set(review.keys())
    for record in records:
        sid = record["sample_id"]
        if sid in review:
            value, notes = review[sid]
            if not validate_semantic_preservation(value):
                raise ValueError(f"Invalid semantic_preservation value {value!r} for {sid}")
            record["semantic_preservation"] = value
            record["semantic_preservation_notes"] = notes
            updated += 1
            unknown_ids.discard(sid)

    if unknown_ids:
        raise ValueError(f"Review referenced sample_ids not found in {samples_path}: {sorted(unknown_ids)}")

    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return {"updated": updated, "total_records": len(records)}
