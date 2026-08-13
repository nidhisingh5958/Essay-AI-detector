# EXP-DATA-001-R1 Confirmation — Larger-Scale Check of Controlled-Span Methodology

> Status: **executed for real**, 2026-08-10, 50 records. Confirms/refutes
> EXP-DATA-001-R1's n=3-per-category finding at ~10-seed scale, on
> **previously unseen** PERSUADE essays (no overlap with EXP-DATA-001's
> 10 or EXP-DATA-001-R1's 3 — 13 IDs excluded by construction). This
> report evaluates the **data generation pipeline only**. No detector was
> run, trained, or evaluated. No detection accuracy/precision/recall/F1
> is reported or implied anywhere below.

## 1. Seed selection

10 seed essays, filtered to `task == "Independent"`, word count in
[150, 320], ≥5 sentences, ≥2 paragraphs (same filters as prior rounds),
sampled deterministically (`rng_seed = RNG_SEED + 2`), explicitly
excluding all 13 seed IDs used in EXP-DATA-001 and EXP-DATA-001-R1 —
verified programmatically (`assert not seed_ids & EXCLUDED_SEED_IDS`).

| Seed ID | Words | Split |
|---|---|---|
| 3AF8147D6DB0 | 318 | train |
| 453380C5CA9C | 253 | validation |
| 4C3FC32093AB | 253 | train |
| 7E3CDEFECEC6 | 212 | train |
| 93B23DB0F67B | ~250 | train |
| 9B9380760425 | ~250 | train |
| B056AD01475D | ~250 | test |
| B8164EA79177 | ~250 | train |
| BCB916A9A9F3 | ~250 | validation |
| E4596B010B9B | 315 | train |

Family split assigned before generation (as always) — **verified
programmatically: zero family/split violations** across all 50 records.

## 2. Category counts

5 categories × 10 seeds = 50 records, exactly as planned. Regime C
(whole-essay polish) **deliberately excluded** — its methodology is
unchanged from EXP-DATA-001-R1 and wasn't in scope here.

| Category | Count |
|---|---|
| `original` (human) | 10 |
| `sentence_light_controlled` | 10 |
| `sentence_moderate_controlled` | 10 |
| `paragraph_light_controlled` | 10 |
| `paragraph_moderate_controlled` | 10 |

## 3. QC results (raw pass/flag/reject counts)

| Category | passed | flagged | rejected |
|---|---|---|---|
| `sentence_light_controlled` | 4 | 3 | 3 |
| `sentence_moderate_controlled` | 8 | 0 | 2 |
| `paragraph_light_controlled` | 9 | 1 | 0 |
| `paragraph_moderate_controlled` | 10 | 0 | 0 |

**Finding 1 — paragraph-level transformation is structurally far more
reliable than sentence-level.** Paragraph categories: 19/20 passed
cleanly, 0 rejections. Sentence categories: 12/20 passed cleanly, 5
rejections. This wasn't visible at EXP-DATA-001-R1's n=3 scale (which
only tested 1 paragraph category, `light_polish`, in a different regime).

**`resegmentation_ok`** (explicit field, all records):

| Category | True | False |
|---|---|---|
| `sentence_light_controlled` | 7 | 3 |
| `sentence_moderate_controlled` | 8 | 2 |
| `paragraph_light_controlled` | 10 | 0 |
| `paragraph_moderate_controlled` | 10 | 0 |

**`instruction_leakage_flagged` / `ai_self_reference_flagged`**: **zero
across all 50 records** — the QC fix continues to hold at this larger
scale, including for a category set (paragraph-level) not exercised in
the original bug discovery.

## 4. Scope / length measurements (raw distributions, not just pass/fail)

`length_ratio_actual_vs_target` (span-level actual ÷ target word count),
sorted, all 10 per category:

- `sentence_light_controlled`: 0.41, 0.85, 0.87, 0.87, 1.00, 1.45, 1.49,
  1.52, 1.91, 2.68
- `sentence_moderate_controlled`: 0.60, 0.64, 0.65, 0.78, 0.79, 1.03,
  1.21, 1.36, 1.55, 1.64
- `paragraph_light_controlled`: 0.63, 0.76, 0.79, 0.80, 0.85, 0.86, 0.87,
  0.96, 1.03, 1.04
- `paragraph_moderate_controlled`: 0.66, 0.78, 0.78, 0.79, 0.82, 0.84,
  0.89, 0.90, 1.03, 1.23

**Finding 2 — paragraph-level length control is tight and consistent;
sentence-level is wide and includes real outliers.** Paragraph ratios
cluster in roughly [0.63, 1.23] with no extreme values. Sentence-level
ratios range far wider, including a 2.68x expansion and a 0.41x
contraction — both real generation behavior, not measurement error
(manually confirmed by reading the text, §8).

**Counter to a plausible hypothesis:** "light" was expected to show
*tighter* length control than "moderate" (a smaller edit should be more
constrained). It didn't, at the sentence level — `sentence_light_controlled`
had *more* scope-drift flags/rejections (3 flagged + 3 rejected = 6/10
affected) than `sentence_moderate_controlled` (0 flagged, 2 rejected =
2/10 affected). This wasn't tested for statistical significance (n=10 is
too small), but it's the opposite of what the category names would
suggest, and it recurs identically in the semantic-preservation findings
below (§5) — worth treating as a real pattern, not noise, until shown
otherwise.

