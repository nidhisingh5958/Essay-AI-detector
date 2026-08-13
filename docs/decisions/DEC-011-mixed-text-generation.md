# DEC-011 — Mixed/AI-Assisted Text Generation Methodology

## Status
Provisional — **partially invalidated by EXP-DATA-001 pilot evidence**
(2026-08-10), **redesigned** the same day (see "Post-Pilot Methodology
Redesign" below), redesign **targeted-validated by EXP-DATA-001-R1**
(2026-08-10, 18 records — small, explicitly-scoped follow-up, not a full
pilot re-run; see [reports/EXP-DATA-001-R1.md](../../reports/EXP-DATA-001-R1.md)).

**R1 results:** Regime A/B (surgical splice, including the new
controlled-span light/moderate categories) — 3/3, 3/3, 2/3, 2/3 passed
respectively; the controlled-span mechanism's length control looked
**dramatically better** at the single-sentence-span level (e.g. 12/12,
17/17 words, target vs. actual) than the old whole-essay approach ever
achieved, though n=3 per new category is too small to call this
validated at scale — it's promising, not proven. One real failure was
caught correctly (`modification_scope_drift` + `splice_resegmentation_mismatch`),
not silently passed. **Regime C (`light_polish`) behaved exactly as
redesigned**: all 3 samples got `ground_truth_confidence:
"essay_level_only"` and `modified_spans: None` unconditionally, and 2/3
showing `structure_drift_observed` were correctly *not* rejected for it.
Zero instruction-leakage/AI-self-reference false positives observed
(consistent with the QC fix, though R1 did not re-exercise `full_ai`
specifically). One new, minor methodology gap found: the near-duplicate
check needs to be scoped per-category (flagged a splice-based variant as
"near-duplicate" of its own human original, which is expected given the
mechanism, not a real problem — not yet fixed in code).

The surgical-splice mechanism (sentence/paragraph rewrite) is confirmed
working well and unchanged. The original whole-essay-instruction-plus-diff
mechanism for light/moderate polish is **abandoned as a sentence-level
ground-truth source** — replaced by the controlled-span mechanism (Regime
A/B, same family as surgical splice, different instruction intensity).
Whole-essay polish is retained only as an essay-level-only category
(Regime C).

**Confirmation round (EXP-DATA-001-R1-confirmation, 2026-08-10, 50
records, 10 NEW previously-unseen seeds, sentence AND paragraph
light/moderate categories — see
[reports/EXP-DATA-001-R1-confirmation.md](../../reports/EXP-DATA-001-R1-confirmation.md)
for full results):** requested specifically to check whether R1's n=3
finding held at scale. **Split verdict, not a uniform pass:**

- **Paragraph-level controlled transformation: close to validated.**
  19/20 passed QC cleanly, 0 resegmentation failures, 18/20 judged
  `semantic_preservation: "preserved"` on manual review, 0
  instruction-leakage/self-reference flags, 0 cross-family duplicates
  (34 same-family matches correctly *not* flagged, validating this
  round's near-duplicate scoping fix in practice).
- **Sentence-level controlled transformation: NOT validated, real problem
  found.** Only 12/20 passed QC cleanly, and — critically — **manual
  semantic-preservation review found automated QC (length ratio +
  resegmentation) does not catch semantic drift**: 4 samples that passed
  every automated check were still judged `"changed"` on meaning (e.g. a
  factual detail altered from "one C" to "two Cs"; a specific grievance
  replaced by a generic sentence with no equivalent claim). Combined
  across both sentence categories: only 5/15 reviewed samples (33%) were
  judged `"preserved"`; 7/15 (47%) were `"changed"`.
- **Unexplained pattern, flagged not resolved:** at the sentence level,
  `light` instructions produced *more* scope drift and rejections than
  `moderate` ones — the opposite of what the category names suggest.
  Temperature also differed between the two (0.5 vs 0.7), so this
  experiment cannot isolate whether wording or temperature (or both)
  caused it.

**Status stays Provisional — this is not a status upgrade, it's a
refined, mixed finding.** Per the explicit instruction not to define
success as "all samples passed" and not to mark this Accepted
automatically: the real question — "does controlled-span generation
produce sufficiently reliable, interpretable ground truth across
previously unseen essays?" — now has an evidenced answer that's
**category-specific**: yes for paragraph-level (with semantic review kept
as an ongoing spot-check, since even paragraph-level had one real
semantic failure), not yet for sentence-level.

**Recommendation (from the confirmation report): B — promising but
requires another revision, not ready for scale as a uniform mechanism.**
Sentence-level needs one of: (a) a second automated signal beyond length/
resegmentation that can catch semantic drift, (b) mandatory semantic
review as a non-optional gate for this category, or (c) more surrounding
context per edit, before being trusted at scale. Paragraph-level can
reasonably proceed to a larger validation round on its own.

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

**Alternative C, as originally adopted, then redesigned post-pilot** (see
"Post-Pilot Methodology Redesign" below for the full reasoning). The
**current** decision organizes every mixed category into exactly one of
three ground-truth regimes:

### Regime A — Surgical sentence-level transformation
Exact ground truth, `ground_truth_confidence: "high"`. One sentence
selected (word count in a sane range, e.g. 8–40 words, to avoid
degenerate one-word "sentences" from segmentation edge cases), sent with
one sentence of context on each side, and spliced back at its exact
character offsets. The **instruction intensity is a parameter of this
same mechanism**, not a different one:
- `sentence_rewrite_single` — full rewrite instruction (original design,
  validated in EXP-DATA-001).
- `sentence_light_controlled` / `sentence_moderate_controlled` — same
  splice mechanism, lighter/more constrained instruction wording
  (post-pilot addition — see redesign section; validated at small scale
  in EXP-DATA-001-R1).
- `sentence_rewrite_multi`: 2–4 non-adjacent sentences, same mechanism
  applied independently to each (not yet exercised in any pilot).

### Regime B — Surgical paragraph-level transformation
Exact ground truth, `ground_truth_confidence: "high"`. Same mechanism as
Regime A at paragraph granularity (`\n\n`-delimited spans, confirmed
surviving in ~95% of both acquired corpora — DEC-009).
- `paragraph_rewrite_single` (validated in EXP-DATA-001).
- `paragraph_rewrite_multi` (not yet exercised).

### Regime C — Whole-essay transformation
**Essay-level-only ground truth, `ground_truth_confidence:
"essay_level_only"` — no sentence-level claim is made, ever, for this
regime.** Covers `light_polish`, `moderate_polish`, and `heavy_revision`.
By design (and confirmed empirically — see Evidence) these can touch most
or all sentences and may restructure/consolidate them, so localizing
"which sentences are AI" is not meaningful. Sentence-diff/alignment MAY
be computed for these categories, but **strictly as a diagnostic**
(detecting gross structural drift, logging an observed similarity range
for documentation) — **never** to derive a `modified_spans` label. This
regime's samples must be excluded from sentence-level and passage-level
evaluation metrics in Phase 10 — documented here so that exclusion isn't
forgotten or silently dropped later.

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

## Post-Pilot Methodology Redesign (2026-08-10)

This section exists so the failure is legible on its own, not just
implied by a status change:

- **Observed similarity range:** light_polish 0.07–0.85 (24 pairs across
  the 3 families that aligned); moderate_polish 0.09–0.97 (38 pairs
  across 3 families). No pair in light_polish scored a perfect 1.0 —
  i.e. even the sentences the pipeline could compare found *no* sentence
  the model left completely untouched.
- **No naturally separable threshold:** both distributions are
  continuous/spread, not bimodal. There is no visible gap between
  "lightly touched" and "heavily touched" sentences to place a cutoff at.
  Picking a number anyway (e.g. "0.5") would be exactly the kind of
  invented, unjustified threshold this project's discipline forbids.
- **Sentence consolidation, not segmenter noise:** manually confirmed
  (EXP-DATA-001 §7) — the model merges multiple original sentences into
  fewer, more fluent ones even when explicitly instructed not to change
  sentence count. This is a real property of how the model "polishes,"
  not a bug in `sentence_segmenter.py`.
- **Structural drift:** 70% of families (7/10) in both `light_polish` and
  `moderate_polish` failed the exact-count alignment check entirely.
- **Ambiguity of sentence-level attribution:** even setting the alignment
  problem aside, the *concept* of "this specific original sentence maps
  to that specific output sentence" breaks down once sentences are
  merged/split/reordered — there may be no single correct answer to
  "which output sentence corresponds to original sentence 3," making any
  forced 1:1 label an artifact of the alignment algorithm rather than a
  fact about the generation. This is a conceptual limit, not something a
  better algorithm fully resolves.

**Decision: do not attempt to rescue whole-essay polish as a
sentence-level ground-truth source at all** — not via a threshold, and
not via a more sophisticated alignment algorithm either (see next
subsection for why `difflib`/sequence-alignment specifically was
considered and rejected *for this purpose*, though retained for
diagnostics). Instead:

1. **Whole-essay polish becomes Regime C** (essay-level-only ground
   truth, no sentence-level claim) — see the redesigned Decision section
   above.
2. **A new mechanism produces sentence-level light/moderate examples
   instead: controlled-span transformation.** Apply the *same* surgical
   splice mechanism already validated for `sentence_rewrite_single`/
   `paragraph_rewrite_single` (Regimes A/B), but with a light- or
   moderate-intensity instruction instead of a full-rewrite instruction.
   Because the transformation is still applied to one pre-selected,
   known span and spliced back at exact offsets, ground truth remains
   exact regardless of how "light" or "moderate" the wording asks the
   model to be — the *instruction intensity* varies, the *mechanism*
   (and its ground-truth guarantee) does not.

### Alternatives considered for the redesign specifically

**Alternative D: Keep whole-essay diffing, but replace exact-count
matching with `difflib.SequenceMatcher`-based sequence alignment
(`get_opcodes()`) to recover partial ground truth from the 70%
currently rejected.**
Advantages: could recover some labeled data from families that currently
produce nothing; handles merges/splits more gracefully than exact-count
matching.
Disadvantages: **this still tries to manufacture sentence-level labels
from an inherently ambiguous transformation** (see "ambiguity of
sentence-level attribution" above) — a `replace` opcode spanning 2
original sentences and 1 output sentence doesn't tell you which *part*
of the output sentence came from which original sentence, if that
question even has an answer. Explicitly rejected for producing training/
evaluation labels, **not** rejected as a tool — see next paragraph.

**Alternative E (chosen): use `difflib`/alignment as a diagnostic only;
produce sentence-level ground truth exclusively through the mechanism
that already guarantees it (controlled-span splicing, Regimes A/B).**
Advantages: never confuses "we can compute *a* diff" with "we know the
ground truth" — the diagnostic use (detecting gross structural drift,
reporting an observed similarity range in documentation) is exactly what
`align_and_diff_sentences` is good for and was actually used for in
EXP-DATA-001's report. Producing actual labeled sentence-level mixed
samples goes through Regime A/B instead, where the guarantee is
structural (we chose the span), not statistical (we measured a
similarity score).
Disadvantages: whole-essay-level "AI touched this essay somewhat, in a
way that isn't localized" scenarios are no longer represented by a
sentence-level-labeled example at all — only by a Regime C essay-level
example. This is an honest limitation, not a gap to paper over: the
project's dataset does not claim to have sentence-level ground truth for
that realistic scenario, because no mechanism tested so far can produce
it trustworthily.

**Decision: Alternative E.** `difflib.SequenceMatcher` remains available
in `generation_utils.align_and_diff_sentences` and continues to be used
exactly as it was in EXP-DATA-001 §7 — as an inspection/diagnostic tool
(structural-drift detection, documented similarity ranges) — but its
output is never again written into a `modified_spans` field.

## QC Additions From the Confirmation Round (2026-08-10)

Three QC mechanisms were added or fixed while preparing
EXP-DATA-001-R1-confirmation, each addressing a real gap found in
existing code/data, not speculative hardening:

**Near-duplicate scoping (family-aware).** Previously, `near_duplicate_pairs`
compared every text against every other text with no notion of "family."
EXP-DATA-001-R1 found this flags a splice-based variant as a "duplicate"
of its own human original — expected given the mechanism, not a real
anomaly. `near_duplicate_pairs_scoped` now separates `cross_family`
(the real detection target — two *different* seed essays producing
suspiciously similar output) from `same_family` (informational,
never treated as suspicious). Validated in the confirmation round: 0
cross-family flags, 34 same-family matches correctly not flagged.

**`SequenceMatcher` `autojunk` bug.** Found while building the scoped
duplicate check: Python's `difflib.SequenceMatcher` defaults to
`autojunk=True`, which materially understates similarity for text over
~200 characters (observed: a single-word change in a ~200-character
sentence scored ~0.28 instead of ~0.97). Fixed with `autojunk=False` in
both `near_duplicate_pairs_scoped` and `align_and_diff_sentences` — the
latter is a correction to code EXP-DATA-001 already used, meaning that
pilot's reported Regime C similarity range (0.07–0.97, no separable
threshold) was computed with the buggy default. **This is not
re-litigated here**: EXP-DATA-001's *structural* finding (70%
sentence-count mismatch) is completely unaffected by this bug (it's a
count comparison, not a similarity score), and Regime C's redesign
(essay-level-only, no threshold) doesn't depend on the exact similarity
numbers being right — but the specific range figures quoted from
EXP-DATA-001 should be read as approximate, not exact, going forward.

