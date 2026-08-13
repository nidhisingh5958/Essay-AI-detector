"""
EXP-DATA-001-R3 -- Paragraph claim-survival validation (review item 5,
2026-08-13).

Per review: EXP-DATA-001-R2 found a new paragraph-level failure mode --
"claim omission despite acceptable structural/length measurements" (seed
DB12BA4206B8, both light and moderate). This experiment adds a
claim-survival SCREENING layer (claim_survival_screen.py -- sentence-
coverage via embedding best-match + aggregate fact-check, NOT ground
truth, see that module's docstring and DEC-012/DEC-013) and validates it
against fresh paragraph transformations, with light and moderate kept
SEPARATELY reported throughout (never combined into one pass/fail
number).

EXPERIMENTAL INDEPENDENCE (review item 6): this experiment does NOT
redesign the paragraph generation mechanism -- it reuses
generate_paragraph_transform completely unchanged (same instructions,
same temperatures: light=0.5, moderate=0.7, same as EXP-DATA-001-R2-
paragraph) so that any newly-observed omission is attributable to the
existing mechanism on fresh seeds, not to a mechanism change. The only
new thing this experiment adds is the claim-survival SCREEN applied
post-hoc (apply_claim_survival_screen.py) plus mandatory manual review.

12 fresh seeds x 3 categories (human, paragraph_light_controlled,
paragraph_moderate_controlled) = 36 records. Excludes all 68 seed IDs
used across every prior generation experiment, INCLUDING
EXP-DATA-001-R3-sentence-light's 25 fresh seeds (kept as a strictly
separate pool, run_exp_data_001_r3_sentence_light.py's own module
docstring / assertion documents its 43; this script's own seeds are
disjoint from those 25 as well, verified by assertion below).
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
from run_exp_data_001_r3_sentence_light import EXCLUDED_SEED_IDS as PRIOR_EXCLUDED_SEED_IDS  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R3-paragraph-claim-survival"
N_SEEDS = 12

# The 43 seeds already excluded by EXP-DATA-001-R3-sentence-light itself
# (23 base + R2-paragraph 10 + R2-sentence 10), imported directly rather
# than recomputed, plus that script's own 25 freshly-selected seeds
# (hardcoded here since seed selection happens at call time, not import
# time -- see that script's printed seed list) -- kept as a strictly
# separate pool. 43 + 25 = 68.
_R3_SENTENCE_LIGHT_SEED_IDS = {
    "19E44CA7DF5A", "27347E260F1C", "30FC788A063D", "3D8260196DC0", "595801A6D808",
    "5ECBD433868E", "802E234C4BB9", "81720D00C09E", "91176971F6BA", "9E4F43374DD5",
    "A2FA6823EBBA", "A95DC9851C4A", "B71DB7CEB4A8", "BF845A6C39D4", "C74CFA4E78D4",
    "C86A3BBC881C", "DCFBD4CF4251", "E51A57766989", "E92E7BAEF0BE", "E940448E4323",
    "EF1F075952C8", "F18ABB1A8920", "F8F1F70A38AE", "FABE0E966789", "FB59DB8F78ED",
}
EXCLUDED_SEED_IDS = PRIOR_EXCLUDED_SEED_IDS | _R3_SENTENCE_LIGHT_SEED_IDS
assert len(EXCLUDED_SEED_IDS) == 68, f"expected 68 excluded seeds, got {len(EXCLUDED_SEED_IDS)}"


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print(f"Filtering candidate seeds (excluding {len(EXCLUDED_SEED_IDS)} prior IDs)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 6,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 6)
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
    print("Next: run apply_automated_screen.py + apply_claim_survival_screen.py, then manual semantic review.")


if __name__ == "__main__":
    main()
