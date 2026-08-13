"""
EXP-DATA-001-R2 -- Paragraph-level validation (fresh seeds).

Per review: paragraph-level controlled transformation showed
substantially better evidence than sentence-level in the confirmation
round and may proceed to a SEPARATE validation experiment -- not
declared production-ready, just re-checked on seeds it hasn't seen yet.
Uses the EXISTING, unchanged paragraph-transform mechanism
(generate_paragraph_transform) -- this script does not redesign
anything, it only re-validates on fresh data.

10 fresh seeds (excluded: all seeds from EXP-DATA-001, EXP-DATA-001-R1,
and EXP-DATA-001-R1-confirmation -- 23 IDs) x 3 categories (human,
paragraph_light_controlled, paragraph_moderate_controlled) = 30 records.

Kept strictly separate from the sentence-level validation
(run_exp_data_001_r2_sentence.py) and its own seed pool, per explicit
instruction to keep sentence-level and paragraph-level results separate.
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
    generate_paragraph_transform,
    load_candidate_records,
    make_human_record,
)
from run_exp_data_001_r1_confirmation import (  # noqa: E402
    PARAGRAPH_LIGHT_CONTROLLED_INSTRUCTION,
    PARAGRAPH_LIGHT_CONTROLLED_META,
    PARAGRAPH_MODERATE_CONTROLLED_INSTRUCTION,
    PARAGRAPH_MODERATE_CONTROLLED_META,
)

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R2-paragraph"
N_SEEDS = 10

# All seeds used in every prior generation experiment -- excluded so this
# round is genuinely on unseen essays.
EXCLUDED_SEED_IDS = {
    # EXP-DATA-001
    "18D47A791678", "72173F3A0279", "83D8EED426D9", "841F9E15D42E", "87186C957B20",
    "94330AB7CD65", "9A7C858EF23B", "C5566100FDF2", "DA723916BCC0", "EE3DDDA7F1B7",
    # EXP-DATA-001-R1
    "0C7EC7D3A247", "8D13461BD81C", "9EE956923B33",
    # EXP-DATA-001-R1-confirmation
    "3AF8147D6DB0", "453380C5CA9C", "4C3FC32093AB", "7E3CDEFECEC6", "93B23DB0F67B",
    "9B9380760425", "B056AD01475D", "B8164EA79177", "BCB916A9A9F3", "E4596B010B9B",
}


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print("Filtering candidate seeds (excluding all 23 prior seeds)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 3,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 3)
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

            if f"{sid}__paragraph_light_controlled" not in already_done:
                print("  generating paragraph_light_controlled...")
                _emit(
                    generate_paragraph_transform(
                        seed, split, "paragraph_light_controlled",
                        PARAGRAPH_LIGHT_CONTROLLED_INSTRUCTION, PARAGRAPH_LIGHT_CONTROLLED_META,
                        temperature=0.5, expected_length_ratio_range=(0.7, 1.4),
                    )
                )
            else:
                print("  paragraph_light_controlled -- already done, skipping")

            if f"{sid}__paragraph_moderate_controlled" not in already_done:
                print("  generating paragraph_moderate_controlled...")
                _emit(
                    generate_paragraph_transform(
                        seed, split, "paragraph_moderate_controlled",
                        PARAGRAPH_MODERATE_CONTROLLED_INSTRUCTION, PARAGRAPH_MODERATE_CONTROLLED_META,
                        temperature=0.7, expected_length_ratio_range=(0.5, 2.0),
                    )
                )
            else:
                print("  paragraph_moderate_controlled -- already done, skipping")

    print(f"\nWrote {len(all_records)} total records to {samples_path}")


if __name__ == "__main__":
    main()
