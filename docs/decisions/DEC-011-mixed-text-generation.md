# DEC-011 — Mixed/AI-Assisted Text Generation Methodology

## Status
Provisional

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

None yet — this is a design decision preceding any generation code or
pilot run. The similarity threshold for the diff-based categories and the
sentence-count-alignment tolerance for rejecting `structure_drift` samples
are **not yet numerically fixed**; they are exactly the kind of thing
EXP-DATA-001's pilot should surface real examples for, rather than picking
a number now with no data to check it against.

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

1. EXP-DATA-001 pilot provides real examples to set the diff-similarity
   threshold and the structure-drift rejection tolerance numerically.
2. If paragraph boundaries turn out not to survive in the acquired
   corpus's raw text (open item, see Limitations) — the paragraph-level
   categories would need to fall back to a different definition of
   "paragraph" (e.g. a fixed sentence-count window) or be dropped, and
   this record updated accordingly.

## Implementation

Not yet — no generation/splicing code has been written. Precedes
`scripts/generate_mixed_samples.py` (not yet created). Full mechanism
description in [generation-methodology.md](../generation-methodology.md).

## Tests / Experiments

None yet. `experiments/EXP-DATA-001-generation-pilot/` (design only, not
run).