**`semantic_preservation` field.** Added per explicit instruction: a
provenance/QC field (`not_yet_reviewed` / `preserved` / `questionable` /
`changed`) tracking whether a controlled rewrite preserved the source's
underlying meaning and claims, independent of structural QC. **Assigned
by manual human review only — never by a model call within this
pipeline** (that would be exactly the LLM-as-ground-truth-judge pattern
DEC-004 rules out elsewhere). `scripts/apply_semantic_review.py` performs
the mechanical merge of a hand-written review into a samples file; it
does not generate the review itself. **This field turned out to be the
single most important addition in the confirmation round**: it found 4
samples that passed every automated check (length ratio, resegmentation)
while still changing the essay's actual meaning — evidence that
structural QC alone is insufficient for the sentence-level categories,
which motivated the "not ready for scale" verdict for that regime (see
below).

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
   one.**
2. ~~Replace the exact-count-match alignment rule with a proper
   sequence-alignment algorithm to recover partial sentence-level ground
   truth from whole-essay diffs~~ — **superseded, 2026-08-10: rejected
   for this purpose after further consideration** (see "Post-Pilot
   Methodology Redesign," Alternatives D/E) — sequence alignment doesn't
   resolve the underlying ambiguity of attribution once sentences are
   merged/split, it just produces a more sophisticated-looking guess.
   Replaced by the controlled-span redesign instead.
3. ~~Fix `check_instruction_leakage`'s scope~~ (formerly
   `check_prompt_leakage`) — **done, 2026-08-10**: now takes a
   meta-instruction-only argument; regression test preserved in
   `scripts/tests/test_generation_utils.py`.
