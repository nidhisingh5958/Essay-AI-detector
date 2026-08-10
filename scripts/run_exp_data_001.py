"""
EXP-DATA-001 -- Generation Pipeline Pilot.

Generates 10 seed human essays x 6 categories = 60 samples (human
original, full AI generation, light polish, moderate polish,
single-sentence rewrite, single-paragraph rewrite), using the real
acquired PERSUADE 2.0 corpus and Qwen2.5-1.5B-Instruct (DEC-010).

This script evaluates the DATA GENERATION PIPELINE. It does not run or
evaluate a detector, compute detection accuracy, or use a detector to
label anything -- ground truth comes entirely from the known generation
process (see generation_utils.align_and_diff_sentences for the
diff-based categories and the explicit splice-index bookkeeping for the
surgical-rewrite categories).

Output: data/generated/EXP-DATA-001/samples.jsonl (all attempted samples,
including rejected ones, each carrying qc_status), plus
data/generated/EXP-DATA-001/summary.json (aggregated statistics used to
write reports/EXP-DATA-001.md). Both gitignored under data/*.
"""

import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.sentence_segmenter import parse_document, segment_sentences  # noqa: E402
from app.services.text_normalizer import normalize_text  # noqa: E402

import generation_utils as gu  # noqa: E402
import qwen_generate  # noqa: E402

PERSUADE_FILE = REPO_ROOT / "data" / "raw" / "persuade_2.0" / "persuade_2.0_human_scores_demo_id_github.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "generated" / "EXP-DATA-001"

N_SEEDS = 10
SEED_MIN_WORDS = 150
SEED_MAX_WORDS = 320
RNG_SEED = 42

LIGHT_POLISH_INSTRUCTION = (
    "Lightly copy-edit the following essay for grammar and word choice only. "
    "Do not change the structure, paragraph breaks, content, or ideas, and do not "
    "add or remove sentences. Return only the edited essay, with no preamble or commentary.\n\n"
    "Essay:\n{text}"
)
MODERATE_POLISH_INSTRUCTION = (
    "Moderately rephrase the following essay: you may reword sentences for clarity and "
    "flow, but do not reorder sentences or paragraphs, do not add or remove sentences, and "
    "do not change the meaning or arguments. Return only the rewritten essay, with no "
    "preamble or commentary.\n\nEssay:\n{text}"
)
SENTENCE_REWRITE_INSTRUCTION = (
    "Rewrite ONLY the following sentence, preserving its meaning and matching the tone of "
    "the surrounding context. Return only the rewritten sentence, with no preamble, quotation "
    "marks, or commentary.\n\nContext before: {before}\nSentence to rewrite: {target}\n"
    "Context after: {after}"
)
PARAGRAPH_REWRITE_INSTRUCTION = (
    "Rewrite ONLY the following paragraph, preserving its meaning and matching the tone of "
    "the surrounding essay. Return only the rewritten paragraph, with no preamble or commentary.\n\n"
    "Paragraph to rewrite:\n{target}"
)
FULL_GENERATION_INSTRUCTION = (
    "Write a {task_type_desc} essay of approximately {target_words} words responding to the "
    "following prompt. Write in the voice of a student. Return only the essay, with no preamble "
    "or title.\n\nPrompt: {prompt_text}"
)

_rng_counter = [1000]  # simple incrementing counter for per-call generation seeds


def next_gen_seed() -> int:
    _rng_counter[0] += 1
    return _rng_counter[0]


def load_candidate_records(df: pd.DataFrame) -> list[dict]:
    """Cheap, corpus-wide filtering pass using regex-based proxies (not
    the real spaCy segmenter, which is reserved for the 10 selected
    seeds) -- running the real segmenter over all 25,996 essays just to
    pick 10 candidates would be needlessly slow."""
    records = []
    for _, row in df.iterrows():
        text = str(row["full_text"])
        word_count = len(text.split())
        sentence_count_proxy = len(re.split(r"(?<=[.!?])\s+", text.strip())) if text.strip() else 0
        paragraph_count_proxy = len(text.split("\n\n"))
        records.append(
            {
                "id": row["essay_id_comp"],
                "word_count": word_count,
                "sentence_count": sentence_count_proxy,
                "paragraph_count": paragraph_count_proxy,
                "prompt_name": row["prompt_name"],
                "task": row["task"],
                "assignment": row["assignment"],
                "full_text": text,
            }
        )
    return records


