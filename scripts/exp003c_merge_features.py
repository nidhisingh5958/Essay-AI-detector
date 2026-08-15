"""
EXP-003C -- Stage 1: build the 3-class essay-level feature dataset by
merging already-cached vectors. NO new feature extraction.

Sources:
  experiments/EXP-003A/features.jsonl  -- human (150) + full_ai (148)
  experiments/EXP-003B/features_essay.jsonl -- human (150) + ai_assisted (127)

The 150 human rows are present in both files. Per EXP-003.md Section 9A,
they were verified byte-identical (both trace to the same deterministic
extract_features_for_essay calls) before this script was written --
re-verified programmatically below, not just asserted in prose.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

EXP003A_PATH = REPO_ROOT / "experiments" / "EXP-003A" / "features.jsonl"
EXP003B_ESSAY_PATH = REPO_ROOT / "experiments" / "EXP-003B" / "features_essay.jsonl"
OUTPUT_PATH = REPO_ROOT / "experiments" / "EXP-003C" / "features_essay.jsonl"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    a_records = load_jsonl(EXP003A_PATH)
    b_records = load_jsonl(EXP003B_ESSAY_PATH)

    a_by_id = {r["sample_id"]: r for r in a_records}
    b_by_id = {r["sample_id"]: r for r in b_records}

    a_human = {k: v for k, v in a_by_id.items() if v["label"] == "human"}
    b_human = {k: v for k, v in b_by_id.items() if v["label"] == "human"}

    assert len(a_human) == 150 and len(b_human) == 150, "expected 150 human rows in each source file"
    mismatches = [k for k in a_human if a_human[k] != b_human.get(k)]
    assert not mismatches, f"human feature vectors differ between EXP-003A and EXP-003B sources: {mismatches}"
    print(f"Verified {len(a_human)} human feature vectors are byte-identical between sources")

    full_ai = [r for r in a_records if r["label"] == "machine"]
    ai_assisted = [r for r in b_records if r["label"] == "ai_assisted"]
    assert len(full_ai) == 148, f"expected 148 full_ai rows, got {len(full_ai)}"
    assert len(ai_assisted) == 127, f"expected 127 ai_assisted rows, got {len(ai_assisted)}"

    merged = list(a_human.values()) + full_ai + ai_assisted
    assert len(merged) == 425, f"expected 425 total rows, got {len(merged)}"

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        for r in merged:
            f.write(json.dumps(r) + "\n")

    from collections import Counter

    print(f"Wrote {len(merged)} merged rows to {OUTPUT_PATH}")
    print("Label counts:", Counter(r["label"] for r in merged))
    print("Split x label:", Counter((r["split"], r["label"]) for r in merged))


if __name__ == "__main__":
    main()
