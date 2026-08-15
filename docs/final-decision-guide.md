# Final Decision Guide — Generation Methodology → Primary Dataset

One-page reference for "what's in, what's out, and why." Strategic
decision made 2026-08-13, executed 2026-08-14/15 as
`PRIMARY-DATASET-v1` (150 families, 425-sample benchmark — see
[reports/FINAL-DATASET-CONSTRUCTION.md](../reports/FINAL-DATASET-CONSTRUCTION.md)
for actual results), **approved and FROZEN as the immutable v1
benchmark, 2026-08-15** (`data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json`
— not to be silently mutated; a genuine defect gets a documented,
versioned successor, PRIMARY-DATASET-v2, not a silent edit). Full
reasoning lives in [DEC-011](decisions/DEC-011-mixed-text-generation.md)'s
"Strategic Decision" section; full dataset construction plan in
[dataset.md](dataset.md); quick-reference decision table in
[decision-summary.md](decision-summary.md).

**Current phase (2026-08-15): detector EXPERIMENT DESIGN, not
training.** [experiments/EXP-003.md](experiments/EXP-003.md) specifies
EXP-003A (human vs. full_ai), EXP-003B (human vs. ai_assisted, essay +
sentence-localization), and EXP-003C (three-class) — feature set
(DEC-014), model/threshold strategy (DEC-015), localization evaluation
(DEC-016), and evidence mapping (DEC-017) are all designed but **not
executed**. No detector has been trained, tuned, or evaluated.

## Included in the primary dataset

| Category | Label | Status |
|---|---|---|
| Human original essays | `human` | Ground truth by definition. **150 in PRIMARY-DATASET-v1.** |
| Fully AI-generated essays | `machine` | Validated, EXP-DATA-001; re-confirmed clean, EXP-DATA-001-R4. **148/150 in PRIMARY-DATASET-v1** (2 excluded: genuine self-reference) |
| Controlled sentence-light AI-assisted | `ai_assisted` | **Used with mandatory semantic review.** 22/25 preserved at EXP-DATA-001-R3's scale; **127/141 (90.1%) preserved in PRIMARY-DATASET-v1's full 150-family construction** — a real, larger-sample drift rate (8 changed, 6 questionable), reported honestly |

## Excluded from the primary dataset (not deleted, not hidden)

| Category | Status | Why |
|---|---|---|
| `sentence_moderate_controlled_v2` | **"Insufficient semantic reliability for primary dataset construction."** | 33% changed rate (EXP-DATA-001-R2). 3 redesign candidates drafted (M1/M2/M3), untested. May be revisited as future work. |
| `paragraph_light_controlled` | **"Promising structural mechanism but insufficient semantic reliability for primary dataset construction."** | Exact ground truth by construction, but EXP-DATA-001-R3 found meaning-reversal drift neither automated screen catches (2/12 changed, both missed by screening). |
| `paragraph_moderate_controlled` | Same as above | 1/12 changed (a narrator-identity swap), 3/12 questionable. |

All excluded categories' experiments, samples, and failure findings
remain fully preserved in `data/generated/`, `reports/`, and
`failure-analysis.md` — exclusion from the primary dataset is a scope
decision, not an evidentiary one.

## The screening pipeline (mandatory order, never skipped)

```
Automated screening (DEC-012 embedding+fact-check, DEC-013 coverage+fact-check)
        |
        v
risk triage  <-- prioritizes review order; NEVER decides inclusion
        |
        v
human semantic review (generation-methodology.md Section 12 protocol)
        |
        v
final ground truth (semantic_preservation field)
```

**The automated screen never overrides human review.** A sample the
screen marks `likely_preserved` still gets full manual review before
entering the dataset; if human review says `"changed"` or
`"questionable"`, the sample is excluded from the high-confidence
dataset regardless of what the screen said. This is not a hypothetical
safeguard: EXP-DATA-001-R3 found 2 real `"changed"` paragraph samples
the automated screens missed, and **PRIMARY-DATASET-v1's construction
found this at much larger scale — 6 of 8 real "changed" sentence-level
samples (75%) were labeled `likely_preserved`.** Had this rule not been
followed, those 6 samples plus 3 "questionable" ones would have entered
the benchmark as false positive ground truth.

## What the automated screens are — and are not

**Are**: automated semantic-**risk screening / triage** tools — cheap,
fast, useful for prioritizing which samples most need careful human
attention, and reliably effective at one specific failure type (numeric/
entity substitution: **0 missed across every validation round to
date**, including PRIMARY-DATASET-v1's 141-sample check).

**Are not**: a semantic safety gate, ground truth, or a substitute for
human review under any circumstance. Known, confirmed blind spots:
meaning reversal (a fluent, structurally-similar rewrite stating the
opposite of the original — e.g. "should not be allowed" → "should not
be discouraged") and claim omission merged inside a garbled, multi-claim
sentence. Observed at the paragraph level in EXP-DATA-001-R3 (2/3
missed) and **at the sentence level, at a higher rate, in
PRIMARY-DATASET-v1 (6/8 missed, 75%)** — not theoretical, and not a
one-off. NLI/entailment (DEC-012 Alternative B) is documented as a
possible future enhancement for the reversal gap — **not being added
right now**; the current conclusion is that automated semantic models
are useful for triage but cannot currently serve as final semantic
ground truth.

## Where the reasoning lives

- **Why sentence-light was used**: [DEC-011](decisions/DEC-011-mixed-text-generation.md) Strategic Decision; [reports/EXP-DATA-001-R2.md](../reports/EXP-DATA-001-R2.md), [reports/EXP-DATA-001-R3.md](../reports/EXP-DATA-001-R3.md) §A.
- **Why sentence-moderate and paragraph-level are excluded**: DEC-011 Strategic Decision; [failure-analysis.md](failure-analysis.md) Failures 4, 7–12.
- **Why the automated screens are triage, not ground truth**: [DEC-012](decisions/DEC-012-semantic-preservation-screen.md) "Reframing" and "Third Validation, at Scale"; [DEC-013](decisions/DEC-013-claim-survival-screen.md) "Validation Results".
- **How the primary dataset was built, and what it actually contains**: [dataset.md](dataset.md) (plan) and [reports/FINAL-DATASET-CONSTRUCTION.md](../reports/FINAL-DATASET-CONSTRUCTION.md) (actual results).