def make_sample_record(
    sample_id, family_id, split, label, transformation_type, source_sample_id, text,
    ground_truth_confidence, modified_spans, generation_config, prompt_template_id,
    target_length_words, qc_status, qc_notes,
):
    return {
        "sample_id": sample_id,
        "family_id": family_id,
        "split": split,
        "source_corpus": "persuade_2.0",
        "label": label,
        "transformation_type": transformation_type,
        "source_sample_id": source_sample_id,
        "text": text,
        "actual_length_words": len(text.split()) if text else 0,
        "target_length_words": target_length_words,
        "ground_truth_confidence": ground_truth_confidence,
        "modified_spans": modified_spans,
        "generation_model": qwen_generate.MODEL_NAME if generation_config else None,
        "generation_model_revision": qwen_generate.model_revision() if generation_config else None,
        "generation_config": generation_config,
        "prompt_template_id": prompt_template_id,
        "qc_status": qc_status,
        "qc_notes": qc_notes,
    }


def run_qc_common(instruction: str | None, text: str, min_words: int, max_words: int) -> list[str]:
    notes = []
    if gu.check_empty_output(text):
        notes.append("empty_output")
        return notes  # nothing else is checkable on empty text
    word_count = len(text.split())
    if not gu.check_length_bounds(word_count, min_words, max_words):
        notes.append(f"length_out_of_bounds(words={word_count},min={min_words},max={max_words})")
    if instruction and gu.check_prompt_leakage(instruction, text):
        notes.append("prompt_leakage")
    flagged, ratio = gu.check_excessive_repetition([w.lower() for w in text.split()])
    if flagged:
        notes.append(f"excessive_repetition(ratio={ratio:.2f})")
    if gu.check_instruction_artifacts(text):
        notes.append("instruction_artifact_preamble")
    return notes


def generate_full_ai(seed: dict, split: str) -> dict:
    target_words = seed["word_count"]
    task_type_desc = "persuasive/argumentative" if seed["task"] == "Independent" else "text-dependent argumentative"
    instruction = FULL_GENERATION_INSTRUCTION.format(
        task_type_desc=task_type_desc, target_words=target_words, prompt_text=seed["assignment"]
    )
    max_new_tokens = gu.budget_max_new_tokens(target_words)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=0.85, top_p=0.95, seed=gen_seed)

    text = normalize_text(result.text)
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc) if doc is not None else []
    truncated = gu.truncate_to_word_budget(text, [s.end_char for s in sentences], target_words) if sentences else text

    notes = run_qc_common(instruction, truncated, min_words=30, max_words=int(target_words * 2))
    qc_status = "passed" if not notes else "flagged"

    return make_sample_record(
        sample_id=f"{seed['id']}__full_ai",
        family_id=seed["id"],
        split=split,
        label="machine",
        transformation_type="full_ai",
        source_sample_id=None,
        text=truncated,
        ground_truth_confidence="high",
        modified_spans=[{"sentence_index": i, "note": "entire sample is machine-generated"} for i in range(len(sentences))],
        generation_config=result.generation_config,
        prompt_template_id="full_generation_v1",
        target_length_words=target_words,
        qc_status=qc_status,
        qc_notes=notes,
    )


def generate_polish(seed: dict, split: str, category: str) -> dict:
    instruction_template = LIGHT_POLISH_INSTRUCTION if category == "light_polish" else MODERATE_POLISH_INSTRUCTION
    original_text = normalize_text(seed["full_text"])
    instruction = instruction_template.format(text=original_text)

    max_new_tokens = gu.budget_max_new_tokens(seed["word_count"])
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=0.6, top_p=0.9, seed=gen_seed)
    candidate_text = normalize_text(result.text)

    orig_doc = parse_document(original_text)
    orig_sentences = segment_sentences(original_text, doc=orig_doc)
    cand_doc = parse_document(candidate_text)
    cand_sentences = segment_sentences(candidate_text, doc=cand_doc) if cand_doc is not None else []

    diff = gu.align_and_diff_sentences([s.text for s in orig_sentences], [s.text for s in cand_sentences])

    notes = run_qc_common(instruction, candidate_text, min_words=30, max_words=int(seed["word_count"] * 2))
    orig_words = seed["word_count"]
    cand_words = len(candidate_text.split())
    if orig_words and abs(cand_words - orig_words) / orig_words > 0.4:
        notes.append(f"length_drift_vs_original({cand_words}_vs_{orig_words})")
    if diff["structure_drift"]:
        notes.append("structure_drift")

    qc_status = "rejected" if "structure_drift" in notes or "empty_output" in notes else ("flagged" if notes else "passed")

    return {
        "record": make_sample_record(
            sample_id=f"{seed['id']}__{category}",
            family_id=seed["id"],
            split=split,
            label="ai_assisted",
            transformation_type=category,
            source_sample_id=f"{seed['id']}__human",
            text=candidate_text,
            ground_truth_confidence="approximate",
            modified_spans=None,  # filled in during post-hoc threshold analysis
            generation_config=result.generation_config,
            prompt_template_id=f"{category}_v1",
            target_length_words=orig_words,
            qc_status=qc_status,
            qc_notes=notes,
        ),
        "diff": diff,
    }


