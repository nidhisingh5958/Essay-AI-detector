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

POST-PILOT PATCH (2026-08-10, after DEC-011's revision): this file was
executed once (results preserved in reports/EXP-DATA-001.md and NOT
re-run) and has since been patched for two things found by that run,
without a second full execution:
  1. The prompt-leakage QC check now uses check_instruction_leakage with
     META-only instruction text (the old check compared against the
     whole formatted instruction, including embedded prompt text, which
     produced false positives -- see DEC-011 "Pilot Findings").
  2. `light_polish`/`moderate_polish` now record
     ground_truth_confidence="essay_level_only" and modified_spans=None,
     per DEC-011's revised three-regime structure (Regime C: whole-essay
     polish is not sentence-level ground truth). The sentence-diff
     computation is retained ONLY as a diagnostic (written to
     diffs.json) -- per instruction, alignment/diffing is not used to
     manufacture sentence-level labels for this regime.
The small, explicitly-scoped follow-up validation for the *new*
controlled-span light/moderate mechanism is a separate script,
run_exp_data_001_r1.py -- not a second run of this file.
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

# META-only counterparts of the instructions above: the wrapper/meta
# language WITHOUT any interpolated topic content (prompt text, target
# sentence/paragraph, surrounding context). Used exclusively for the
# instruction-leakage QC check (check_instruction_leakage) -- never pass
# the full formatted instruction to that check, since a generated essay
# is expected to legitimately echo its prompt/target content (see the
# POST-PILOT PATCH note above and DEC-011).
LIGHT_POLISH_META = (
    "Lightly copy-edit the following essay for grammar and word choice only. "
    "Do not change the structure, paragraph breaks, content, or ideas, and do not "
    "add or remove sentences. Return only the edited essay, with no preamble or commentary."
)
MODERATE_POLISH_META = (
    "Moderately rephrase the following essay: you may reword sentences for clarity and "
    "flow, but do not reorder sentences or paragraphs, do not add or remove sentences, and "
    "do not change the meaning or arguments. Return only the rewritten essay, with no "
    "preamble or commentary."
)
SENTENCE_REWRITE_META = (
    "Rewrite ONLY the following sentence, preserving its meaning and matching the tone of "
    "the surrounding context. Return only the rewritten sentence, with no preamble, quotation "
    "marks, or commentary."
)
PARAGRAPH_REWRITE_META = (
    "Rewrite ONLY the following paragraph, preserving its meaning and matching the tone of "
    "the surrounding essay. Return only the rewritten paragraph, with no preamble or commentary."
)
FULL_GENERATION_META = (
    "Write a {task_type_desc} essay of approximately {target_words} words responding to the "
    "following prompt. Write in the voice of a student. Return only the essay, with no preamble "
    "or title."
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
    intended_span_index=None,
    span_target_words=None,
    span_actual_words=None,
    resegmentation_ok=None,
    instruction_leakage_flagged=False,
    ai_self_reference_flagged=False,
    cross_family_duplicate_flag=False,
    semantic_preservation=None,
    semantic_preservation_notes=None,
):
    """Fields added for EXP-DATA-001-R1 confirmation-round measurability
    (all optional, default to None/False so EXP-DATA-001/R1's original
    call sites -- preserved, not rewritten -- remain valid):

    - intended_span_index / span_target_words / span_actual_words: the
      SPAN-level (not whole-essay) target vs. actual, since the
      whole-record actual_length_words/target_length_words below
      describe the whole spliced text and conflating the two was a
      source of confusion in earlier analysis.
    - resegmentation_ok: explicit bool, not just a qc_notes string.
    - instruction_leakage_flagged / ai_self_reference_flagged: explicit
      bools, always present (not just noted when true), so raw
      distributions can be reported even when nothing was flagged.
    - cross_family_duplicate_flag: filled in post-hoc by a batch
      near_duplicate_pairs_scoped pass, default False.
    - semantic_preservation / semantic_preservation_notes: manual-review
      fields (see generation_utils.SEMANTIC_PRESERVATION_VALUES) --
      never set automatically to anything but "not_yet_reviewed" or None.
    """
    length_ratio = None
    if span_target_words and span_actual_words is not None and span_target_words > 0:
        length_ratio = round(span_actual_words / span_target_words, 3)

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
        "intended_span_index": intended_span_index,
        "span_target_words": span_target_words,
        "span_actual_words": span_actual_words,
        "length_ratio_actual_vs_target": length_ratio,
        "ground_truth_confidence": ground_truth_confidence,
        "modified_spans": modified_spans,
        "resegmentation_ok": resegmentation_ok,
        "generation_model": qwen_generate.MODEL_NAME if generation_config else None,
        "generation_model_revision": qwen_generate.model_revision() if generation_config else None,
        "generation_config": generation_config,
        "prompt_template_id": prompt_template_id,
        "instruction_leakage_flagged": instruction_leakage_flagged,
        "ai_self_reference_flagged": ai_self_reference_flagged,
        "cross_family_duplicate_flag": cross_family_duplicate_flag,
        "semantic_preservation": semantic_preservation,
        "semantic_preservation_notes": semantic_preservation_notes,
        "qc_status": qc_status,
        "qc_notes": qc_notes,
    }


