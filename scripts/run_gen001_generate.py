"""
GEN-001 -- Stage 1: generate Phi-3.5-mini-instruct `full_ai` counterparts
for the 23 human essays already in PRIMARY-DATASET-v1's frozen `test`
split (DEC-019, docs/experiments/GEN-001.md).

Held-out generator principle: this script ONLY generates new text. It
does not touch PRIMARY-DATASET-v1, does not retrain or reselect anything,
and does not evaluate the detector. Evaluation is a separate stage
(run_gen001_evaluate.py), applied to this output unchanged.

Reuses, byte-for-byte, the same full_ai generation methodology already
validated for Qwen (run_exp_data_001.generate_full_ai): same
FULL_GENERATION_INSTRUCTION/META templates, same temperature=0.85/
top_p=0.95, same length-budgeting (generation_utils.budget_max_new_tokens
/ truncate_to_word_budget), same QC checks (run_qc_common). The ONLY
variable changed is the generator itself (phi_generate instead of
qwen_generate) -- this isolates "which generator produced the text" as
the sole difference under test, per GEN-001's research question.

Output: data/generated/GEN-001/samples.jsonl -- stored separately from
PRIMARY-DATASET-v1, never merged into it.
"""

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402
from app.services.text_normalizer import normalize_text  # noqa: E402

import generation_utils as gu  # noqa: E402
import phi_generate  # noqa: E402
from run_exp_data_001 import FULL_GENERATION_INSTRUCTION, FULL_GENERATION_META, run_qc_common  # noqa: E402

PERSUADE_FILE = REPO_ROOT / "data" / "raw" / "persuade_2.0" / "persuade_2.0_human_scores_demo_id_github.csv"
PRIMARY_SAMPLES_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "samples.jsonl"
PRIMARY_MANIFEST_PATH = REPO_ROOT / "data" / "generated" / "PRIMARY-DATASET-v1" / "inclusion_manifest.json"

# Recorded 2026-08-15, immediately before GEN-001 generation, and checked
# again at the top of main() -- the human source essays and manifest must
# be byte-identical to when EXP-003C was reviewed and accepted.
EXPECTED_SAMPLES_MD5 = "44c1ae6464aaec9d0e74f2b217c0133c"
EXPECTED_MANIFEST_MD5 = "029b72d69cf579faadc8aef9a2073d54"

OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "GEN-001"

GENERATION_TEMPERATURE = 0.85  # identical to run_exp_data_001.generate_full_ai
GENERATION_TOP_P = 0.95

_gen_seed_counter = [5000]  # distinct namespace from Qwen's (starts at 1000) -- no functional meaning beyond that


def next_gen_seed() -> int:
    _gen_seed_counter[0] += 1
    return _gen_seed_counter[0]


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def verify_primary_dataset_unchanged() -> None:
    actual_samples = _md5(PRIMARY_SAMPLES_PATH)
    actual_manifest = _md5(PRIMARY_MANIFEST_PATH)
    if actual_samples != EXPECTED_SAMPLES_MD5:
        raise RuntimeError(
            f"PRIMARY-DATASET-v1/samples.jsonl checksum changed: "
            f"expected {EXPECTED_SAMPLES_MD5}, got {actual_samples}. Stopping -- do not generate against a modified frozen dataset."
        )
    if actual_manifest != EXPECTED_MANIFEST_MD5:
        raise RuntimeError(
            f"PRIMARY-DATASET-v1/inclusion_manifest.json checksum changed: "
            f"expected {EXPECTED_MANIFEST_MD5}, got {actual_manifest}. Stopping -- do not generate against a modified frozen dataset."
        )
    print("Verified: PRIMARY-DATASET-v1 samples.jsonl and inclusion_manifest.json checksums match the frozen values.")


def load_frozen_test_human_essays() -> list[dict]:
    with open(PRIMARY_SAMPLES_PATH) as f:
        records = [json.loads(line) for line in f if line.strip()]
    human_test = [r for r in records if r["label"] == "human" and r["split"] == "test"]
    if len(human_test) != 23:
        raise RuntimeError(f"Expected exactly 23 frozen test-split human essays, found {len(human_test)}.")
    return human_test


def load_persuade_metadata(family_ids: set[str]) -> dict[str, dict]:
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["essay_id_comp"].isin(family_ids)]
    if len(df) != len(family_ids):
        missing = family_ids - set(df["essay_id_comp"])
        raise RuntimeError(f"Missing PERSUADE metadata for family_ids: {missing}")
    return {row["essay_id_comp"]: {"task": row["task"], "assignment": row["assignment"]} for _, row in df.iterrows()}