def generate_sentence_rewrite(seed: dict, split: str) -> dict:
    original_text = normalize_text(seed["full_text"])
    doc = parse_document(original_text)
    sentences = segment_sentences(original_text, doc=doc)
    sentence_texts = [s.text for s in sentences]

    idx = gu.pick_rewrite_sentence_index(sentence_texts, rng_seed=RNG_SEED)
    if idx is None:
        return make_sample_record(
            sample_id=f"{seed['id']}__sentence_rewrite_single",
            family_id=seed["id"], split=split, label="ai_assisted", transformation_type="sentence_rewrite_single",
            source_sample_id=f"{seed['id']}__human", text=None, ground_truth_confidence="high", modified_spans=None,
            generation_config=None, prompt_template_id="sentence_rewrite_v1", target_length_words=None,
            qc_status="skipped", qc_notes=["no_suitable_sentence_found"],
        )

    target = sentences[idx]
    before = sentence_texts[idx - 1] if idx > 0 else ""
    after = sentence_texts[idx + 1] if idx < len(sentence_texts) - 1 else ""
    instruction = SENTENCE_REWRITE_INSTRUCTION.format(before=before, target=target.text, after=after)

    max_new_tokens = gu.budget_max_new_tokens(len(target.text.split()) + 5)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=0.8, top_p=0.95, seed=gen_seed)
    rewritten = normalize_text(result.text).strip().strip('"')

    spliced = original_text[: target.start_char] + rewritten + original_text[target.end_char :]

    notes = run_qc_common(instruction, rewritten, min_words=2, max_words=max(80, len(target.text.split()) * 4))

    # Correctness QC: re-segment the spliced essay and confirm sentence count is unchanged
    # and the target index now contains (approximately) the rewritten text.
    spliced_doc = parse_document(spliced)
    spliced_sentences = segment_sentences(spliced, doc=spliced_doc) if spliced_doc is not None else []
    resegmentation_ok = len(spliced_sentences) == len(sentences)
    if not resegmentation_ok:
        notes.append(f"splice_resegmentation_mismatch(orig={len(sentences)},spliced={len(spliced_sentences)})")

    modified_spans = None
    if resegmentation_ok:
        new_span = spliced_sentences[idx]
        modified_spans = [{"sentence_index": idx, "char_start": new_span.start_char, "char_end": new_span.end_char}]

    qc_status = "rejected" if "splice_resegmentation_mismatch" in " ".join(notes) or "empty_output" in notes else ("flagged" if notes else "passed")

    return make_sample_record(
        sample_id=f"{seed['id']}__sentence_rewrite_single",
        family_id=seed["id"], split=split, label="ai_assisted", transformation_type="sentence_rewrite_single",
        source_sample_id=f"{seed['id']}__human", text=spliced, ground_truth_confidence="high",
        modified_spans=modified_spans, generation_config=result.generation_config,
        prompt_template_id="sentence_rewrite_v1", target_length_words=len(target.text.split()),
        qc_status=qc_status, qc_notes=notes,
    )


