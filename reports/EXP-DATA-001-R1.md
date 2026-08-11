# EXP-DATA-001-R1 — Generation Methodology Revision Check: Results

> Status: **executed for real**, 2026-08-10. NOT a new full pilot — a
> small, targeted validation (18 records) that the DEC-011 redesign
> (three ground-truth regimes; controlled-span light/moderate
> transformation; the `check_instruction_leakage` fix) behaves as
> intended, following EXP-DATA-001's findings. This report evaluates the
> **data generation pipeline only** — no detector accuracy/F1 is
> reported or implied. Raw output:
> `data/generated/EXP-DATA-001-R1/samples.jsonl` and `diffs.json`
> (gitignored). Prior findings this revision responds to:
> [reports/EXP-DATA-001.md](EXP-DATA-001.md) (preserved, not overwritten).

## What changed and why

Three changes, all made *before* this run, per DEC-011's "Post-Pilot
Methodology Redesign":

1. **QC leakage check fixed.** `check_prompt_leakage` (compared against
   the whole formatted instruction, including embedded prompt/target
   content) → `check_instruction_leakage` (compared only against
   meta-instructional wrapper text) + new `check_ai_self_reference`
   (searches anywhere in text, not just as a preamble). Regression test
   preserved in `scripts/tests/test_generation_utils.py`.
2. **Whole-essay polish reclassified as Regime C** (essay-level-only
   ground truth). `modified_spans` is always `None`; sentence-diffing is
   computed only as a diagnostic (logged to `diffs.json`), never used to
   produce a label. Structural drift is now an informative QC note, not
   a rejection reason — the essay-level claim holds regardless.
3. **New controlled-span mechanism for sentence-level light/moderate
   examples**: the same surgical-splice mechanism already validated for
   `sentence_rewrite_single` (Regime A), applied with a light-copy-edit
   or moderate-reword instruction instead of a full-rewrite instruction.
   Ground truth stays exact because the mechanism (splice a
   pre-selected, known span) is unchanged — only instruction wording
   varies. New: a **modification-scope check** validates the output's
   length ratio against a category-specific documented range (light:
   0.7–1.3x; moderate: 0.5–1.8x; full rewrite: 0.3–3.0x), flagging
   drift rather than assuming compliance.

## Sample set (as run)

3 seed essays (distinct from EXP-DATA-001's 10 — `rng_seed` offset by 1
specifically to avoid overlap), × 6 categories (human + 5 generated) = 18
records:

| Seed ID | Words | Split |
|---|---|---|
| 0C7EC7D3A247 | 252 | test |
| 8D13461BD81C | 227 | train |
| 9EE956923B33 | 277 | train |

Family split assigned before generation, as always — **verified
programmatically: zero family/split violations** across all 18 records.

## Results by category

| Category | Regime | passed | flagged | rejected |
|---|---|---|---|---|
| human (original) | — | 3 | 0 | 0 |
| sentence_rewrite_single | A | 3 | 0 | 0 |
| paragraph_rewrite_single | B | 3 | 0 | 0 |
| sentence_light_controlled | A (new) | 2 | 0 | 1 |
| sentence_moderate_controlled | A (new) | 2 | 0 | 1 |
| light_polish | C (reclassified) | 1 | 2 | 0 |

**Zero `instruction_leakage` or `ai_self_reference` flags across all 18
records** — consistent with the QC fix (no false positives observed;
this small sample can't prove the bug is gone everywhere, but it's
consistent with the fix working as intended).

### Regime A/B (unchanged categories): stable, as in EXP-DATA-001

`sentence_rewrite_single` and `paragraph_rewrite_single` both passed
3/3 cleanly — consistent with EXP-DATA-001's 6/10 and 9/10 (this run's
smaller sample happened to hit no edge cases, not evidence of a higher
true pass rate than the original pilot found).

### Controlled-span light/moderate: length control works dramatically
better at the span level than at the whole-essay level

For the samples that passed, actual length matched the target sentence's
length closely:

| Sample | Target words | Actual words |
|---|---|---|
| 8D13461BD81C light | 12 | 12 (exact) |
| 9EE956923B33 light | 32 | 31 |
| 0C7EC7D3A247 moderate | 17 | 17 (exact) |
| 8D13461BD81C moderate | 12 | 8 |

Compare this to EXP-DATA-001's whole-essay `light_polish` results (100–380
words against ~250-word seeds — wildly uncontrolled). **This is the
strongest finding of this validation run: constraining the transformation
to a single known span, rather than a whole essay, appears to make length
control tractable** — though n=3 per category is far too small to
generalize beyond "this looks promising, worth testing at real pilot
scale."