4. ~~Run a small follow-up pilot on just the polish categories~~ — **done,
   2026-08-10: EXP-DATA-001-R1**, see
   [reports/EXP-DATA-001-R1.md](../../reports/EXP-DATA-001-R1.md) for
   results and whether the redesign holds up.
5. ~~Dedicated length-control mechanism for the controlled-span light/
   moderate categories~~ — **confirmed at scale for paragraph-level,
   2026-08-10**: `modification_scope_drift` combined with the tighter
   paragraph-level ratio distribution (§4 of the confirmation report)
   shows span-level length control works well for paragraphs. **Still
   open for sentence-level**: wider, less predictable ratio distribution
   (0.41–2.68) with `light` performing worse than `moderate` for reasons
   this experiment couldn't isolate (§10 of the confirmation report).
6. ~~Near-duplicate check needs per-category scoping~~ — **done,
   2026-08-10**: `near_duplicate_pairs_scoped` (family-aware), 5
   regression tests, validated in the confirmation round (0 cross-family
   false positives, 34 same-family matches correctly not flagged). See
   "QC Additions From the Confirmation Round" above.
7. Still open: whether the model itself (escalating to
   Phi-3.5-mini-instruct, DEC-010) needs to change for the sentence-level
   categories specifically, now that the *methodology* gap there
   (semantic drift undetected by structural QC) is understood rather
   than being confounded with a model-quality question.
