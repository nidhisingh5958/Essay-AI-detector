# DEC-019 — GEN-001 Held-Out Generator Selection

## Status
Provisional (design-only — GEN-001 has not been executed, no generator
downloaded)

## Date
2026-08-15

## Context

Every EXP-003 result to date is scoped to Qwen2.5-1.5B-Instruct
specifically (DEC-010) — an explicitly named, repeated limitation in
every report so far. DEC-010 itself deferred testing a hosted API model
"for a future held-out generalization test only." This decision fixes
which generator that test uses, and how, before any download or
generation happens.

## Problem

Which second generation model should serve as GEN-001's held-out
generalization test, and how should the evaluation be structured so the
held-out data cannot influence the model being tested?

## Alternatives Considered

### Alternative A — A different-size Qwen variant (e.g. Qwen2.5-7B-Instruct)
Advantages: minimal new infrastructure (same model family/tokenizer
lineage already integrated).
Disadvantages: **rejected** — same vendor, same training recipe/family.
Tests whether more Qwen capacity changes detectability, not whether the
signal generalizes beyond Qwen. Does not answer GEN-001's actual
research question.

### Alternative B — A hosted API model (GPT-4o-mini, Claude Haiku, Gemini Flash)
Advantages: maximally different training data/vendor/architecture — the
strongest possible test of generalization.
Disadvantages: requires an API key and real (if modest) cost; less
reproducible for anyone without their own credentials; reopens the
vendor-lock-in/reproducibility concerns DEC-010 already weighed when
selecting a local model as primary. **Deferred, not rejected** — a
natural second-phase test if Phi-3.5-mini-instruct's result
(Alternative C) is informative enough to justify the added cost.

### Alternative C (chosen) — Phi-3.5-mini-instruct (Microsoft), local
Advantages: MIT-licensed, free, no API key, fully reproducible;
different vendor, training corpus, and architecture family from Qwen —
genuinely distinct, not a same-family variant; same local-inference
pattern already used throughout this project (EXP-DATA-001 through R4),
no new infrastructure category.
Disadvantages: still a single alternative model — establishes
generalization to *that* model specifically, not to AI-generated text
in general; a real, disclosed scope limit, not a claim this decision
overstates.

## Decision

**Alternative C**: Phi-3.5-mini-instruct as GEN-001's held-out
generator, full_ai category only for this first pass (not
`ai_assisted` — see GEN-001.md §E for why that's deferred, not
avoided). Full protocol: [GEN-001.md](../experiments/GEN-001.md).

**Held-out principle, hard constraint**: EXP-003A's already-frozen
model (scaler, `C`, threshold) is applied unchanged to the new
generator's essays. No refitting, no threshold reselection, no feature
changes based on this data — the model under test must not be allowed
to see or adapt to the held-out generator's data in any way.

**Scope**: reuse PRIMARY-DATASET-v1's existing 23 test-split human
essays (unmodified, not regenerated); generate only their Phi-3.5-mini-
instruct `full_ai` counterparts, newly, stored separately in
`data/generated/GEN-001/` — never merged into PRIMARY-DATASET-v1.

## Why

Phi-3.5-mini-instruct is the best available balance of "genuinely
different from Qwen" (different vendor/corpus/architecture) against
"small, free, reproducible, no new infrastructure" — matching this
project's standing preference (DEC-007, DEC-010) for local,
license-clear, no-cost models, while still being a real test of
generalization rather than a same-family variant that would beg the
research question.

## Evidence

None yet — this is a pre-registration of the generator choice and
evaluation design, written before any download or generation happens,
so the choice can't be adjusted reactively based on results.

## Trade-offs

A single alternative generator cannot establish universal
generalization — only generalization to this specific second model.
Accepted as the appropriate scope for a "small held-out evaluation"
(per explicit instruction not to build a second full dataset), with
Alternative B (a hosted API model) available as a deliberate next step
if this result warrants the added cost.

## Consequences

Positive: a concrete, low-cost, fully reproducible generalization test
is now specified and ready to execute once authorized.
Negative: `ai_assisted` cross-generator generalization remains entirely
untested after this first pass — a real, disclosed gap in what GEN-001
alone can establish (GEN-001.md §E).

## Revisit When

1. If Phi-3.5-mini-instruct's result shows either strong generalization
   or a large collapse, that is itself grounds to consider Alternative
   B (a hosted API model) as a stronger, second-phase test — not
   decided now, revisited with that evidence.
2. If EXP-003B's `ai_assisted` detector improves enough to be worth
   testing for cross-generator generalization (currently near-chance at
   the essay level, weak-precision at the sentence level — EXP-003B/
   B-R1), extend GEN-001 to that category then, not before.

## Implementation

Not yet implemented — no generator downloaded, no generation run.

## Tests / Experiments

Not yet — pending GEN-001 execution, explicitly not authorized in this
design phase.