def run_qc_common(meta_instruction: str | None, text: str, min_words: int, max_words: int) -> tuple[list[str], dict]:
    """`meta_instruction` must be the META/wrapper-only instruction text
    (see the *_META constants above) -- never the fully-interpolated
    instruction, which would embed prompt/target content the output is
    expected to legitimately reference (see POST-PILOT PATCH note).

    Returns (notes, flags). `flags` exposes each check's boolean result
    explicitly (not just as a conditional note string), so raw
    pass/fail distributions can be reported even for checks that never
    fired -- per the explicit instruction to report full distributions,
    not just violations."""
    flags = {
        "empty_output": False,
        "length_out_of_bounds": False,
        "instruction_leakage": False,
        "ai_self_reference": False,
        "excessive_repetition": False,
        "instruction_artifact": False,
    }
    notes = []
    if gu.check_empty_output(text):
        notes.append("empty_output")
        flags["empty_output"] = True
        return notes, flags  # nothing else is checkable on empty text
    word_count = len(text.split())
    if not gu.check_length_bounds(word_count, min_words, max_words):
        notes.append(f"length_out_of_bounds(words={word_count},min={min_words},max={max_words})")
        flags["length_out_of_bounds"] = True
    if meta_instruction and gu.check_instruction_leakage(meta_instruction, text):
        notes.append("instruction_leakage")
        flags["instruction_leakage"] = True
    if gu.check_ai_self_reference(text):
        notes.append("ai_self_reference")
        flags["ai_self_reference"] = True
    repetition_flagged, ratio = gu.check_excessive_repetition([w.lower() for w in text.split()])
    if repetition_flagged:
        notes.append(f"excessive_repetition(ratio={ratio:.2f})")
        flags["excessive_repetition"] = True
    if gu.check_instruction_artifacts(text):
        notes.append("instruction_artifact_preamble")
        flags["instruction_artifact"] = True
    return notes, flags


def generate_full_ai(seed: dict, split: str) -> dict:
    target_words = seed["word_count"]
    task_type_desc = "persuasive/argumentative" if seed["task"] == "Independent" else "text-dependent argumentative"
    instruction = FULL_GENERATION_INSTRUCTION.format(
        task_type_desc=task_type_desc, target_words=target_words, prompt_text=seed["assignment"]
    )
    meta_instruction = FULL_GENERATION_META.format(task_type_desc=task_type_desc, target_words=target_words)
    max_new_tokens = gu.budget_max_new_tokens(target_words)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=0.85, top_p=0.95, seed=gen_seed)

    text = normalize_text(result.text)
    doc = parse_document(text)
    sentences = segment_sentences(text, doc=doc) if doc is not None else []
    truncated = gu.truncate_to_word_budget(text, [s.end_char for s in sentences], target_words) if sentences else text

    notes, flags = run_qc_common(meta_instruction, truncated, min_words=30, max_words=int(target_words * 2))
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
        instruction_leakage_flagged=flags["instruction_leakage"],
        ai_self_reference_flagged=flags["ai_self_reference"],
    )