def generate_paragraph_rewrite(seed: dict, split: str) -> dict:
    original_text = normalize_text(seed["full_text"])
    paragraphs = original_text.split("\n\n")

    idx = gu.pick_rewrite_paragraph_index(paragraphs, rng_seed=RNG_SEED)
    if idx is None:
        return make_sample_record(
            sample_id=f"{seed['id']}__paragraph_rewrite_single",
            family_id=seed["id"], split=split, label="ai_assisted", transformation_type="paragraph_rewrite_single",
            source_sample_id=f"{seed['id']}__human", text=None, ground_truth_confidence="high", modified_spans=None,
            generation_config=None, prompt_template_id="paragraph_rewrite_v1", target_length_words=None,
            qc_status="skipped", qc_notes=["no_suitable_paragraph_found"],
        )

    target_paragraph = paragraphs[idx]
    instruction = PARAGRAPH_REWRITE_INSTRUCTION.format(target=target_paragraph)

    max_new_tokens = gu.budget_max_new_tokens(len(target_paragraph.split()) + 10)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=0.8, top_p=0.95, seed=gen_seed)
    rewritten_paragraph = normalize_text(result.text).strip()

    new_paragraphs = list(paragraphs)
    new_paragraphs[idx] = rewritten_paragraph
    spliced = "\n\n".join(new_paragraphs)

    notes = run_qc_common(instruction, rewritten_paragraph, min_words=5, max_words=max(200, len(target_paragraph.split()) * 4))

    spliced_doc = parse_document(spliced)
    spliced_sentences = segment_sentences(spliced, doc=spliced_doc) if spliced_doc is not None else []
    char_start = len("\n\n".join(new_paragraphs[:idx])) + (2 if idx > 0 else 0)
    char_end = char_start + len(rewritten_paragraph)
    modified_spans = [
        {"sentence_index": s.index, "char_start": s.start_char, "char_end": s.end_char}
        for s in spliced_sentences
        if s.start_char >= char_start and s.end_char <= char_end
    ]
    if not modified_spans:
        notes.append("paragraph_span_had_no_resolvable_sentences")

    qc_status = "rejected" if "empty_output" in notes else ("flagged" if notes else "passed")

    return make_sample_record(
        sample_id=f"{seed['id']}__paragraph_rewrite_single",
        family_id=seed["id"], split=split, label="ai_assisted", transformation_type="paragraph_rewrite_single",
        source_sample_id=f"{seed['id']}__human", text=spliced, ground_truth_confidence="high",
        modified_spans=modified_spans, generation_config=result.generation_config,
        prompt_template_id="paragraph_rewrite_v1", target_length_words=len(target_paragraph.split()),
        qc_status=qc_status, qc_notes=notes,
    )


def make_human_record(seed: dict, split: str) -> dict:
    text = normalize_text(seed["full_text"])
    return make_sample_record(
        sample_id=f"{seed['id']}__human", family_id=seed["id"], split=split, label="human",
        transformation_type="original", source_sample_id=None, text=text, ground_truth_confidence="high",
        modified_spans=[], generation_config=None, prompt_template_id=None,
        target_length_words=seed["word_count"], qc_status="passed", qc_notes=[],
    )


def main():
    print("Loading PERSUADE corpus...")
    df = pd.read_csv(PERSUADE_FILE, dtype={"essay_id_comp": str})
    df = df[df["task"] == "Independent"]  # keep the pilot self-contained (no source_text dependency)

    print("Filtering candidate seeds...")
    records = load_candidate_records(df)
    seed_ids = gu.select_seed_essays(
        records, n=N_SEEDS, min_words=SEED_MIN_WORDS, max_words=SEED_MAX_WORDS,
        min_sentences=5, min_paragraphs=2, rng_seed=RNG_SEED,
    )
    seeds_by_id = {r["id"]: r for r in records if r["id"] in seed_ids}
    print(f"Selected {len(seed_ids)} seed essays: {seed_ids}")

    splits = gu.assign_family_splits(seed_ids, rng_seed=RNG_SEED)
    print(f"Family split assignment (before generation): {splits}")

    all_records = []
    diffs_by_category = {"light_polish": [], "moderate_polish": []}

    for i, sid in enumerate(seed_ids):
        seed = seeds_by_id[sid]
        split = splits[sid]
        print(f"\n[{i+1}/{len(seed_ids)}] Seed {sid} (split={split}, words={seed['word_count']})")

        all_records.append(make_human_record(seed, split))

        print("  generating full_ai...")
        all_records.append(generate_full_ai(seed, split))

        print("  generating light_polish...")
        result = generate_polish(seed, split, "light_polish")
        all_records.append(result["record"])
        diffs_by_category["light_polish"].append((sid, result["diff"]))

        print("  generating moderate_polish...")
        result = generate_polish(seed, split, "moderate_polish")
        all_records.append(result["record"])
        diffs_by_category["moderate_polish"].append((sid, result["diff"]))

        print("  generating sentence_rewrite_single...")
        all_records.append(generate_sentence_rewrite(seed, split))

        print("  generating paragraph_rewrite_single...")
        all_records.append(generate_paragraph_rewrite(seed, split))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / "samples.jsonl", "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")

    # Serialize diff pair data (raw similarity scores) for post-hoc threshold analysis.
    diff_export = {
        category: [
            {"seed_id": sid, "structure_drift": d["structure_drift"], "pairs": [(a, b, r) for a, b, r in d["pairs"]]}
            for sid, d in pairs
        ]
        for category, pairs in diffs_by_category.items()
    }
    with open(OUTPUT_DIR / "diffs.json", "w") as f:
        json.dump(diff_export, f, indent=2)

    print(f"\nWrote {len(all_records)} records to {OUTPUT_DIR / 'samples.jsonl'}")
    print(f"Wrote diff data to {OUTPUT_DIR / 'diffs.json'}")


if __name__ == "__main__":
    main()
