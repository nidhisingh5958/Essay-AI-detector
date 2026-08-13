"""
EXP-DATA-001-R2 -- Sentence-level validation: context redesign +
automated semantic screen, on a small fresh sample (10 seeds).

Per review, this is explicitly NOT a scale-up of sentence-level
generation -- it is a test of whether two specific changes reduce the
semantic-drift problem found in EXP-DATA-001-R1-confirmation:

1. More context: the model sees the FULL PARAGRAPH containing the target
   sentence (not just one sentence before/after), while being explicitly
   instructed to modify ONLY the target sentence
   (generate_sentence_transform_with_paragraph_context).
2. An automated semantic screen (DEC-012) flags likely drift for
   priority human review -- it does NOT set ground truth itself.

CONTROLLED EXPERIMENT: model, model revision, temperature, top_p,
max_new_tokens strategy, context format, source-selection procedure, and
QC procedure are IDENTICAL between light and moderate -- only the
instruction wording varies. This directly addresses the confound in
EXP-DATA-001-R1-confirmation (temperature differed 0.5 vs 0.7 alongside
wording), which made it impossible to attribute the light-vs-moderate
difference found there to either cause.

10 fresh seeds (excluded: 23 from prior experiments + 10 from
EXP-DATA-001-R2-paragraph = 33 IDs) x 3 categories (human,
sentence_light_controlled_v2, sentence_moderate_controlled_v2) = 30
records. Success is NOT defined as 100% passing -- see the report.
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
    generate_sentence_transform_with_paragraph_context,
    load_candidate_records,
    make_human_record,
)
from run_exp_data_001_r2_paragraph import EXCLUDED_SEED_IDS as PRIOR_EXCLUDED_SEED_IDS  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R2-sentence"
N_SEEDS = 10

# Prior experiments' seeds (23) plus EXP-DATA-001-R2-paragraph's 10 --
# kept as a strictly separate seed pool from paragraph-level validation.
EXCLUDED_SEED_IDS = PRIOR_EXCLUDED_SEED_IDS | {
    "0F38D6102C2C", "23C514D3D801", "7A75826F5403", "87F826CDE47A", "ABFE420BA213",
    "B2EC537A5265", "BCEF4D5FF6AB", "C1528CD20761", "CBB6B78B7E7D", "DB12BA4206B8",
}

# Held constant across light and moderate -- this is the point of this round.
GENERATION_TEMPERATURE = 0.6
GENERATION_TOP_P = 0.95

SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION = (
    "You are editing ONE sentence within a paragraph. Only lightly copy-edit the SPECIFIC "
    "TARGET SENTENCE below for grammar and word choice, keeping its meaning and length almost "
    "exactly the same -- this should read as a minor edit, not a rewrite. Do NOT change, "
    "paraphrase, or rewrite any other sentence in the paragraph. Return ONLY the rewritten "
    "target sentence, with no preamble, quotation marks, or commentary.\n\n"
    "Full paragraph for context:\n{paragraph}\n\nTarget sentence to edit: {target}"
)
SENTENCE_LIGHT_CONTROLLED_V2_META = (
    "You are editing ONE sentence within a paragraph. Only lightly copy-edit the SPECIFIC "
    "TARGET SENTENCE below for grammar and word choice, keeping its meaning and length almost "
    "exactly the same -- this should read as a minor edit, not a rewrite. Do NOT change, "
    "paraphrase, or rewrite any other sentence in the paragraph. Return ONLY the rewritten "
    "target sentence, with no preamble, quotation marks, or commentary."
)
SENTENCE_MODERATE_CONTROLLED_V2_INSTRUCTION = (
    "You are editing ONE sentence within a paragraph. Only moderately reword the SPECIFIC "
    "TARGET SENTENCE below for clarity and flow, while preserving its meaning and keeping "
    "roughly the same length. Do NOT change, paraphrase, or rewrite any other sentence in the "
    "paragraph. Return ONLY the reworded target sentence, with no preamble, quotation marks, "
    "or commentary.\n\nFull paragraph for context:\n{paragraph}\n\nTarget sentence to edit: {target}"
)
SENTENCE_MODERATE_CONTROLLED_V2_META = (
    "You are editing ONE sentence within a paragraph. Only moderately reword the SPECIFIC "
    "TARGET SENTENCE below for clarity and flow, while preserving its meaning and keeping "
    "roughly the same length. Do NOT change, paraphrase, or rewrite any other sentence in the "
    "paragraph. Return ONLY the reworded target sentence, with no preamble, quotation marks, "
    "or commentary."
)


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print("Filtering candidate seeds (excluding 33 prior IDs)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 4,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 4)
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

            if f"{sid}__sentence_moderate_controlled_v2" not in already_done:
                print("  generating sentence_moderate_controlled_v2 (paragraph context)...")
                _emit(
                    generate_sentence_transform_with_paragraph_context(
                        seed, split, "sentence_moderate_controlled_v2",
                        SENTENCE_MODERATE_CONTROLLED_V2_INSTRUCTION, SENTENCE_MODERATE_CONTROLLED_V2_META,
                        temperature=GENERATION_TEMPERATURE, top_p=GENERATION_TOP_P,
                        expected_length_ratio_range=(0.5, 1.8),
                    )
                )
            else:
                print("  sentence_moderate_controlled_v2 -- already done, skipping")

    print(f"\nWrote {len(all_records)} total records to {samples_path}")
    print("Next: run apply_automated_screen.py, then manual semantic review.")


if __name__ == "__main__":
    main()
