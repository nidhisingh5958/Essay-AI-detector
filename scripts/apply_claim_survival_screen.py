"""
Apply the claim-survival screen (claim_survival_screen.py) to a generated
samples file, post-hoc -- same pattern as apply_automated_screen.py.
Scoped to paragraph_* categories only (this screen targets the
paragraph-level claim-omission failure mode; see DEC-011/DEC-013 and
claim_survival_screen.py's module docstring).

This does NOT set semantic_preservation -- it only fills in
claim_survival_screen_label / claim_survival_coverage / claim_survival_
fact_check as advisory fields. Manual review remains the authority.

Usage:
    python apply_claim_survival_screen.py data/generated/<dir>/samples.jsonl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from apply_automated_screen import extract_span_pair  # noqa: E402
from claim_survival_screen import run_claim_survival_screen  # noqa: E402


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python apply_claim_survival_screen.py <samples.jsonl path>")
        sys.exit(1)

    samples_path = Path(sys.argv[1])
    records = [json.loads(line) for line in samples_path.read_text().splitlines() if line.strip()]
    by_family = {}
    for r in records:
        by_family.setdefault(r["family_id"], {})[r["transformation_type"]] = r

    screened = 0
    for fam, cats in by_family.items():
        human = cats.get("original")
        if human is None:
            continue
        for cat, record in cats.items():
            if cat == "original" or not cat.startswith("paragraph_"):
                continue
            pair = extract_span_pair(human, record)
            if pair is None:
                continue
            original, rewritten = pair
            result = run_claim_survival_screen(original, rewritten)
            record["claim_survival_screen_label"] = result.screen_label
            record["claim_survival_coverage"] = result.coverage
            record["claim_survival_fact_check"] = result.fact_check
            screened += 1
            n_dropped = len(result.coverage["dropped_sentences"])
            print(f"  {record['sample_id']}: label={result.screen_label} dropped_sentences={n_dropped}")

    with open(samples_path, "w") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    print(f"\nApplied claim-survival screen to {screened} paragraph-category records in {samples_path}")


if __name__ == "__main__":
    main()
