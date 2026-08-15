# FAIR-001 — Fairness Evaluation Design (Protocol Only, Not Executed)

**Status: DESIGN ONLY, 2026-08-15. NOT executed.** This document
specifies how a fairness evaluation of EXP-003A's (and, with caveats,
EXP-003B's) frozen detector would be run. No fairness analysis has been
performed. `reports/FAIR-001.md` will be created only after this design
is reviewed and execution is explicitly authorized.

## Research question

Does the frozen EXP-003A detector's error behavior (false-positive rate,
false-negative rate, score distribution) differ across English-language-
proficiency subgroups, for reasons unrelated to actual AI involvement?

## What this evaluates (and what it doesn't)

**Evaluates**: whether an already-fitted, already-frozen detector
(EXP-003A's logistic regression, and secondarily EXP-003B's) produces
different error rates for human essays written by English-language
learners versus other students. **Does not**: retrain anything, use
any demographic attribute as a feature, or produce a general "this
system is fair" claim — per this project's standing fairness.md ground
rule, no such claim is made unless backed by an actual evaluation on
appropriately labeled data, and even then only for the specific
comparison actually run.

## A. Primary questions

1. Does false-positive rate (human essays flagged as AI/AI-assisted)
   differ across `ell_status` groups?
2. Does false-negative rate (AI/AI-assisted essays missed) differ —
   only answerable where the AI/AI-assisted side's provenance can
   itself be tied to an `ell_status`-labeled human seed (true for every
   `full_ai`/`ai_assisted` sample in PRIMARY-DATASET-v1, since every one
   derives from a human seed with its own `family_id`).
3. Does the detector's score distribution (not just the thresholded
   decision) differ by subgroup?
4. Does behavior differ between `human`-vs-`full_ai` (EXP-003A, a
   working detector) and `human`-vs-`ai_assisted` (EXP-003B, an
   essentially chance-level detector) — **evaluating a fairness question
   on a chance-level detector is itself of limited interpretive value**,
   noted here as a scoping caveat, not deferred silently: EXP-003B's
   comparison is included for completeness, but any finding there should
   be read as "does a near-random classifier's randomness happen to
   correlate with subgroup" rather than "does a working detector treat
   subgroups differently" — those are different questions, and only the
   first is answerable given EXP-003B's current performance.

## B. Data source, separation, and a critical feasibility finding

**Source**: PERSUADE 2.0's `ell_status` field (`Yes`/`No`/unlabeled),
joined via `family_id == essay_id_comp` — the same key already used
throughout this project's provenance tracking. No new data acquisition.

**Separation, verified**: `ell_status` (and every other PERSUADE
demographic column — `gender`, `race_ethnicity`,
`economically_disadvantaged`, `student_disability_status`) is **not**
present in any generated sample record or any feature file
(`experiments/EXP-003A/features.jsonl`, `experiments/EXP-003B/features_*.jsonl`)
— re-confirmed by direct inspection for this design (grep across
`scripts/*.py` shows no code path ever reads these columns except
`load_candidate_records`, which doesn't either — see fairness.md). The
join for this experiment happens in a **separate analysis table only**,
built at evaluation time, never merged into any feature matrix a model
trains on.

**Critical feasibility finding (a legitimate design-phase check, not
execution)**: within PRIMARY-DATASET-v1's 150 families,
`ell_status` distribution is **10 `Yes` / 132 `No` / 8 unlabeled**.
**Within the frozen test split alone (23 families), this is 1 `Yes` /
22 `No`** — a single family is far too few to support any rate
comparison (§C). This single fact drives the rest of this design.

## C. Design response to the feasibility finding

**Recommendation: score all 150 families, not just the 23-family test
split, using the already-frozen EXP-003A/B models.** This is proposed
as a deliberate, justified departure from "only touch test once for the
detector's own evaluation" — because it does not touch the detector's
own development in any way:

- The model, scaler, and threshold are already fully frozen (documented
  exactly in EXP-003A/B's reproducibility sections — `C`, threshold,
  scaler parameters are all deterministic given the same code/data).
- FAIR-001 does not select, tune, or compare models/features/thresholds
  based on this scoring — it only *reads* the frozen model's output on
  more inputs.
- This is analogous to using a shipped, frozen product on new data, not
  re-opening model development.

Even with all 150 families, **`Yes` still numbers only 10** — far below
what would normally be considered adequate for a confident rate
comparison. This is disclosed as the central limitation of this
evaluation, not glossed over (§E).

**What this requires that doesn't exist yet (not built in this design
phase)**: EXP-003A/B's `results.json` currently only persists **test**-
split predictions. Scoring the full 150 families requires a small,
new, read-only script that re-applies the exact frozen
scaler+model+threshold (deterministic, same random seed, same code) to
the `train`+`validation` rows too. This is new *code* (a straightforward
extension of already-tested fitting/scoring utilities already in
`run_exp003a.py`), not new *model development* — flagged explicitly so
this distinction isn't glossed over either.

