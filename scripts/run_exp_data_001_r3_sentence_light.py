"""
EXP-DATA-001-R3 -- Sentence-light larger confirmation (review item 3,
2026-08-13).

Per review: `sentence_light_controlled_v2` is now the strongest mixed-
text candidate (EXP-DATA-001-R2: 9/10 preserved, 0/10 changed on 10
fresh seeds). This experiment asks ONLY: "Does the promising
sentence-light mechanism remain reliable on a larger fresh sample?" --
it is explicitly NOT a redesign and does NOT touch `sentence_moderate_
controlled_v2` (that category is excluded entirely from this run; its
redesign is a separate, not-yet-implemented design task -- see
sentence_moderate_redesign_candidates.py and DEC-011).

EXPERIMENTAL INDEPENDENCE (review item 6): only the sample size and seed
pool change relative to EXP-DATA-001-R2-sentence. Everything else is
held IDENTICAL:
- same model (Qwen2.5-1.5B-Instruct), same revision
- same temperature (0.6) / top_p (0.95)
- same context format (generate_sentence_transform_with_paragraph_context
  -- full paragraph context, edit only the target sentence)
- same max_new_tokens strategy (budget_max_new_tokens, unchanged)
- same span-selection methodology (pick_rewrite_sentence_index, unchanged)
- same QC (run_qc_common, unchanged)
- same semantic-screen procedure (DEC-012, semantic_screen.py, unchanged)
- same instruction/meta-instruction wording (SENTENCE_LIGHT_CONTROLLED_V2)

No new success threshold is defined here before observing results, per
explicit instruction.

25 fresh seeds x 2 categories (human, sentence_light_controlled_v2) = 50
records. Excludes all 43 seed IDs used in every prior generation
experiment (EXP-DATA-001: 10, EXP-DATA-001-R1: 3,
EXP-DATA-001-R1-confirmation: 10, EXP-DATA-001-R2-paragraph: 10,
EXP-DATA-001-R2-sentence: 10) -- genuinely unseen essays.
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
from run_exp_data_001_r2_sentence import (  # noqa: E402
    EXCLUDED_SEED_IDS as PRIOR_EXCLUDED_SEED_IDS,
)
from run_exp_data_001_r2_sentence import (  # noqa: E402
    SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION,
    SENTENCE_LIGHT_CONTROLLED_V2_META,
)

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R3-sentence-light"
N_SEEDS = 25

# 33 seeds excluded by EXP-DATA-001-R2-sentence's own script, plus the 10
# fresh seeds THAT script itself selected and used (read directly from
# its output file, not recomputed, so this is exact rather than relying
# on reproducing an RNG draw) = 43 total.
_R2_SENTENCE_SAMPLES = REPO_ROOT / "data" / "generated" / "EXP-DATA-001-R2-sentence" / "samples.jsonl"
_r2_sentence_family_ids = set()
with open(_R2_SENTENCE_SAMPLES) as f:
    for line in f:
        if line.strip():
            _r2_sentence_family_ids.add(json.loads(line)["family_id"])
assert len(_r2_sentence_family_ids) == 10, f"expected 10 R2-sentence families, got {len(_r2_sentence_family_ids)}"

EXCLUDED_SEED_IDS = PRIOR_EXCLUDED_SEED_IDS | _r2_sentence_family_ids
assert len(EXCLUDED_SEED_IDS) == 43, f"expected 43 excluded seeds, got {len(EXCLUDED_SEED_IDS)}"

# Held identical to EXP-DATA-001-R2-sentence -- this experiment does not
# vary these.
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
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED + 5,
    )
    assert not (set(seed_ids) & EXCLUDED_SEED_IDS), "seed overlap with prior experiments -- must not happen"
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED + 5)
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

    print(f"\nWrote {len(all_records)} total records to {samples_path}")
    print("Next: run apply_automated_screen.py, then manual semantic review.")


if __name__ == "__main__":
    main()