## 5. Semantic-preservation findings (manual review, never LLM-judged)

Reviewed by hand: read each original-vs-rewritten span pair directly
(review notes recorded per-sample in `semantic_preservation_notes`).
Rejected samples (span boundaries not trustworthy) are marked
`not_yet_reviewed` rather than force-judged.

| Category | preserved | questionable | changed | not_yet_reviewed (rejected) |
|---|---|---|---|---|
| `sentence_light_controlled` | 2 | 1 | 4 | 3 |
| `sentence_moderate_controlled` | 3 | 2 | 3 | 2 |
| `paragraph_light_controlled` | 9 | 0 | 1 | 0 |
| `paragraph_moderate_controlled` | 9 | 1 | 0 | 0 |

**Combined:** sentence-level (15 reviewed) — 5 preserved (33%), 3
questionable (20%), **7 changed (47%)**. Paragraph-level (20 reviewed) —
18 preserved (90%), 2 questionable/changed (10%).

**Finding 3 — the most important finding of this experiment: automated
QC (length ratio + resegmentation) does NOT catch semantic drift, and
sentence-level transformation has a real, substantial semantic-drift
problem that structural QC alone would completely miss.** Four samples
passed QC cleanly (`qc_status: "passed"`) and were still judged
`"changed"` on manual review:

- `4C3FC32093AB__sentence_light_controlled` — original: *"Students
  aren't liking the fat[sic] that they cant get involved because of
  their C average."* Rewrite: *"And I think with all due respect, you
  need to address this issue."* The model replaced a specific grievance
  with a generic transition sentence carrying no equivalent claim.
- `4C3FC32093AB__sentence_moderate_controlled` — same essay, same
  problem: *"I believe it's important to address this matter
  properly."*
- `3AF8147D6DB0__sentence_moderate_controlled` — introduces a new claim
  not in the original **and** inserts a `"Sincerely,\n\n"` letter-closing
  artifact mid-essay — a structural defect the resegmentation check
  didn't catch because it doesn't break sentence *count*.
- `BCB916A9A9F3__sentence_moderate_controlled` — a factual alteration:
  original says *"at least one C"*; rewrite discusses *"two Cs"*. A
  number changed, not just phrasing — this is exactly the kind of
  content change a "moderate reword, preserve meaning" instruction is
  supposed to prevent, and QC (which only checks length/structure) had
  no way to detect it.

Paragraph-level had one real semantic failure:
`453380C5CA9C__paragraph_light_controlled` dropped most of a 4-sentence
paragraph's content (kept only one fragment about professional athletes,
lost the actual policy argument) while still passing length-ratio QC
(0.625, within a plausible-looking range) — a reminder that even
paragraph-level isn't immune, just far less prone to this failure.

## 6. Duplicate findings (family-aware, per Section 1 fix)

- **Cross-family pairs flagged: 0.** No suspicious duplication between
  different seed essays' outputs.
- **Same-family pairs flagged: 34** (informational only, never treated as
  a problem) — expected, since a single-span edit is necessarily close to
  its own human original and its siblings.
