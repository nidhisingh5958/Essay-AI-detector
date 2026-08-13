"""
EXP-DATA-001-R1 Confirmation -- larger-scale check of the controlled-span
methodology on previously unseen PERSUADE seed essays.

NOT detector evaluation. NOT full-scale dataset generation. A targeted
confirmation that the controlled-span mechanism (validated at n=3 per
category in EXP-DATA-001-R1) holds up at roughly EXP-DATA-001's original
scale (~10 seeds), across a wider set of categories (sentence AND
paragraph, light AND moderate).

10 NEW seed essays (excluded: all 10 from EXP-DATA-001, all 3 from
EXP-DATA-001-R1 -- 13 IDs total), x 5 categories:
  1. Human original
  2. sentence_light_controlled
  3. sentence_moderate_controlled
  4. paragraph_light_controlled
  5. paragraph_moderate_controlled
= 50 records.

Regime C (whole-essay polish) is explicitly NOT included -- its
methodology is unchanged and this experiment isn't meant to re-verify it.

Output: data/generated/EXP-DATA-001-R1-confirmation/samples.jsonl
(gitignored). Semantic-preservation review is a separate, later pass
(scripts/apply_semantic_review.py) -- this script only generates and
QCs; it never sets semantic_preservation to anything but
"not_yet_reviewed".
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
    generate_sentence_transform,
    load_candidate_records,
    make_human_record,
)
from run_exp_data_001_r1 import (  # noqa: E402
    SENTENCE_LIGHT_CONTROLLED_INSTRUCTION,
    SENTENCE_LIGHT_CONTROLLED_META,
    SENTENCE_MODERATE_CONTROLLED_INSTRUCTION,
    SENTENCE_MODERATE_CONTROLLED_META,
)

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R1-confirmation"
N_SEEDS = 10

# Seeds already used in EXP-DATA-001 (10) and EXP-DATA-001-R1 (3) --
# excluded so this confirmation genuinely tests previously-unseen essays,
# per explicit instruction.
EXCLUDED_SEED_IDS = {
    # EXP-DATA-001
    "18D47A791678", "72173F3A0279", "83D8EED426D9", "841F9E15D42E", "87186C957B20",
    "94330AB7CD65", "9A7C858EF23B", "C5566100FDF2", "DA723916BCC0", "EE3DDDA7F1B7",
    # EXP-DATA-001-R1
    "0C7EC7D3A247", "8D13461BD81C", "9EE956923B33",
}

PARAGRAPH_LIGHT_CONTROLLED_INSTRUCTION = (
    "Lightly copy-edit ONLY the following paragraph for grammar and word choice. "
    "Keep its meaning, claims, and length almost exactly the same -- this should read as a "
    "minor edit, not a rewrite. Return only the edited paragraph, with no preamble or commentary.\n\n"
    "Paragraph to edit:\n{target}"
)
PARAGRAPH_LIGHT_CONTROLLED_META = (
    "Lightly copy-edit ONLY the following paragraph for grammar and word choice. "
    "Keep its meaning, claims, and length almost exactly the same -- this should read as a "
    "minor edit, not a rewrite. Return only the edited paragraph, with no preamble or commentary."
)
PARAGRAPH_MODERATE_CONTROLLED_INSTRUCTION = (
    "Moderately reword ONLY the following paragraph for clarity and flow, while preserving its "
    "meaning, claims, and roughly the same length. Return only the reworded paragraph, with no "
    "preamble or commentary.\n\nParagraph to edit:\n{target}"
)
PARAGRAPH_MODERATE_CONTROLLED_META = (
    "Moderately reword ONLY the following paragraph for clarity and flow, while preserving its "
    "meaning, claims, and roughly the same length. Return only the reworded paragraph, with no "
    "preamble or commentary."
)


def main() -> None:
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]

    print("Filtering candidate seeds (excluding EXP-DATA-001 and R1 seeds)...")
    records = load_candidate_records(df)
    records = [r for r in records if r["id"] not in EXCLUDED_SEED_IDS]
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 2,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 2)
    print(f"Family split assignment (before generation): {splits}")

    # Write incrementally (append + flush after every record) and support
    # RESUMING from a partially-completed run -- this experiment's
    # background process has been killed mid-run by session interruptions
    # twice already (not a code bug; the environment's execution window
    # is shorter than a 50-sample generation run takes). Re-running this
    # script now skips any sample_id already present in samples.jsonl
    # instead of regenerating it, so repeated invocations converge on the
    # full 50-record set rather than losing progress or duplicating work.
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
        print(f"Resuming: {len(already_done)} records already present in {samples_path}")

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

            if f"{sid}__sentence_light_controlled" not in already_done:
                print("  generating sentence_light_controlled...")
                _emit(
                    generate_sentence_transform(
                        seed, split, "sentence_light_controlled",
                        SENTENCE_LIGHT_CONTROLLED_INSTRUCTION, SENTENCE_LIGHT_CONTROLLED_META,
                        temperature=0.5, expected_length_ratio_range=(0.7, 1.3),
                    )
                )
            else:
                print("  sentence_light_controlled -- already done, skipping")

            if f"{sid}__sentence_moderate_controlled" not in already_done:
                print("  generating sentence_moderate_controlled...")
                _emit(
                    generate_sentence_transform(
                        seed, split, "sentence_moderate_controlled",
                        SENTENCE_MODERATE_CONTROLLED_INSTRUCTION, SENTENCE_MODERATE_CONTROLLED_META,
                        temperature=0.7, expected_length_ratio_range=(0.5, 1.8),
                    )
                )
            else:
                print("  sentence_moderate_controlled -- already done, skipping")

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

    # Cross-family duplicate check (family-aware -- Section 1 fix) over
    # every non-empty text in this run. Done as a post-pass and rewrites
    # the file once at the end (cheap; only 50 records) so the
    # incremental-write resilience above doesn't complicate this step.
    print("\nRunning cross-family duplicate check...")
    items = [(r["sample_id"], r["family_id"], r["text"]) for r in all_records if r["text"]]
    dup_result = gu.near_duplicate_pairs_scoped(items)
    flagged_ids = {sid for pair in dup_result["cross_family"] for sid in pair[:2]}
    for r in all_records:
        if r["sample_id"] in flagged_ids:
            r["cross_family_duplicate_flag"] = True

    with open(samples_path, "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")
    with open(OUTPUT_DIR / "duplicate_analysis.json", "w") as f:
        json.dump(dup_result, f, indent=2)

    print(f"\nWrote {len(all_records)} records to {OUTPUT_DIR / 'samples.jsonl'}")
    print(f"Cross-family duplicate pairs found: {len(dup_result['cross_family'])}")
    print(f"Same-family similar pairs (expected, informational): {len(dup_result['same_family'])}")


if __name__ == "__main__":
    main()
