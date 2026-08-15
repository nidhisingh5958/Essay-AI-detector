# DEC-016 — Sentence-Level Localization Evaluation Design

## Status
**Provisional — design validated, detection performance is weak.**
EXP-003B (2026-08-15, [reports/EXP-003B.md](../../reports/EXP-003B.md))
confirms the *evaluation mechanism itself* works correctly (exact
`modified_spans` provenance produced 1,578 correctly-labeled sentence
rows across 127 essays, cross-checked programmatically — see
`scripts/tests/test_exp003_data_prep.py`), which is what this decision
actually governs. **The detector's current features achieve only weak
localization performance using this mechanism** (86.7% test recall at
17.6% precision; 60% top-1 per-essay accuracy on test vs. 25% on
validation) — that is a finding about the features/model (DEC-014/015),
not a defect in this evaluation design. Status is NOT marked Accepted
merely because the experiment ran, per explicit instruction — the
design is sound; whether it's *finished* (i.e. produces a launch-ready
localization signal) is a separate, still-open question.

## Date
2026-08-15

## Context

The hackathon brief requires the system to show **where** in an essay
suspicious writing occurs, not just an essay-level verdict. PRIMARY-
DATASET-v1's `ai_assisted` category (`sentence_light_controlled_v2`)
carries an exact `modified_spans` provenance field — the precise
sentence that was AI-rewritten, known by construction (DEC-011's
surgical-splice mechanism), not inferred. This is the ground truth
EXP-003B's localization evaluation must use.

## Problem

How should sentence-level "human vs. ai_assisted" localization be
evaluated for mixed essays, using what ground truth, and with what
metrics?

## Alternatives Considered

### Ground-truth source

**Alternative A — Infer AI-touched sentences via similarity to the
human original (post-hoc diffing).**
Rejected outright, and already rejected once before in this project:
DEC-011's "Post-Pilot Methodology Redesign" specifically abandoned
diff-based sentence labeling as unreliable and conceptually ambiguous
once any restructuring occurs. Re-adopting it here for evaluation
ground truth would reopen exactly that closed question.

**Alternative B (chosen) — Use the stored `modified_spans` field
directly.** Every `ai_assisted` sample in PRIMARY-DATASET-v1 has an
exact `intended_span_index` / `modified_spans` recording which sentence
was surgically replaced. Every sentence in that essay other than the
recorded span is `human`; the recorded span is `ai_assisted`. No
inference, no similarity threshold.

### Metrics

**Alternative A — Essay-level accuracy only, treating localization as a
bonus/qualitative feature.**
Rejected — the brief and this project's own evaluation.md explicitly
require sentence/passage-level results reported *separately* from
essay-level, not folded in or treated as secondary.

**Alternative B (chosen) — Standard binary classification metrics at
the sentence level: precision, recall, F1, and a confusion matrix,**
computed over every sentence in every included `ai_assisted` essay
(each sentence labeled `human` or `ai_assisted` per the provenance
above), reported **separately** from essay-level metrics, never
averaged together into one number.

Ranking/localization-specific metrics (e.g. top-k hit rate, if the
system surfaces a ranked list of "most suspicious sentences") are
**not** adopted for this round — no such ranked-output mechanism is
implemented yet, and adopting a ranking metric ahead of the mechanism
that would produce a ranking would be premature. If a scoring/ranking
UI mechanism is built later (Phase 7+), this decision should be
revisited to add rank-aware metrics then, with justification tied to
that actual mechanism.

## Decision

**Ground truth**: for each `ai_assisted` essay in the manifest, label
every sentence `human` except the one(s) named in `modified_spans`,
labeled `ai_assisted`. This is exact, not inferred.

**Evaluation scope**: only essays from the `ai_assisted` category (127
in the manifest) — `human` and `full_ai` essays are not part of the
localization task (there is no "which sentence" question for a fully
human or fully AI essay; EXP-003A already covers essay-level human vs.
full_ai separately).

**Metrics**: sentence-level precision, recall, F1, confusion matrix —
computed and reported entirely separately from EXP-003A/B's essay-level
metrics. Per-split (not just aggregate), consistent with the
train→validation→test protocol (DEC-015/test-freeze).

## Why

Using stored provenance rather than inferred similarity avoids
reopening a methodology question DEC-011 already closed for a different
but analogous reason (unreliable, ambiguous diff-based attribution), and
keeps ground truth exact — consistent with this whole project's
insistence on exact, constructed ground truth over inferred
approximations.

## Evidence

**EXP-003B executed 2026-08-15.** Ground-truth construction: 1,707 raw
sentences across 127 `ai_assisted` essays, 1,578 retained after
excluding 129 with an undefined `predictability_delta` (documented, not
imputed — see EXP-003B §4); 119 of 127 essays retained a locatable
positive-labeled sentence (8 lost theirs because the AI-edited sentence
was the essay's first sentence). **Detection performance using this
ground truth**: at a validation-selected threshold (0.06, reflecting
~8% positive prevalence), test recall 86.7% (13/15) at precision 17.6%
(61 false positives/182 negatives). A secondary, essay-normalized
metric (added this round specifically to avoid essays with more
sentences dominating an aggregate, per explicit instruction) — top-1
accuracy (does the single highest-scored sentence in an essay match the
true target) — reached 60.0% on test (9/15) vs. 25.0% on validation
(5/20), a real but noisy signal given the small per-split counts.

## Trade-offs

Localization can only be evaluated on the `ai_assisted` category (127
essays, further split three ways) — a small evaluation set, especially
per-split (as few as 16 essays in `test`). Any localization metric from
this round should be read with that sample-size caveat explicit, not
presented as a stable rate.

## Consequences

Positive: localization ground truth requires no new mechanism or
inference step — it reuses data already recorded during dataset
construction.
Negative: this evaluation protocol says nothing about
`sentence_moderate_controlled_v2` or paragraph-level localization
(excluded from PRIMARY-DATASET-v1 entirely) — any future work on those
categories needs its own localization design.

## Revisit When

1. If a ranked/scored sentence-level UI output is built, add rank-aware
   metrics with justification tied to that mechanism.
2. If PRIMARY-DATASET-v1-v2 adds more `ai_assisted` samples, the small-
   sample caveat above should be reassessed with the new counts.

## Implementation

Not yet implemented — EXP-003B has not run. Ground-truth field already
exists: `modified_spans` in `data/generated/PRIMARY-DATASET-v1/samples.jsonl`.

## Tests / Experiments

Not yet — pending EXP-003B execution.