**One real failure, correctly caught, not silently passed:**
`0C7EC7D3A247__sentence_light_controlled` was rejected with
`modification_scope_drift(ratio=2.71, expected=[0.7,1.3])` — despite a
light-copy-edit instruction, the model produced a rewrite ~2.7x longer
than the target sentence (roughly 46 words instead of 17). The new
modification-scope check caught this instead of accepting a "light" edit
that was actually a substantial rewrite. This sample was also flagged for
`splice_resegmentation_mismatch`, compounding the rejection.

### Regime C (`light_polish`, reclassified): behaves exactly as redesigned

All 3 samples show `ground_truth_confidence: "essay_level_only"` and
`modified_spans: None` **unconditionally** — including the 2 that showed
`structure_drift_observed`. Critically, **neither was rejected for
structural drift** — confirming the redesign's intent: an essay-level
claim ("this essay was AI-polished") doesn't depend on how much internal
restructuring occurred, so drift is now informative metadata, not a
disqualifying failure. This is the behavior change EXP-DATA-001-R1 was
specifically built to verify.

## Sentence-level provenance validation

- All `modified_spans` produced (for passing Regime A samples) correctly
  slice the final spliced text at valid offsets — spot-checked directly
  by extracting the exact rewritten-sentence substring for every passing
  controlled-category sample (see examples below).
- `splice_resegmentation_mismatch` fired twice (once combined with
  `modification_scope_drift`, once alone) and both were correctly
  rejected rather than silently mislabeled — the safety check continues
  to work as intended, unconditionally, as instructed.

## Metadata validation

All 18 records contain every required schema field — checked
programmatically, zero missing fields.

## Examples

**Successful light-controlled edit** (`8D13461BD81C`, target 12 words,
actual 12): rewritten sentence — *"They will learn how to not abuse it
and obey the rules."* Reads as a genuine light edit, not a rewrite.

**Successful moderate-controlled edit** (`0C7EC7D3A247`, target 17 words,
actual 17): *"Texting while driving significantly increases the risk of
major accidents, leading to hefty fines up to $400."* Reworded, meaning
preserved, appropriately more substantial than the light example.

**Failed light-controlled edit** (`0C7EC7D3A247`, rejected): the model
produced a multi-sentence, ~46-word expansion instead of an ~17-word
light edit — instruction wording alone did not guarantee compliance,
consistent with EXP-DATA-001's original length-control finding (Section
15 there) now recurring at the span level, just far less often (1 of 6
controlled-category attempts vs. pervasive whole-essay drift).

## A secondary finding: near-duplicate check needs scoping

The pairwise near-duplicate heuristic
(`generation_utils.near_duplicate_pairs`) flagged
`8D13461BD81C__human` and `8D13461BD81C__sentence_light_controlled` as
near-duplicates. **This is expected, not a bug**: a single-sentence
surgical edit produces an essay that's necessarily almost identical to
its human original by design. The check was built for catching
independent `full_ai` generations that happen to converge on similar
text, not for comparing a splice-based variant against its own source.
**Recommendation:** scope near-duplicate checks to compare only within
the same `transformation_type`/`label` (e.g. `full_ai` vs `full_ai`), not
indiscriminately across an entire family. Not fixed in this run — noted
for the next code pass.

## Is the redesign ready for scale?

**Partially — with specific caveats, not a blanket yes.**

- **Regime A/B (surgical splice, including the new controlled-span
  categories): promising.** Length control at the span level looks much
  more tractable than at the whole-essay level. But n=3 per new category
  is too small to be confident — the one real failure
  (`modification_scope_drift` + `resegmentation_mismatch` together)
  shows the failure mode from EXP-DATA-001 (uncontrolled length) can
  still occur, just less often. A larger run (comparable scale to the
  original EXP-DATA-001, i.e. ~10 seeds) is needed before treating this
  as validated, not just promising.
- **Regime C (whole-essay, essay-level-only): confirmed working as
  redesigned.** The behavior this run specifically checked for
  (no-rejection-on-structure-drift, unconditional essay-level-only
  labeling) held for all 3 samples.
- **QC leakage fix: consistent with working**, but zero flags on 10
  `full_ai`-adjacent... actually zero *generation* samples of type
  `full_ai` were run in R1 (not in scope) — the fix is validated by the
  regression test in `test_generation_utils.py`, not by this run
  specifically producing a true-negative on real `full_ai` output. Worth
  noting as a gap: **R1 did not re-exercise `full_ai` generation**, so
  the leakage fix's real-world false-positive rate on that category is
  confirmed only by the unit-level regression test, not by a second live
  sample.
- **Near-duplicate check scoping**: a real, minor methodology gap found,
  not yet fixed.

## Explicit non-findings

No detector was involved in producing or judging any sample. No
detection accuracy, precision, recall, or generalization claim is made.
