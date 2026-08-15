# DEC-019 — GEN-001 Held-Out Generator Selection

## Status
Provisional (**executed 2026-08-15** — see Evidence below; remains
Provisional, not Accepted, per standing instruction not to auto-resolve
decisions from a single held-out generator/single pass)

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

**Updated 2026-08-15 — GEN-001 executed** (see
[reports/GEN-001.md](../../reports/GEN-001.md) for full results). Phi-
3.5-mini-instruct (revision `2fe192450127e6a83f7441aef6e3ca586c338b77`)
generated 23/23 `full_ai` essays, all passing QC with zero flags on
first generation. Applying EXP-003A's frozen model (unchanged, refit-
reproduction verified byte-identical to its recorded `chosen_C` values)
to the held-out Phi essays found **mixed transfer**: the primary
(combined) and stylometric-only feature groups transferred essentially
perfectly (identical accuracy to Qwen's own frozen test result, zero
score-distribution overlap between human and Phi `full_ai`), while the
LM-only feature group — already the weakest, least-trusted group across
three prior Qwen-only experiments — degraded further specifically on
Phi (`full_ai` recall 100%→56.5%). This validates the core premise of
Alternative C (genuinely different vendor/architecture from Qwen
produces a real, informative test) rather than a same-family variant
that would have begged the question. The single held-out generator
scope limitation (Trade-offs, below) stands as originally stated — this
result establishes generalization to Phi-3.5-mini-instruct specifically,
not universally.

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

`scripts/phi_generate.py` (generation wrapper), `scripts/run_gen001_generate.py`
(Stage 1: generation), `scripts/run_gen001_features.py` (Stage 2:
feature extraction, reuses `exp003a_extract_features.py` unchanged),
`scripts/run_gen001_evaluate.py` (Stage 3: evaluation against the
frozen EXP-003A model).

## Tests / Experiments

`scripts/tests/test_gen001.py` (8 tests: provenance, no-leakage,
frozen-dataset-checksum, split-value hygiene, feature-schema
compatibility, and freeze-reproduction invariants). GEN-001 itself:
[reports/GEN-001.md](../../reports/GEN-001.md).