def generate_polish(seed: dict, split: str, category: str) -> dict:
    """Regime C (DEC-011 revision): whole-essay light/moderate polish
    produces ESSAY-LEVEL-ONLY ground truth -- we know with certainty the
    whole essay passed through this generation process, but we make NO
    sentence-level claim from it. The sentence-diff below is computed and
    logged strictly as a DIAGNOSTIC (structure-drift detection, observed
    similarity range for documentation) -- per explicit instruction, it
    is never used to manufacture per-sentence labels for this category."""
    instruction_template = LIGHT_POLISH_INSTRUCTION if category == "light_polish" else MODERATE_POLISH_INSTRUCTION
    meta_instruction = LIGHT_POLISH_META if category == "light_polish" else MODERATE_POLISH_META
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

    # Diagnostic only -- see docstring. Not used to set modified_spans.
    diff = gu.align_and_diff_sentences([s.text for s in orig_sentences], [s.text for s in cand_sentences])

    notes, flags = run_qc_common(meta_instruction, candidate_text, min_words=30, max_words=int(seed["word_count"] * 2))
    orig_words = seed["word_count"]
    cand_words = len(candidate_text.split())
    if orig_words and abs(cand_words - orig_words) / orig_words > 0.4:
        notes.append(f"length_drift_vs_original({cand_words}_vs_{orig_words})")
    if diff["structure_drift"]:
        # Informative, not disqualifying: essay-level ground truth ("this
        # essay was AI-polished") holds regardless of how much internal
        # restructuring occurred -- unlike the old design, this no longer
        # invalidates the sample, since no sentence-level claim depends on it.
        notes.append("structure_drift_observed")

    qc_status = "rejected" if "empty_output" in notes else ("flagged" if notes else "passed")

    return {
        "record": make_sample_record(
            sample_id=f"{seed['id']}__{category}",
            family_id=seed["id"],
            split=split,
            label="ai_assisted",
            transformation_type=category,
            source_sample_id=f"{seed['id']}__human",
            text=candidate_text,
            ground_truth_confidence="essay_level_only",
            modified_spans=None,  # never derived from alignment for this regime -- see docstring
            generation_config=result.generation_config,
            prompt_template_id=f"{category}_v1",
            target_length_words=orig_words,
            qc_status=qc_status,
            qc_notes=notes,
            instruction_leakage_flagged=flags["instruction_leakage"],
            ai_self_reference_flagged=flags["ai_self_reference"],
        ),
        "diff": diff,  # diagnostic export only (diffs.json)
    }