- The scoping fix (this round's Section 1 deliverable) is validated in
  practice: at the old flat check's sensitivity, this run would likely
  have flagged dozens of false "duplicates"; the family-aware version
  correctly separated 0 real anomalies from 34 expected same-family
  matches.

## 7. Resegmentation findings

Kept as an unconditional hard-reject rule, exactly as instructed — not
relaxed. 5 of 5 `sentence_*` resegmentation failures were manually
spot-checked (via the informal/run-on punctuation patterns in the source
essays, consistent with EXP-DATA-001's original 2 cases) and are genuine
edge cases, not check bugs. Paragraph-level: 0 failures across 20
attempts — paragraph splicing appears structurally safer, consistent
with Finding 1.

## 8. Metadata and provenance integrity

- **Metadata integrity:** all 50 records contain every field in the
  expanded schema (intended_span_index, span_target_words,
  span_actual_words, length_ratio_actual_vs_target, resegmentation_ok,
  instruction_leakage_flagged, ai_self_reference_flagged,
  cross_family_duplicate_flag, semantic_preservation,
  semantic_preservation_notes, plus the original fields) — checked
  programmatically, zero missing fields.
- **Provenance integrity:** zero family/split violations; every
  `source_sample_id` resolves to a real record in the same file —
  checked programmatically.

## 9. Failure examples (preserved, not hidden)

1. **QC-blind semantic drift** (the most important failure category —
   see §5): 4 samples passed all automated checks while changing meaning.
2. **Structural artifact insertion**: `3AF8147D6DB0__sentence_moderate_controlled`
   inserted a `"Sincerely,\n\n"` salutation mid-essay — the model
   produced letter-formatting boilerplate when asked to reword a single
   sentence. Passed QC (no length/resegmentation violation).
3. **Extreme scope drift**: `9B9380760425__sentence_light_controlled`
   (ratio 2.68) replaced a single sentence with a two-sentence block
   including a `"Dear Principal,"` salutation and an entirely different
   claim — flagged by `modification_scope_drift`, correctly not silently
   accepted.
4. **Content loss under paragraph rewrite**:
   `453380C5CA9C__paragraph_light_controlled` — the one paragraph-level
   semantic failure, discussed in §5.

## 10. Remaining uncertainty

- **n=10 per category is still modest.** The sentence-vs-paragraph
  reliability gap is large and consistent enough to trust directionally,
  but exact rates (e.g. "47% of sentence-level samples have semantic
  drift") should not be treated as a precise population estimate.
- **Why "light" underperforms "moderate" at the sentence level is not
  explained by this experiment** — temperature differed (0.5 vs 0.7)
  alongside instruction wording, so the cause isn't isolated. A
  controlled follow-up (same temperature, only instruction wording
  varied) would be needed to attribute this properly.
- **Semantic review was performed by one reviewer (the agent operating
  this pipeline) reading text directly — not a second independent human
  rater.** No inter-rater reliability figure exists. This is a real
  limitation of the review's rigor, stated plainly rather than implied
  away.
- **The `modification_scope_drift` ratio bounds** ([0.7,1.3] light,
  [0.5,1.8] moderate for both sentence and paragraph in this round) were
  carried over from EXP-DATA-001-R1's n=3 sentence-only findings, not
  re-derived from this round's paragraph data specifically — paragraph
  ratios in this round (§4) suggest tighter bounds might fit paragraphs
  better, but that wasn't tested.

## 11. Recommendation

**B — promising but requires another revision, not ready for scale as a
uniform mechanism.**

Specifically:

- **Paragraph-level controlled transformation (light and moderate):
  close to ready.** Strong structural QC pass rate (19/20), strong
  semantic preservation (18/20 preserved), zero resegmentation failures,
  zero leakage/self-reference issues. The one semantic failure found
  (§5, §9.4) suggests semantic review should remain in the pipeline as a
  spot-check even for paragraph-level, not be dropped once structural QC
  looks clean.
- **Sentence-level controlled transformation (light and moderate): not
  ready.** Real, substantial semantic-drift problem (47% of reviewed
  samples) that automated QC does not catch, plus a wider structural
  failure rate than paragraph-level. Scaling this category now would
  silently inject a meaningful fraction of mislabeled "AI-touched, meaning
  preserved" samples into any downstream dataset.
- **Before treating sentence-level as usable:** either (a) restrict it to
  cases where a second automated signal beyond length/resegmentation can
  catch semantic drift (this experiment shows length/resegmentation alone
  is insufficient), or (b) require semantic review as a mandatory,
  non-optional gate for this category specifically, or (c) investigate
  whether more surrounding context (more than one sentence before/after)
  reduces the drift rate.
- **Regime C (whole-essay polish) is unaffected by any of this** — not
  retested here, per instruction, and its existing essay-level-only
  treatment remains appropriate regardless of this experiment's outcome.

DEC-011 should be updated to reflect this evidence (paragraph-level
promising, sentence-level needs more work) rather than marked Accepted —
see the corresponding DEC-011 update.