8. Still open: **`full_ai` still hasn't been re-exercised** with the
   fixed `check_instruction_leakage` in a live run (the confirmation
   round didn't include `full_ai`, by design — it was scoped to the
   controlled-span categories only). Worth checking in any future run
   that includes `full_ai`.
9. ~~Paragraph boundaries might not survive in the acquired corpus~~ —
   resolved (DEC-009). Confirmed compatible with the controlled-span
   mechanism specifically: 0 resegmentation failures across 20 paragraph
   attempts in the confirmation round.
10. **New, from the confirmation round**: sentence-level controlled
    transformation needs one of — (a) a second automated signal beyond
    length/resegmentation that can catch semantic drift, (b) mandatory
    semantic review as a non-optional gate, or (c) more surrounding
    context per edit — before being trusted at scale. Not yet
    implemented; a design/alternatives comparison for whichever path is
    chosen belongs in a future DEC-011 revision, not decided here.

## Implementation

`scripts/run_exp_data_001.py` (original pilot orchestrator, patched
post-pilot for the QC fix, Regime C reclassification, and the generic
`generate_sentence_transform`/`generate_paragraph_transform` refactor —
not re-run in full), `scripts/run_exp_data_001_r1.py` (targeted
validation of the controlled-span redesign, n=3),
`scripts/run_exp_data_001_r1_confirmation.py` (larger-scale confirmation,
n=10, resumable — see script docstring re: session-interruption
resilience), `scripts/generation_utils.py` (pure logic:
`align_and_diff_sentences` — diagnostic-only, `autojunk=False` fix,
`check_instruction_leakage`, `check_ai_self_reference`,
`near_duplicate_pairs_scoped`, `validate_semantic_preservation`,
`pick_rewrite_sentence_index`, `pick_rewrite_paragraph_index`, other QC
checks), `scripts/qwen_generate.py` (model wrapper),
`scripts/apply_semantic_review.py` (mechanical merge of manual review
into a samples file). The full-scale versions
(`scripts/generate_samples.py`, `scripts/generate_mixed_samples.py`)
still do not exist and should follow the three-regime structure above —
with the sentence-level caveat from the confirmation round factored in —
when written.

## Tests / Experiments

`scripts/tests/test_generation_utils.py` (pure-logic fixtures: 5
instruction-leakage scenarios + regression test, 5 near-duplicate-scoping
scenarios, an `autojunk` regression test, semantic-preservation validator
tests). `scripts/tests/test_apply_semantic_review.py`. `EXP-DATA-001` —
executed 2026-08-10, 60 real samples:
[reports/EXP-DATA-001.md](../../reports/EXP-DATA-001.md) (preserved,
not erased). `EXP-DATA-001-R1` — targeted redesign-validation, n=3,
executed 2026-08-10:
[reports/EXP-DATA-001-R1.md](../../reports/EXP-DATA-001-R1.md).
`EXP-DATA-001-R1-confirmation` — larger-scale check, n=10 (50 records),
executed 2026-08-10:
[reports/EXP-DATA-001-R1-confirmation.md](../../reports/EXP-DATA-001-R1-confirmation.md).
Design doc: `experiments/EXP-DATA-001-generation-pilot/README.md`.
