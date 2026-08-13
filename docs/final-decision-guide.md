# Final Decision Guide — Generation Methodology → Primary Dataset

One-page reference for "what's in, what's out, and why," as of the
2026-08-13 post-R3 strategic review. Full reasoning lives in
[DEC-011](decisions/DEC-011-mixed-text-generation.md)'s "Strategic
Decision" section; full dataset construction plan in
[dataset.md](dataset.md); quick-reference decision table in
[decision-summary.md](decision-summary.md).

## Included in the primary dataset

| Category | Label | Status |
|---|---|---|
| Human original essays | `human` | Ground truth by definition |
| Fully AI-generated essays | `machine` | Validated, EXP-DATA-001 |
| Controlled sentence-light AI-assisted | `ai_assisted` | **Approved for controlled dataset construction, with mandatory semantic review.** 22/25 preserved, 1/25 changed at 2.5x EXP-DATA-001-R2's scale (EXP-DATA-001-R3) |

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
safeguard — EXP-DATA-001-R3 found 2 real `"changed"` paragraph samples
the automated screens missed, which is exactly the scenario this rule
protects against.

## What the automated screens are — and are not

**Are**: automated semantic-**risk screening / triage** tools — cheap,
fast, useful for prioritizing which samples most need careful human
attention, and reliably effective at one specific failure type (numeric/
entity substitution: 0 missed across 3 validation rounds, calibration
through R3).

**Are not**: a semantic safety gate, ground truth, or a substitute for
human review under any circumstance. Known, confirmed blind spots:
meaning reversal (a fluent, structurally-similar rewrite stating the
opposite of the original) and claim omission merged inside a garbled,
multi-claim sentence — both observed directly in EXP-DATA-001-R3, not
theoretical. NLI/entailment (DEC-012 Alternative B) is documented as a
possible future enhancement for the reversal gap — **not being added
right now**; the current conclusion is that automated semantic models
are useful for triage but cannot currently serve as final semantic
ground truth.

## Where the reasoning lives

- **Why sentence-light is approved**: [DEC-011](decisions/DEC-011-mixed-text-generation.md) Strategic Decision; [reports/EXP-DATA-001-R2.md](../reports/EXP-DATA-001-R2.md), [reports/EXP-DATA-001-R3.md](../reports/EXP-DATA-001-R3.md) §A.
- **Why sentence-moderate and paragraph-level are excluded**: DEC-011 Strategic Decision; [failure-analysis.md](failure-analysis.md) Failures 4, 7–12.
- **Why the automated screens are triage, not ground truth**: [DEC-012](decisions/DEC-012-semantic-preservation-screen.md) "Reframing"; [DEC-013](decisions/DEC-013-claim-survival-screen.md) "Validation Results".
- **How the primary dataset will be built**: [dataset.md](dataset.md) — design only, not yet executed.
