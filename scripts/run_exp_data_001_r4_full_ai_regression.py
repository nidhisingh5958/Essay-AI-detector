"""
EXP-DATA-001-R4 -- full_ai pre-scale regression check (review item 1,
2026-08-14).

Required prerequisite before the 150-family primary dataset
construction: confirm the full_ai mechanism (unchanged since
EXP-DATA-001, but never re-exercised live with the fixed
check_instruction_leakage) still behaves correctly on fresh seeds.
Explicitly NOT a methodology-discovery experiment -- no new mechanism,
no new QC signal, no threshold changes. If a real regression is found,
STOP and report rather than silently patching the mechanism.

10 fresh seeds (excluding all 80 seed IDs used across every prior
generation experiment: EXP-DATA-001 10, R1 3, R1-confirmation 10,
R2-paragraph 10, R2-sentence 10, R3-sentence-light 25,
R3-paragraph-claim-survival 12) x 1 category (full_ai) = 10 records,
plus the 10 human originals for reference/context = 20 records.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

import generation_utils as gu  # noqa: E402
from run_exp_data_001 import (  # noqa: E402
    PERSUADE_FILE,
    RNG_SEED,
    SEED_MAX_WORDS,
    SEED_MIN_WORDS,
    generate_full_ai,
    load_candidate_records,
    make_human_record,
)
from run_exp_data_001_r3_paragraph_claim_survival import (  # noqa: E402
    EXCLUDED_SEED_IDS as PRIOR_EXCLUDED_SEED_IDS,
)

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R4-full-ai-regression"
N_SEEDS = 10

# 68 seeds excluded by R3-paragraph-claim-survival's own script, plus its
# own 12 freshly-selected seeds (read directly from that script's output
# file, not recomputed) = 80 total.
_R3_PARAGRAPH_SAMPLES = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R3-paragraph-claim-survival" / "samples.jsonl"
_r3_paragraph_family_ids = set()
with open(_R3_PARAGRAPH_SAMPLES) as f:
    for line in f:
        if line.strip():
            _r3_paragraph_family_ids.add(json.loads(line)["family_id"])
assert len(_r3_paragraph_family_ids) == 12, f"expected 12 R3-paragraph families, got {len(_r3_paragraph_family_ids)}"

EXCLUDED_SEED_IDS = PRIOR_EXCLUDED_SEED_IDS | _r3_paragraph_family_ids
assert len(EXCLUDED_SEED_IDS) == 80, f"expected 80 excluded seeds, got {len(EXCLUDED_SEED_IDS)}"


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print(f"Filtering candidate seeds (excluding {len(EXCLUDED_SEED_IDS)} prior IDs)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 7,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 7)
    print(f"Family split assignment (before generation): {splits}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples_path = OUTPUT_DIR / "samples.jsonl"

    all_records = []
    already_done = set()
    if samples_path.exists():
        with open(samples_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    all_records.append(rec)
                    already_done.add(rec["sample_id"])
        print(f"Resuming: {len(already_done)} records already present")

    with open(samples_path, "a") as f:

        def _emit(record):
            all_records.append(record)
            f.write(json.dumps(record) + "\n")
            f.flush()

        for i, sid in enumerate(seed_ids):
            seed = seeds_by_id[sid]
            split = splits[sid]
            print(f"\n[{i+1}/{len(seed_ids)}] Seed {sid} (split={split}, words={seed['word_count']})")

            if f"{sid}__human" not in already_done:
                _emit(make_human_record(seed, split))
            else:
                print("  human -- already done, skipping")

            if f"{sid}__full_ai" not in already_done:
                print("  generating full_ai...")
                _emit(generate_full_ai(seed, split))
            else:
                print("  full_ai -- already done, skipping")

    print(f"\nWrote {len(all_records)} total records to {samples_path}")
    print("Next: run near-duplicate scoping + manual topic/prompt-adherence spot check.")


if __name__ == "__main__":
    main()