def generate_sentence_transform(
    seed: dict,
    split: str,
    category: str,
    instruction_template: str,
    meta_instruction: str,
    temperature: float,
    expected_length_ratio_range: tuple[float, float],
) -> dict:
    """Regime A (surgical sentence-level transformation). Shared by
    `sentence_rewrite_single` (full-rewrite instruction) and the
    post-pilot controlled-span additions (`sentence_light_controlled`,
    `sentence_moderate_controlled`) -- same splice mechanism and the same
    exact-ground-truth guarantee, only the instruction wording and the
    documented intended length-modification scope differ per category
    (`expected_length_ratio_range` -- e.g. light edits should stay close
    to 1.0x the original sentence's length; a full rewrite is allowed a
    wider range). Deviation from that documented scope is flagged, not
    silently ignored -- see the `modification_scope` QC note below."""
    original_text = normalize_text(seed["full_text"])
    doc = parse_document(original_text)
    sentences = segment_sentences(original_text, doc=doc)
    sentence_texts = [s.text for s in sentences]

    idx = gu.pick_rewrite_sentence_index(sentence_texts, rng_seed=RNG_SEED)
    if idx is None:
        return make_sample_record(
            sample_id=f"{seed['id']}__{category}",
            family_id=seed["id"], split=split, label="ai_assisted", transformation_type=category,
            source_sample_id=f"{seed['id']}__human", text=None, ground_truth_confidence="high", modified_spans=None,
            generation_config=None, prompt_template_id=f"{category}_v1", target_length_words=None,
            qc_status="skipped", qc_notes=["no_suitable_sentence_found"],
        )

    target = sentences[idx]
    before = sentence_texts[idx - 1] if idx > 0 else ""
    after = sentence_texts[idx + 1] if idx < len(sentence_texts) - 1 else ""
    instruction = instruction_template.format(before=before, target=target.text, after=after)
    target_words = len(target.text.split())

    max_new_tokens = gu.budget_max_new_tokens(target_words + 5)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=temperature, top_p=0.95, seed=gen_seed)
    rewritten = normalize_text(result.text).strip().strip('"')

    spliced = original_text[: target.start_char] + rewritten + original_text[target.end_char :]

    notes, flags = run_qc_common(meta_instruction, rewritten, min_words=2, max_words=max(80, target_words * 4))

    # Documented modification-scope validation (Section 6, user instruction):
    # does the output actually stay within the length ratio this category
    # claims to target, or did it drift into a different category's territory?
    # Always recorded via span_actual_words/span_target_words below, not
    # just noted when it drifts -- raw distributions, not just violations.
    rewritten_words = len(rewritten.split())
    if target_words > 0 and rewritten:
        ratio = rewritten_words / target_words
        lo, hi = expected_length_ratio_range
        if not (lo <= ratio <= hi):
            notes.append(f"modification_scope_drift(ratio={ratio:.2f},expected=[{lo},{hi}])")

    # Correctness QC: re-segment the spliced essay and confirm sentence count is unchanged
    # and the target index now contains (approximately) the rewritten text.
    # Kept as an unconditional hard-reject rule -- this is what Regime A/B's
    # "exact ground truth" claim depends on; do not relax it.
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
        sample_id=f"{seed['id']}__{category}",
        family_id=seed["id"], split=split, label="ai_assisted", transformation_type=category,
        source_sample_id=f"{seed['id']}__human", text=spliced, ground_truth_confidence="high",
        modified_spans=modified_spans, generation_config=result.generation_config,
        prompt_template_id=f"{category}_v1", target_length_words=target_words,
        qc_status=qc_status, qc_notes=notes,
        intended_span_index=idx,
        span_target_words=target_words,
        span_actual_words=rewritten_words,
        resegmentation_ok=resegmentation_ok,
        instruction_leakage_flagged=flags["instruction_leakage"],
        ai_self_reference_flagged=flags["ai_self_reference"],
        semantic_preservation="not_yet_reviewed",
    )


def generate_sentence_rewrite(seed: dict, split: str) -> dict:
    """Thin wrapper: `sentence_rewrite_single` = generate_sentence_transform
    with the full-rewrite instruction and a wide expected length ratio."""
    return generate_sentence_transform(
        seed, split, "sentence_rewrite_single",
        SENTENCE_REWRITE_INSTRUCTION, SENTENCE_REWRITE_META,
        temperature=0.8, expected_length_ratio_range=(0.3, 3.0),
    )


