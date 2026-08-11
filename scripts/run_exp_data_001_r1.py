"""
EXP-DATA-001-R1 -- Generation Methodology Revision Check.

NOT a new full pilot. A small, explicitly-scoped validation that the
post-EXP-DATA-001 redesign (DEC-011) behaves as intended:

  - 3 sentence rewrites          (sentence_rewrite_single, Regime A, unchanged)
  - 3 paragraph rewrites         (paragraph_rewrite_single, Regime B, unchanged)
  - 3 light controlled rewrites  (sentence_light_controlled, Regime A, NEW)
  - 3 moderate controlled rewrites (sentence_moderate_controlled, Regime A, NEW)
  - 3 whole-essay polish samples (light_polish, Regime C, reclassified)

= 15 generated samples from 3 seed essays (each seed gets one of every
category), plus the 3 human originals reused = 18 records total.

This script evaluates the DATA GENERATION PIPELINE and its QC checks. It
does not run or evaluate a detector, compute detection accuracy, or use
a detector to label anything.

Output: data/generated/EXP-DATA-001-R1/samples.jsonl,
data/generated/EXP-DATA-001-R1/diffs.json (Regime C diagnostic only).
Both gitignored under data/*.
"""

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import generation_utils as gu  # noqa: E402
from run_exp_data_001 import (  # noqa: E402
    PERSUADE_FILE,
    RNG_SEED,
    SEED_MAX_WORDS,
    SEED_MIN_WORDS,
    generate_paragraph_rewrite,
    generate_polish,
    generate_sentence_rewrite,
    generate_sentence_transform,
    load_candidate_records,
    make_human_record,
)

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R1"
N_SEEDS = 3

# New: instruction templates for controlled-span light/moderate sentence
# transformations -- same splice mechanism as sentence_rewrite_single
# (Regime A), lighter/more constrained instruction wording. See DEC-011
# "Post-Pilot Methodology Redesign."
SENTENCE_LIGHT_CONTROLLED_INSTRUCTION = (
    "Lightly copy-edit ONLY the following sentence for grammar and word choice. "
    "Keep its meaning and length almost exactly the same -- this should read as a "
    "minor edit, not a rewrite. Return only the edited sentence, with no preamble, "
    "quotation marks, or commentary.\n\nContext before: {before}\nSentence to edit: {target}\n"
    "Context after: {after}"
)
SENTENCE_LIGHT_CONTROLLED_META = (
    "Lightly copy-edit ONLY the following sentence for grammar and word choice. "
    "Keep its meaning and length almost exactly the same -- this should read as a "
    "minor edit, not a rewrite. Return only the edited sentence, with no preamble, "
    "quotation marks, or commentary."
)
SENTENCE_MODERATE_CONTROLLED_INSTRUCTION = (
    "Moderately reword ONLY the following sentence for clarity and flow, while "
    "preserving its meaning and keeping roughly the same length. Return only the "
    "reworded sentence, with no preamble, quotation marks, or commentary.\n\n"
    "Context before: {before}\nSentence to edit: {target}\nContext after: {after}"
)
SENTENCE_MODERATE_CONTROLLED_META = (
    "Moderately reword ONLY the following sentence for clarity and flow, while "
    "preserving its meaning and keeping roughly the same length. Return only the "
    "reworded sentence, with no preamble, quotation marks, or commentary."
)


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print("Filtering candidate seeds...")
    records = load_candidate_records(df)
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 1,  # different seed than EXP-DATA-001, distinct seed essays
    )
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 1)
    print(f"Family split assignment (before generation): {splits}")

    all_records = []
    regime_c_diffs = []

    for i, sid in enumerate(seed_ids):
        seed = seeds_by_id[sid]
        split = splits[sid]
        print(f"\n[{i+1}/{len(seed_ids)}] Seed {sid} (split={split}, words={seed['word_count']})")

        all_records.append(make_human_record(seed, split))

        print("  generating sentence_rewrite_single (Regime A, unchanged)...")
        all_records.append(generate_sentence_rewrite(seed, split))

        print("  generating paragraph_rewrite_single (Regime B, unchanged)...")
        all_records.append(generate_paragraph_rewrite(seed, split))

        print("  generating sentence_light_controlled (Regime A, NEW)...")
        all_records.append(
            generate_sentence_transform(
                seed, split, "sentence_light_controlled",
                SENTENCE_LIGHT_CONTROLLED_INSTRUCTION, SENTENCE_LIGHT_CONTROLLED_META,
                temperature=0.5, expected_length_ratio_range=(0.7, 1.3),
            )
        )

        print("  generating sentence_moderate_controlled (Regime A, NEW)...")
        all_records.append(
            generate_sentence_transform(
                seed, split, "sentence_moderate_controlled",
                SENTENCE_MODERATE_CONTROLLED_INSTRUCTION, SENTENCE_MODERATE_CONTROLLED_META,
                temperature=0.7, expected_length_ratio_range=(0.5, 1.8),
            )
        )

        print("  generating light_polish (Regime C, reclassified essay-level-only)...")
        result = generate_polish(seed, split, "light_polish")
        all_records.append(result["record"])
        regime_c_diffs.append((sid, result["diff"]))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "samples.jsonl", "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")

    diff_export = [
        {"seed_id": sid, "structure_drift": d["structure_drift"], "pairs": [(a, b, r) for a, b, r in d["pairs"]]}
        for sid, d in regime_c_diffs
    ]
    with open(OUTPUT_DIR / "diffs.json", "w") as f:
        json.dump(diff_export, f, indent=2)

    print(f"\nWrote {len(all_records)} records to {OUTPUT_DIR / 'samples.jsonl'}")
    print(f"Wrote Regime C diagnostic diff data to {OUTPUT_DIR / 'diffs.json'}")


if __name__ == "__main__":
    main()