## D. Small-sample caution (mandatory reporting, not optional)

For every subgroup comparison, the FAIR-001 report (when authorized)
will report, without exception:

- Subgroup `n` (families and derived samples)
- FP count and FN count (raw, not just rates)
- FP rate and FN rate, with a small-sample-appropriate interval (Wilson
  score interval, consistent with this project's existing practice —
  see reports/EXP-003A.md's use of the same method)
- **An explicit statement of whether the subgroup can support a
  reliable comparison at all**, using a stated, non-arbitrary
  threshold: **fewer than 10 subgroup members → sample too small for
  ANY reliability claim, reported as "insufficient data," not given a
  point estimate presented as if reliable.** Given `ell_status=Yes`
  numbers exactly 10 across all of PRIMARY-DATASET-v1, this evaluation
  is expected to land right at that boundary — the design pre-commits to
  this threshold now, before seeing results, specifically so the
  threshold itself can't be adjusted after the fact to make a marginal
  result look more or less conclusive.

**Anticipated, disclosed conclusion risk**: given n=10, FAIR-001 is
likely to produce an **inconclusive** result rather than a confident
finding either direction. This is stated now, not discovered and then
downplayed later. An inconclusive fairness result is still worth
reporting plainly (per this project's standing ground rule) — "we
could not detect a difference with the data available" is a true,
useful, and honestly bounded statement, distinct from "no difference
exists."

## E. Report (deferred)

`reports/FAIR-001.md` will be created **only after this design is
reviewed and execution is authorized** — not part of this design-only
phase. Its planned structure: research question, data/join
methodology, subgroup sizes and small-sample assessment, FP/FN rates
with intervals, score-distribution comparison, EXP-003A vs. EXP-003B
scoping caveat (§A.4), limitations, conclusion (including explicit
"inconclusive" as an acceptable, honestly-reported outcome).

## Compute/data requirements

No new generation, no new model training. New work: a small scoring
script (re-apply frozen models to train+validation rows — a few seconds
of compute) and an analysis/join script (pandas merge + interval
computation — trivial). No new dependency beyond what's already
installed (`sklearn`, `pandas`, already used throughout this project).

## Limitations, stated now

- `ell_status` is binary and self/institution-reported, not a
  continuous or independently verified proficiency measure.
- Reflects the *source human writer's* subgroup for a whole family,
  including its AI-touched samples — says nothing about the AI
  generation model's own behavior conditioned on a subgroup, only about
  detector error rates on writing *originating from* essays by writers
  in that subgroup (same caveat already recorded in fairness.md).
- ~8 families (5.3%) have no `ell_status` label and are excluded from
  the comparison, not imputed.
- The n=10 `Yes` ceiling means this evaluation, even if executed
  exactly as designed, is unlikely to definitively resolve the
  fairness question for this project on its own — a future, larger
  PRIMARY-DATASET-v2 (or an ELLIPSE-based extension, still not built)
  would be needed for a more powered comparison.