def generate_paragraph_transform(
    seed: dict,
    split: str,
    category: str,
    instruction_template: str,
    meta_instruction: str,
    temperature: float,
    expected_length_ratio_range: tuple[float, float],
) -> dict:
    """Regime B (surgical paragraph-level transformation) -- the
    paragraph-granularity counterpart to generate_sentence_transform.
    Same principle: instruction intensity (full rewrite vs. light/
    moderate controlled) is a parameter of one mechanism, not a
    different one, and ground truth stays exact because the mechanism
    (splice a pre-selected paragraph) guarantees it regardless of
    wording."""
    original_text = normalize_text(seed["full_text"])
    paragraphs = original_text.split("\n\n")

    idx = gu.pick_rewrite_paragraph_index(paragraphs, rng_seed=RNG_SEED)
    if idx is None:
        return make_sample_record(
            sample_id=f"{seed['id']}__{category}",
            family_id=seed["id"], split=split, label="ai_assisted", transformation_type=category,
            source_sample_id=f"{seed['id']}__human", text=None, ground_truth_confidence="high", modified_spans=None,
            generation_config=None, prompt_template_id=f"{category}_v1", target_length_words=None,
            qc_status="skipped", qc_notes=["no_suitable_paragraph_found"],
        )

    target_paragraph = paragraphs[idx]
    target_words = len(target_paragraph.split())
    instruction = instruction_template.format(target=target_paragraph)

    max_new_tokens = gu.budget_max_new_tokens(target_words + 10)
    gen_seed = next_gen_seed()
    result = qwen_generate.generate(instruction, max_new_tokens=max_new_tokens, temperature=temperature, top_p=0.95, seed=gen_seed)
    rewritten_paragraph = normalize_text(result.text).strip()
    rewritten_words = len(rewritten_paragraph.split())

    new_paragraphs = list(paragraphs)
    new_paragraphs[idx] = rewritten_paragraph
    spliced = "\n\n".join(new_paragraphs)

    notes, flags = run_qc_common(meta_instruction, rewritten_paragraph, min_words=5, max_words=max(200, target_words * 4))

    if target_words > 0 and rewritten_paragraph:
        ratio = rewritten_words / target_words
        lo, hi = expected_length_ratio_range
        if not (lo <= ratio <= hi):
            notes.append(f"modification_scope_drift(ratio={ratio:.2f},expected=[{lo},{hi}])")

    spliced_doc = parse_document(spliced)
    spliced_sentences = segment_sentences(spliced, doc=spliced_doc) if spliced_doc is not None else []
    char_start = len("\n\n".join(new_paragraphs[:idx])) + (2 if idx > 0 else 0)
    char_end = char_start + len(rewritten_paragraph)
    modified_spans = [
        {"sentence_index": s.index, "char_start": s.start_char, "char_end": s.end_char}
        for s in spliced_sentences
        if s.start_char >= char_start and s.end_char <= char_end
    ]
    # Paragraph-level "resegmentation_ok" doesn't require the same TOTAL
    # sentence count as the original (a rephrased paragraph may
    # legitimately combine/split its own internal sentences) -- what
    # matters is whether the rewritten paragraph's character range still
    # resolves to at least one real sentence in the re-parsed spliced
    # text. If it doesn't, we cannot confidently say which sentences are
    # AI-touched, so treat it the same as a resegmentation failure: reject.
    resegmentation_ok = bool(modified_spans)
    if not resegmentation_ok:
        notes.append("paragraph_span_had_no_resolvable_sentences")

    qc_status = "rejected" if "empty_output" in notes or not resegmentation_ok else ("flagged" if notes else "passed")

    return make_sample_record(
        sample_id=f"{seed['id']}__{category}",
        family_id=seed["id"], split=split, label="ai_assisted", transformation_type=category,
        source_sample_id=f"{seed['id']}__human", text=spliced, ground_truth_confidence="high",
        modified_spans=modified_spans, generation_config=result.generation_config,
        prompt_template_id=f"{category}_v1", target_length_words=target_words,
        qc_status=qc_status, qc_notes=notes,
        intended_span_index=idx,
        span_target_words=target_words,
        span_actual_words=rewritten_words,
        resegmentation_ok=resegmentation_ok,
        instruction_leakage_flagged=flags["instruction_leakage"],
        ai_self_reference_flagged=flags["ai_self_reference"],
        semantic_preservation="not_yet_reviewed",
    )


def generate_paragraph_rewrite(seed: dict, split: str) -> dict:
    """Thin wrapper: `paragraph_rewrite_single` = generate_paragraph_transform
    with the full-rewrite instruction and a wide expected length ratio."""
    return generate_paragraph_transform(
        seed, split, "paragraph_rewrite_single",
        PARAGRAPH_REWRITE_INSTRUCTION, PARAGRAPH_REWRITE_META,
        temperature=0.8, expected_length_ratio_range=(0.3, 3.0),
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
