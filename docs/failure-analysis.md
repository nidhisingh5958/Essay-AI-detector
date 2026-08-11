# Failure Analysis

This document has two parts, kept explicitly separate so neither is
mistaken for the other:

1. **Data generation pipeline failures** (below) — real, already found
   during EXP-DATA-001. These are failures of the *dataset construction*
   process, not the detector.
2. **Detector failures** (Phase 11, still a placeholder) — no detector
   exists yet, so this part remains empty until one does.

---

## Part 1: Data Generation Pipeline Failures (EXP-DATA-001, 2026-08-10)

Preserved here per explicit instruction not to erase or minimize them.
Full context: [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md),
[DEC-011](decisions/DEC-011-mixed-text-generation.md).

### Failure 1: Whole-essay light/moderate polish does not produce reliable sentence-level ground truth

**What was attempted:** send a whole human essay to Qwen2.5-1.5B-Instruct
with an instruction to lightly or moderately polish it, then diff the
before/after sentences to label which ones the model touched.

**What happened:** 70% of families (7/10) in both `light_polish` and
`moderate_polish` failed an exact-sentence-count alignment check —
manually confirmed as genuine sentence consolidation by the model (it
merges sentences despite explicit instructions not to), not a
segmentation bug. Among the 30% that did align, similarity scores were
continuous across the full range (0.07–0.97) with no separation between
"touched" and "untouched" sentences — no sentence in `light_polish`
scored a perfect match even where alignment succeeded.

**Why it failed:** the underlying assumption — that a "light polish"
instruction produces a *recoverable mix* of touched and untouched
sentences — does not hold for this model at this instruction wording.
This is a property of how the model edits, not a measurement problem
solvable with a better threshold or a smarter alignment algorithm (a
sequence-alignment-based fix was considered and specifically rejected for
this reason — see DEC-011).

**What changed as a result:** whole-essay polish was reclassified as
essay-level-only ground truth (Regime C) and is never used for
sentence-level claims. A new controlled-span mechanism (apply light/
moderate instructions to a single pre-selected sentence, then splice)
replaced it as the source of sentence-level light/moderate examples —
targeted-validated in EXP-DATA-001-R1
([report](../reports/EXP-DATA-001-R1.md)).

### Failure 2: Prompt-leakage QC check flagged legitimate on-topic essays

**What was attempted:** detect generation failures where the model
echoes its own instructions instead of producing real content, by
checking for 6-word overlaps between the instruction and the output.

**What happened:** all 3 `full_ai` samples this check flagged were false
positives. The overlapping phrases came from the *essay prompt* embedded
in the instruction (e.g. "...bring their phones to school and use
them...") — the essay was legitimately discussing the policy it was
asked to write about.

**Why it failed:** the check compared against the *entire* formatted
instruction, including prompt/target content the output is *expected* to
reference, rather than only the instructional meta-language.

**What changed as a result:** `check_prompt_leakage` was replaced with
`check_instruction_leakage`, which requires callers to pass only the
meta-instructional wrapper text. A regression test preserves the
original failure case in `scripts/tests/test_generation_utils.py` so it
cannot silently reappear.

### Failure 3 (a correctly-caught edge case, not a bug): resegmentation mismatch after sentence splicing

**What was attempted:** splice a rewritten sentence into an essay at
exact character offsets, then re-segment the spliced essay to confirm
the sentence count is unchanged (a safety check on the surgical-splice
mechanism's ground-truth guarantee).

**What happened:** 2 of 10 `sentence_rewrite_single` samples failed this
check — the original essay's informal, run-on punctuation style caused
the parser to find a different sentence boundary after the rewritten
(more standard-punctuation) sentence was spliced in.

**Why this is listed as a "failure" but not a bug:** the QC check did
exactly what it was designed to do — catch a case where `modified_spans`
would otherwise have pointed at the wrong sentence index — and rejected
the sample rather than silently producing incorrect ground truth. Listed
here as evidence the safety mechanism works, and as a reminder that
informal/non-standard punctuation in real student writing is a genuine
source of segmentation disagreement worth being aware of elsewhere in the
pipeline (e.g. Phase 3 feature extraction).

---

## Part 2: Detector Failures

> Status: not started. There is no trained/calibrated detector yet to
> produce failures from (see [project-status.md](project-status.md)).
> This part remains a placeholder for the required structure (Section
> 15/39) — it will be populated with at least three real,
> confidently-wrong examples once evaluation (Phase 10) has actually run,
> never with invented ones.

### Required structure per failure case (Phase 11)

For each of at least three essays the detector confidently gets wrong:

1. The essay/passage sample
2. Ground truth label
3. The system's prediction and stated confidence
4. The actual feature values that drove the (wrong) prediction
5. An analysis of why the detector likely failed — tied to specific
   feature behavior, not speculation
6. A concrete idea for how the system could improve, ideally phrased as a
   testable follow-up experiment

### Ground rule

These cases will not be hidden or cherry-picked to look better than they
are (Section 15: "Do not hide these examples"). The purpose of this
section is to demonstrate understanding of the system's real failure
modes, which is only possible once the system exists and has been run
against held-out data.
