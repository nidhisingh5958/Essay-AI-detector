# EXP-DATA-001-R4 — full_ai Pre-Scale Regression Check

**Date**: 2026-08-14
**Status**: Regression check only. No new methodology, no threshold
changes, no detector work.

## Purpose

Required prerequisite (per the post-R3 strategic review) before
generating the 150-family primary dataset: confirm the `full_ai`
mechanism — unchanged since EXP-DATA-001, but never re-exercised in a
live run with the fixed `check_instruction_leakage` — still behaves
correctly on fresh seeds. Not a methodology-discovery experiment.

## Setup

10 fresh PERSUADE seeds, excluding all 80 seed IDs used across every
prior generation experiment (EXP-DATA-001, R1, R1-confirmation,
R2-paragraph, R2-sentence, R3-sentence-light,
R3-paragraph-claim-survival). `human` + `full_ai` only = 20 records.
Same model (Qwen2.5-1.5B-Instruct), same revision
(`989aa7980e4cf806f80c7fef2b1adb7bc71aa306`), same
`full_generation_v1` prompt template as EXP-DATA-001. One background
interruption occurred mid-run (this environment's known behavior); the
script's existing resumable pattern (checks `samples.jsonl`, skips
completed `sample_id`s) resumed cleanly with no duplicate or lost
records.

## Results

**Instruction leakage**: 0/10 flagged.
**AI self-reference**: 0/10 flagged.
**QC status**: 10/10 `passed`, 0 flagged, 0 rejected.
**Output length**: ratio (actual/target words) ranged 0.89–1.15, median
1.08 — consistent with EXP-DATA-001's original finding ("full_ai length
control is reasonable").
**Metadata integrity**: all 20 records carry every required field
(`sample_id`, `family_id`, `split`, `source_sample_id`,
`generation_config`, `generation_model`, `generation_model_revision`,
`prompt_template_id`, `target_length_words`, `qc_status`, `qc_notes`,
`instruction_leakage_flagged`, `ai_self_reference_flagged`, `label`,
`transformation_type`, `ground_truth_confidence`, `modified_spans`) —
none missing. `generation_model`/`generation_model_revision`/
`prompt_template_id` are uniform across all 10 `full_ai` records, as
expected for an unchanged mechanism.
**Provenance/family assignment**: every `full_ai` record's `family_id`
matches its seed's `human` record; `source_sample_id` is `None` for
both (correct — a full generation has no specific source span to
reference). `find_family_split_violations()` (new utility, added this
round with regression tests — see below) reports **0 violations**: no
family has members in more than one split. Re-run against all 8
existing experiment data files (EXP-DATA-001 through R4) — **0
violations in every one**.
**Duplicate behavior**: `near_duplicate_pairs_scoped` reports **0
cross-family duplicates and 0 same-family near-duplicate flags** (the
latter is expected to be low/zero for `full_ai`, since it's an
independent generation, not a splice of the human original — unlike
splice-based categories, `full_ai` text is not inherently similar to
its own human seed).
**Topic/prompt adherence** (manual spot-check, all 10): every essay
directly and correctly addresses its own assigned prompt, including
prompt-specific details (e.g., correctly identifies and argues for
"Policy 2" specifically in the cell-phone-policy prompts; correctly
cites "B+ grade average" / "B average" thresholds matching each
prompt's exact wording). No topic drift, no generic/off-prompt output
observed in any of the 10 samples.

## Conclusion

**No substantive regression found.** All 9 checked dimensions
(leakage, self-reference, prompt adherence, topic adherence, output
length, metadata integrity, provenance/family assignment, duplicate
behavior, generation failures) came back clean. The `full_ai` mechanism
was not modified. `find_family_split_violations()` was added as a new,
reusable, tested utility (not a methodology change) to make the
family-split leakage invariant checkable programmatically for this and
future rounds, including the upcoming 150-family construction.

**Per the stop condition: reporting and stopping here for review before
proceeding to 150-family construction.**
