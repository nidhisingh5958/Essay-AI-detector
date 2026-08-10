# DEC-011 — Mixed/AI-Assisted Text Generation Methodology

## Status
Provisional — **partially invalidated by EXP-DATA-001 pilot evidence**
(2026-08-10). The surgical-splice mechanism (sentence/paragraph rewrite)
is confirmed working well. The whole-essay-instruction-plus-diff
mechanism for light/moderate polish is **not working as designed** —
see "Pilot Findings" below. Do not treat the polish-category design in
this record as validated; it needs the revision described there before
further use.

## Date
2026-08-10

## Context

Section 11 of the project brief and this phase's instructions both treat
mixed/AI-polished text as a *core* requirement, not an afterthought: real
essays plausibly involve a human writing a draft and AI touching some
sentences, some paragraphs, or the whole thing lightly — not just a clean
100%-human vs. 100%-AI split. For sentence-level evaluation to mean
anything (Phase 10's sentence-level metrics), each mixed sample needs
**exact, trustworthy** ground truth about which sentences were AI-touched
— not an approximation invented after the fact.

## Problem

For each category of mixed sample (light polish, moderate polish,
single-sentence rewrite, multi-sentence rewrite, single-paragraph
rewrite, multi-paragraph rewrite, heavy revision), how should the
transformation actually be produced, and how should sentence-level ground
truth be derived from it?

## Alternatives Considered

### Alternative A: Whole-essay instruction + post-hoc diff
Send the entire essay to the model with an instruction like "lightly
polish this essay," then diff the before/after text sentence-by-sentence
and label any sentence that changed beyond some similarity threshold as
AI-touched.

Advantages: one simple prompt per sample; no need to pre-select which
sentences/paragraphs to target.

Disadvantages: no control over *how much* actually changes — an
instruction to "lightly" polish is a request, not a guarantee, and a
small instruction-tuned model may over- or under-comply. Ground truth
becomes an approximation dependent on a diff-similarity threshold choice,
which is a second source of label noise stacked on top of the
generation itself.

### Alternative B: Surgical span-level replacement
Pre-select the exact sentence(s) or paragraph(s) to target (using the
same sentence segmenter from [DEC-005](DEC-005-sentence-segmentation.md)),
send only that span plus one sentence of surrounding context to the model
with an instruction to rewrite just that span, then splice the result
back into the essay at the exact original character offsets.

Advantages: ground truth is exact and deterministic by construction — no
diffing, no threshold, no ambiguity about which sentences are AI-touched.
Also gives precise control over "how much" is changed, since that's
determined by how many sentences/paragraphs were selected, not by hoping
the model complies with a vague severity instruction.

Disadvantages: the rewritten span is generated with limited context (only
adjacent sentences, not the full essay), so it may read slightly less
globally coherent than a whole-document-aware rewrite would. Requires
correctly locating sentence/paragraph boundaries before generation, which
depends on the corpus's paragraph structure actually surviving
preprocessing (an open item — see Limitations).

### Alternative C: Hybrid — match the mechanism to what each category is
actually simulating
Use Alternative B (surgical splice) for the categories where exact
localization is the entire point (single/multi-sentence rewrite,
single/multi-paragraph rewrite) — these are meant to simulate "AI touched
*this specific part*," so the generation mechanism should guarantee that.
Use Alternative A (whole-essay instruction + diff) for light polish,
moderate polish, and heavy revision — these are meant to simulate a
pervasive, whole-essay touch that doesn't have a clean boundary in real
life either, so approximating the boundary via diffing is not just an
engineering compromise here, it's actually a more honest model of what
that category represents.

## Decision

**Alternative C.** Concretely:

**Surgical-splice categories** (exact ground truth,
`ground_truth_confidence: "high"`):
- `sentence_rewrite_single`: one sentence selected (word count in a
  sane range, e.g. 8–40 words, to avoid degenerate one-word "sentences"
  from segmentation edge cases), rewritten with one sentence of context
  on each side, spliced back at its exact character offsets.
- `sentence_rewrite_multi`: 2–4 non-adjacent sentences, same mechanism
  applied independently to each.
- `paragraph_rewrite_single` / `paragraph_rewrite_multi`: same mechanism
  at paragraph granularity.

**Whole-essay + diff categories** (approximate ground truth,
`ground_truth_confidence: "approximate"`, validated during QC):
- `light_polish`: instruction constrains the model to grammar/word-choice
  only, explicitly forbidding structural or content changes.
- `moderate_polish`: instruction allows sentence-level rephrasing but not
  reordering or content changes.
- After generation, sentences are aligned by position (segmenting the
  output with the same [DEC-005](DEC-005-sentence-segmentation.md)
  pipeline) and compared to the original; a sentence is labeled AI-touched
  only if it changed beyond a documented similarity threshold. **If
  sentence count or order doesn't match closely enough to align
  confidently, the sample is rejected by quality control (`structure_
  drift`), not silently mislabeled** (see QC in
  [generation-methodology.md](../generation-methodology.md)).

**Essay-level-only category** (`ground_truth_confidence:
"essay_level_only"` — no sentence-level claim made at all):
- `heavy_revision`: instruction asks for substantial rewriting for
  clarity/sophistication while preserving meaning and structure. By
  design this touches most or all sentences, so localizing "which
  sentences are AI" would be meaningless. This category is usable for
  essay-level evaluation only and must be excluded (or specially flagged)
  from sentence-level and passage-level evaluation metrics in Phase 10 —
  documented here so that exclusion isn't forgotten or silently dropped
  later without explanation.

**Full machine generation** (not a "mixed" category, but sharing the same
family/metadata scheme): every sentence is trivially AI-authored,
`ground_truth_confidence: "high"`.

### Leakage invariant (Section 13)

All samples derived from one human seed essay — the original plus every
transformation of it — share one `family_id` (the seed essay's own ID)
and **must** be assigned to the same train/validation/test split. This is
enforced by ordering, not just by convention: **split assignment happens
at the family level, before any generation runs** — a seed essay is first
assigned to a split, and only then are its derived samples generated
"into" that split. Generating first and splitting afterward is exactly
the bug this ordering exists to prevent.

## Why

Matching the ground-truth mechanism to what each category is actually
supposed to represent (surgical splice for "AI touched this specific
part," diff-based approximation for "AI touched the whole thing lightly")
produces trustworthy labels for the categories where sentence-level
evaluation matters most, while being honest that some categories
(`heavy_revision`) cannot support that granularity at all rather than
inventing a false-precision label for them.

## Evidence

**Original (pre-pilot):** None — this was a design decision preceding any
generation code or pilot run.

**EXP-DATA-001 pilot, executed 2026-08-10** (full report:
[reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md)), 10 seed
essays × 6 categories = 60 real samples against the actual acquired
PERSUADE corpus and Qwen2.5-1.5B-Instruct:

- **Surgical-splice categories confirmed working well**: `sentence_
  rewrite_single` passed cleanly for 6/10 (2 more only flagged by a QC
  check bug, not a real problem — see below); `paragraph_rewrite_single`
  passed cleanly for 9/10. The `splice_resegmentation_mismatch` QC check
  (re-segmenting the spliced essay and confirming sentence count is
  unchanged) caught 2 real edge cases correctly, validating that check's
  design.
- **Whole-essay-instruction-plus-diff categories failed at a high rate,
  for a real, substantive reason, not noise**: `light_polish` and
  `moderate_polish` both showed **70% structure_drift** (7/10 families
  each) — manually confirmed as genuine sentence-count-changing
  consolidation by the model, not a segmentation artifact (see
  EXP-DATA-001 §7 for a quoted before/after example). Even among the 3/10
  families per category that *did* align, similarity ratios were
  continuous/spread (0.07–0.85 for light, 0.09–0.97 for moderate) with no
  visible separation between "touched" and "untouched" sentences — no
  pair scored a perfect 1.0 in light_polish. **This pilot found no
  evidence a numeric similarity threshold would be meaningful for this
  category as currently designed** — the assumption that "light polish"
  produces a recoverable mix of touched/untouched sentences did not hold.
- Length control also failed for these two categories specifically
  (light_polish ranged 100–380 words against ~250-word seeds;
  moderate_polish consistently undershot, median 156.5) — a related but
  separate problem from the alignment failure.
- A QC implementation bug was found and diagnosed (not a generation
  problem): `check_prompt_leakage` compared against the *entire*
  instruction, including the embedded essay prompt — essays legitimately
  referencing their own prompt's wording triggered false positives on all
  3 `full_ai` samples it flagged. Confirmed via a corrected re-check.
- Zero near-duplicate samples found; zero metadata-schema violations;
  zero leakage-invariant violations (checked programmatically, not just
  assumed from the split-before-generation ordering).

Per this pilot's explicit instructions, **no threshold was invented to
paper over the structure_drift/diff findings** — the recommended fix
(below) is a mechanism change, not a parameter tune.

## Trade-offs

The surgical-splice categories may read as slightly less globally
coherent than a full-document-aware rewrite, in exchange for ground truth
that requires no threshold, no diffing, and no ambiguity.

## Consequences

Positive:
- Every mixed sample carries ground truth whose confidence level is
  explicitly labeled, rather than a single undifferentiated "mixed"
  bucket.
- Sentence-level evaluation (Phase 10) can be scoped correctly per
  category instead of over-claiming precision the data doesn't support.

Negative:
- More implementation complexity than one uniform mechanism for every
  category (two different generation code paths: splice-based and
  diff-based).
- The diff-based categories' similarity threshold is a real, if narrow,
  arbitrary-seeming parameter — must be chosen from pilot evidence
  (EXP-DATA-001) and documented when fixed, not guessed and left
  unexamined.

## Revisit When

1. ~~EXP-DATA-001 pilot provides real examples to set the diff-similarity
   threshold~~ — **done, 2026-08-10: the pilot found no basis for setting
   one** (see Evidence). What needs revisiting instead, before any further
   generation:
   - **Replace the exact-count-match alignment rule** with a proper
     sequence-alignment algorithm (`difflib.SequenceMatcher` operating on
     the sentence *list*, using `get_opcodes()` to find equal/replace/
     insert/delete blocks) instead of requiring identical sentence counts.
     This should recover usable, if block-level rather than strictly 1:1,
     ground truth for most of the currently-rejected 70%, instead of
     discarding them outright. **Proposed, not implemented** — implementing
     and re-piloting this is explicitly out of scope for the point this
     decision was updated at (EXP-DATA-001's stop condition).
   - **Add a dedicated length-control mechanism** for `light_polish`/
     `moderate_polish` (they currently reuse `full_ai`'s token budgeting,
     which doesn't fit their "stay close to original length" goal).
   - **Fix `check_prompt_leakage`** to exclude prompt/target-text content
     from its comparison (an implementation bug, not a methodology
     question — see Evidence).
   - **After** those fixes, run a small follow-up pilot on just the
     polish categories before deciding whether the model itself
     (escalating to Phi-3.5-mini-instruct, DEC-010) also needs to change
     — test the methodology fix and the model change one at a time, not
     together, so it's clear which one (if either) actually helped.
2. If paragraph boundaries turn out not to survive in the acquired
   corpus's raw text — **resolved, 2026-08-10: they do, in ~95% of
   essays** (see DEC-009's inspection update and
   [reports/dataset-inspection.md](../../reports/dataset-inspection.md)).
   The surgical paragraph-rewrite mechanism using `\n\n` boundaries is
   confirmed working (9/10 passed in the pilot).

## Implementation

`scripts/run_exp_data_001.py` (pilot orchestrator), `scripts/generation_utils.py`
(pure logic: `align_and_diff_sentences`, `pick_rewrite_sentence_index`,
`pick_rewrite_paragraph_index`, QC checks), `scripts/qwen_generate.py`
(model wrapper). The full-scale versions
(`scripts/generate_samples.py`, `scripts/generate_mixed_samples.py`) do
not exist yet and should incorporate the alignment-algorithm and
length-control fixes above before being written, not before.

## Tests / Experiments

`scripts/tests/test_generation_utils.py` (19 tests, pure-logic fixtures).
`EXP-DATA-001` — **executed 2026-08-10**, 60 real samples. Full results:
[reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md). Design doc:
`experiments/EXP-DATA-001-generation-pilot/README.md`.
