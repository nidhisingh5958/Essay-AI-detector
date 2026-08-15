"""
PRIMARY-DATASET-v1 -- 150-family primary dataset construction (approved
post-R4 review, 2026-08-14).

Controlled EXECUTION phase, not methodology research -- per explicit
instruction, do NOT modify any validated mechanism here. Every
generation call reuses the exact, already-validated configuration:

- full_ai: generate_full_ai (run_exp_data_001.py), unchanged since
  EXP-DATA-001, re-confirmed clean in EXP-DATA-001-R4.
- sentence_light_controlled_v2: generate_sentence_transform_with_paragraph_context
  with SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION/META, temperature=0.6,
  top_p=0.95 -- byte-for-byte the same constants imported from
  run_exp_data_001_r2_sentence.py, exactly as validated in
  EXP-DATA-001-R2/R3.

Do NOT generate sentence_moderate_controlled_v2 or any paragraph_*
category here -- excluded from the primary dataset per DEC-011's
Strategic Decision.

150 fresh seeds, excluding all 90 seed IDs used across every prior
generation experiment (EXP-DATA-001 through R4). Family split assigned
BEFORE generation (hard leakage invariant, DEC-011 Section 13) --
105 train / 22 validation / 23 test (see module-level SPLIT_COUNTS).

Resumable: checks existing samples.jsonl at startup, skips any
sample_id already present, appends and flushes after every record --
same pattern used (and needed) in every prior multi-hour generation
round in this project.
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
    generate_sentence_transform_with_paragraph_context,
    load_candidate_records,
    make_human_record,
)
from run_exp_data_001_r2_sentence import (  # noqa: E402
    SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION,
    SENTENCE_LIGHT_CONTROLLED_V2_META,
)
from run_exp_data_001_r4_full_ai_regression import EXCLUDED_SEED_IDS as PRIOR_EXCLUDED_SEED_IDS  # noqa: E402

DATASET_NAME = "PRIMARY-DATASET-v1"
OUTPUT_DIR = REPO_ROOT / "data" / "generated" / DATASET_NAME
N_FAMILIES = 150

# 80 excluded by R4's own script, plus R4's own 10 selected seeds (read
# directly from its output file, exact -- not recomputed) = 90 total.
_R4_SAMPLES = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R4-full-ai-regression" / "samples.jsonl"
_r4_family_ids = set()
with open(_R4_SAMPLES) as f:
    for line in f:
        if line.strip():
            _r4_family_ids.add(json.loads(line)["family_id"])
assert len(_r4_family_ids) == 10, f"expected 10 R4 families, got {len(_r4_family_ids)}"

EXCLUDED_SEED_IDS = PRIOR_EXCLUDED_SEED_IDS | _r4_family_ids
assert len(EXCLUDED_SEED_IDS) == 90, f"expected 90 excluded seeds, got {len(EXCLUDED_SEED_IDS)}"

# Held identical to EXP-DATA-001-R2-sentence / R3-sentence-light -- this
# is an execution round, not a methodology round; nothing here varies.
GENERATION_TEMPERATURE = 0.6
GENERATION_TOP_P = 0.95


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print(f"Filtering candidate seeds (excluding {len(EXCLUDED_SEED_IDS)} prior IDs)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_FAMILIES, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 8,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    assert len(seed_ids) == N_FAMILIES, f"expected {N_FAMILIES} seeds, got {len(seed_ids)}"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays.")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 8)
    from collections import Counter
    split_counts = Counter(splits.values())
    print(f"Family split assignment (before generation): {dict(split_counts)}")

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

            if f"{sid}__sentence_light_controlled_v2" not in already_done:
                print("  generating sentence_light_controlled_v2 (paragraph context)...")
                _emit(
                    generate_sentence_transform_with_paragraph_context(
                        seed, split, "sentence_light_controlled_v2",
                        SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION, SENTENCE_LIGHT_CONTROLLED_V2_META,
                        temperature=GENERATION_TEMPERATURE, top_p=GENERATION_TOP_P,
                        expected_length_ratio_range=(0.7, 1.3),
                    )
                )
            else:
                print("  sentence_light_controlled_v2 -- already done, skipping")

    print(f"\nWrote {len(all_records)} total records to {samples_path}")
    print("Next: apply_automated_screen.py, then mandatory manual semantic review, then build inclusion manifest.")


if __name__ == "__main__":
    main()