def make_gen001_record(
    sample_id, family_id, source_sample_id, text, target_length_words,
    generation_config, prompt_template_id, qc_status, qc_notes,
    instruction_leakage_flagged, ai_self_reference_flagged,
) -> dict:
    return {
        "sample_id": sample_id,
        "family_id": family_id,
        "experiment": "GEN-001",
        "split": "held_out_test",  # not one of PRIMARY-DATASET-v1's train/validation/test splits -- explicit, distinct value
        "source_corpus": "persuade_2.0",
        "label": "machine",
        "transformation_type": "full_ai",
        "source_sample_id": source_sample_id,  # the PRIMARY-DATASET-v1 human sample this essay is paired with
        "text": text,
        "actual_length_words": len(text.split()) if text else 0,
        "target_length_words": target_length_words,
        "generation_model": phi_generate.MODEL_NAME,
        "generation_model_revision": phi_generate.model_revision(),
        "generation_config": generation_config,
        "prompt_template_id": prompt_template_id,
        "instruction_leakage_flagged": instruction_leakage_flagged,
        "ai_self_reference_flagged": ai_self_reference_flagged,
        "qc_status": qc_status,
        "qc_notes": qc_notes,
    }


def generate_phi_full_ai(human_record: dict, persuade_meta: dict) -> dict:
    target_words = human_record["target_length_words"]
    task_type_desc = "persuasive/argumentative" if persuade_meta["task"] == "Independent" else "text-dependent argumentative"
    instruction = FULL_GENERATION_INSTRUCTION.format(
        task_type_desc=task_type_desc, target_words=target_words, prompt_text=persuade_meta["assignment"]
    )
    meta_instruction = FULL_GENERATION_META.format(task_type_desc=task_type_desc, target_words=target_words)
    max_new_tokens = gu.budget_max_new_tokens(target_words)
    gen_seed = next_gen_seed()
    result = phi_generate.generate(
        instruction, max_new_tokens=max_new_tokens,
        temperature=GENERATION_TEMPERATURE, top_p=GENERATION_TOP_P, seed=gen_seed,
    )

    text = normalize_text(result.text)
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc) if doc is not None else []
    truncated = gu.truncate_to_word_budget(text, [s.end_char for s in sentences], target_words) if sentences else text

    notes, flags = run_qc_common(meta_instruction, truncated, min_words=30, max_words=int(target_words * 2))
    qc_status = "passed" if not notes else "flagged"

    return make_gen001_record(
        sample_id=f"{human_record['family_id']}__phi_full_ai",
        family_id=human_record["family_id"],
        source_sample_id=human_record["sample_id"],
        text=truncated,
        target_length_words=target_words,
        generation_config=result.generation_config,
        prompt_template_id="full_generation_v1",  # identical template id to Qwen's -- same instruction wrapper
        qc_status=qc_status,
        qc_notes=notes,
        instruction_leakage_flagged=flags["instruction_leakage"],
        ai_self_reference_flagged=flags["ai_self_reference"],
    )


def main() -> None:
    verify_primary_dataset_unchanged()

    human_essays = load_frozen_test_human_essays()
    print(f"Loaded {len(human_essays)} frozen test-split human essays.")

    persuade_meta = load_persuade_metadata({r["family_id"] for r in human_essays})

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    samples_path = OUTPUT_DIR / "samples.jsonl"

    already_done = set()
    all_records = []
    if samples_path.exists():
        with open(samples_path) as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    all_records.append(rec)
                    already_done.add(rec["sample_id"])
        print(f"Resuming: {len(already_done)} records already present")

    with open(samples_path, "a") as f:
        for i, human_record in enumerate(human_essays):
            sample_id = f"{human_record['family_id']}__phi_full_ai"
            if sample_id in already_done:
                print(f"[{i+1}/{len(human_essays)}] {sample_id} -- already done, skipping")
                continue
            print(f"[{i+1}/{len(human_essays)}] Generating {sample_id} (target_words={human_record['target_length_words']})...")
            record = generate_phi_full_ai(human_record, persuade_meta[human_record["family_id"]])
            all_records.append(record)
            f.write(json.dumps(record) + "\n")
            f.flush()

    print(f"\nWrote {len(all_records)} total records to {samples_path}")
    flagged = [r for r in all_records if r["qc_status"] == "flagged"]
    print(f"QC: {len(all_records) - len(flagged)} passed, {len(flagged)} flagged")
    for r in flagged:
        print(f"  FLAGGED {r['sample_id']}: {r['qc_notes']}")


if __name__ == "__main__":
    main()
