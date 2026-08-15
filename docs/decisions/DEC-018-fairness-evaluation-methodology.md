# DEC-018 — Fairness Evaluation Methodology (FAIR-001)

## Status
Provisional (**executed 2026-08-15** — Category A finding, no material
disparity detected within the available data; remains Provisional, not
Accepted, given the small `n=10` `ell_status=Yes` sample — see Evidence)

## Date
2026-08-15

## Context

`fairness.md` has carried a design sketch since earlier phases (DEC-009
anticipated PERSUADE's `ell_status` / ELLIPSE as the eventual fairness
data source). Now that EXP-003A produces an actual frozen detector,
this decision fixes exactly how a fairness evaluation of it would be
run, including a concrete feasibility problem discovered while
designing it (see Evidence).

## Problem

How should detector error-rate fairness be evaluated across English-
proficiency subgroups, given the available data, without ever using a
demographic attribute as a model feature, and without overstating
confidence in a small-sample comparison?

## Alternatives Considered

### Data source
**Alternative A — Wait for an ELLIPSE-based dataset extension** (finer-
grained, continuous proficiency scores).
Advantages: richer signal than a binary flag.
Disadvantages: requires a whole new dataset-extension effort, not yet
built, and PRIMARY-DATASET-v1 is frozen — blocks any fairness work
until that separate effort happens.

**Alternative B (chosen) — Use PERSUADE's existing `ell_status`
field**, already present in the source corpus every PRIMARY-DATASET-v1
human essay derives from, joined via `family_id`.
Advantages: no new data acquisition; usable immediately against the
already-frozen EXP-003A/B models.
Disadvantages: binary, self/institution-reported, not independently
verified — a real limitation, disclosed (FAIR-001 §Limitations), not
hidden.

### Which split(s) to evaluate on
**Alternative A — Only the frozen test split (23 families).**
Advantages: strictest adherence to "test is touched once."
Disadvantages: **found to be infeasible** — only 1 of 23 test families
has `ell_status=Yes`, making any rate comparison meaningless by
construction (n=1).

**Alternative B (chosen) — Score all 150 families (train+validation+test)
using the already-frozen model, unchanged.**
Advantages: raises the `Yes` subgroup from 1 to 10 — still small, but
at least minimally comparable; does not touch model development (the
model is not retrained, tuned, or reselected using this data, only
read from).
Disadvantages: requires new code to score train/validation rows (not
previously persisted) — disclosed as new work, not new model training.
Blurs the usual "test-only" framing in a way that must be explained
clearly in any report using it, so it isn't mistaken for a second
detector-selection test-set touch.

## Decision

**Alternative B for both**: PERSUADE's `ell_status`, joined via
`family_id`, evaluated against the already-frozen EXP-003A (and,
scoped separately, EXP-003B) model applied to all 150 families. Full
protocol: [FAIR-001.md](../experiments/FAIR-001.md).

**Hard rule, non-negotiable**: `ell_status` and every other PERSUADE
demographic field are joined only in a separate analysis table, never
into any feature matrix a model trains on. Verified by direct code
inspection (no generation script reads these columns except
`load_candidate_records`, which also doesn't use them downstream) —
recorded in fairness.md.

**Small-sample threshold, fixed in advance**: fewer than 10 subgroup
members → reported as "insufficient data for a reliability claim," not
given a bare point estimate. Chosen now, before FAIR-001 runs,
specifically so it can't be adjusted afterward to make a marginal
result look more or less conclusive either way.

## Why

Using the already-available `ell_status` field unblocks a real fairness
evaluation now rather than waiting on an unbuilt ELLIPSE extension, and
scoring all 150 families is the only way to get a subgroup size (10)
large enough to even attempt a comparison — while keeping the
"never touches model development" boundary explicit so this expanded
scoring doesn't quietly erode the test-set discipline used everywhere
else in this project.

## Evidence

**Design-phase feasibility check, 2026-08-15** (not an execution of
FAIR-001 itself): `ell_status` distribution across PRIMARY-DATASET-v1's
150 families — 10 `Yes`, 132 `No`, 8 unlabeled. Within the frozen test
split alone — 1 `Yes`, 22 `No`. This single finding is what drove
Alternative B's selection over Alternative A above.

**Updated 2026-08-15 — FAIR-001 executed** (see
[reports/FAIR-001.md](../../reports/FAIR-001.md) for full results).
Both frozen detectors (EXP-003A primary combined, EXP-003B essay-level
primary combined) were refit-reproduced (verified byte-identical
`chosen_C` to their recorded values) and applied, unchanged, to all
150 families. **No demographic field leakage** into any feature file,
re-verified programmatically (not just claimed at design time).

For the working detector (EXP-003A, human vs. `full_ai`): human
false-positive rate 0.0% (`ell_status=Yes`, n=10) vs. 0.76% (`No`,
n=132); AI false-negative rate 0.0% vs. 0.0%. Score distributions
overlap substantially between groups. **No material disparity
detected** — Category A, but explicitly bounded by the small `n=10`
`Yes` group (Wilson 95% CI up to ±27.8 points), so this rules out only
a large disparity, not a smaller one.

For the near-chance detector (EXP-003B essay-level, human vs.
`ai_assisted`): both groups sit near-ceiling false-positive rate
(100% `Yes` vs. 95.45% `No`) — consistent with this detector's own
degenerate near-universal-positive behavior at its frozen threshold,
not interpretable as a subgroup effect (the anticipated scoping caveat
in FAIR-001.md §A.4, confirmed as it played out).

A secondary, exploratory ELLIPSE proficiency-score comparison (n=9,
below the `n=10` threshold) produced descriptive data only — no
correlation statistic computed or claimed, per the pre-registered
small-sample rule.

## Trade-offs

Even the best available design here (n=10) is likely to produce an
**inconclusive** result rather than a confident finding — accepted and
disclosed in advance (FAIR-001 §D) as more honest than either skipping
the evaluation entirely or overstating what a small sample can show.

## Consequences

Positive: a concrete, executable fairness protocol exists, using only
already-available data, with no risk of demographic-feature leakage
into the detector.
Negative: the evaluation, even when run, will likely be underpowered —
a real, disclosed ceiling on what this project can currently claim
about fairness, not resolved by this decision.

## Revisit When

1. If PRIMARY-DATASET-v1 is superseded by a larger v2, or an
   ELLIPSE-based extension is built, re-run FAIR-001 with the larger
   subgroup size that would provide.
2. If FAIR-001's inconclusive result (anticipated) is later
   supplemented by a differently-designed comparison (e.g. a
   purpose-built, balanced-by-`ell_status` sample), revisit whether
   this design should be superseded rather than extended.

## Implementation

`scripts/run_fair001_score_all.py` (Stage 1: scores all 150 families
with the frozen EXP-003A/EXP-003B essay-level models, refit-
reproduction verified before scoring), `scripts/run_fair001_fairness_analysis.py`
(Stage 2: `ell_status`/ELLIPSE join, subgroup metrics, small-sample
rule, no-leakage verification — all in a separate analysis layer, never
merged into any feature file).

## Tests / Experiments

`scripts/tests/test_fair001_execution.py` (15 tests: threshold-rule
correctness, FP/FN calculation correctness, score aggregation,
no-demographic-leakage, subgroup-join correctness, reproduction-check
values). FAIR-001 itself: [reports/FAIR-001.md](../../reports/FAIR-001.md).
