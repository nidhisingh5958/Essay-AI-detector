# DEC-014 — EXP-003 Feature Set and Baseline Definitions

## Status
Provisional (validated across four experiments — EXP-003A, EXP-003B-R1,
EXP-003C, GEN-001 — and implemented in production, `feature_spec.py`;
kept Provisional since the LM feature group's lack of demonstrated
value is a consistent finding, not yet acted on by dropping it)

## Date
2026-08-15

## Context

PRIMARY-DATASET-v1 (DEC-011's Strategic Decision, 425-sample manifest)
now exists. Before any detector training, EXP-003 (see
[experiments/EXP-003.md](../experiments/EXP-003.md)) needs a concrete,
non-fabricated feature set and a baseline ladder to compare the primary
model against — otherwise a complex model's apparent performance can't
be distinguished from "any simple approach would have done as well."

## Problem

1. Which of this project's IMPLEMENTED features (see
   [feature-inventory.md](../feature-inventory.md)) go into EXP-003's
   primary feature set, and which are excluded and why?
2. What baselines does the primary model need to beat, and why these
   specific ones?

## Alternatives Considered

### For feature selection

**Alternative A — Use every IMPLEMENTED feature unconditionally.**
Advantages: simplest, no judgment calls, lets the model itself decide
what matters via regularization.
Disadvantages: some IMPLEMENTED features (e.g. `punctuation_count`,
which does not normalize by sentence length) are known-crude and
including them without at least noting the limitation risks treating a
weak proxy as a validated signal.

**Alternative B (chosen) — Use every IMPLEMENTED feature, but tag each
with its known limitation from feature-inventory.md, and let EXP-003
itself report which ones show measurable separation, rather than
pre-filtering by intuition.**
Advantages: consistent with this project's standing discipline of not
inventing thresholds/decisions without evidence (DEC-006's own
precedent — "which features carry signal" is an empirical question for
EXP-002/EXP-003, not a design-time guess). Every feature that goes in
is at least already implemented and tested, not invented for this
decision.
Disadvantages: a genuinely useless feature still gets computed for this
first round; acceptable, since dropping it retroactively (DEC-006's
"Revisit When") is cheap once EXP-003 shows it has no signal.

### For baselines

**Alternative A — Compare only against a majority-class baseline.**
Advantages: simplest.
Disadvantages: doesn't answer the specific question this project
actually cares about — whether the LM instrument (DEC-004/007/008) adds
value beyond stylometry alone, which DEC-004 explicitly flagged as an
open question to test empirically ("EXP-002 'linguistic only' vs
EXP-003 'linguistic + perplexity'").

**Alternative B (chosen) — Three baselines, each isolating one
question:**
1. **Majority/random** — is there any signal at all worth measuring?
2. **Stylometric-only** (Phase 3 features, no LM) — does the
   non-LM-derived feature set alone separate the classes?
3. **LM-only** (perplexity/log-prob features, no stylometry) — does the
   LM instrument alone separate the classes, and does "low perplexity"
   actually correlate with either class (testing, not assuming, DEC-004's
   standing caution)?

Advantages: Baseline 2 vs. Baseline 3 directly answers the question
DEC-004 deferred to "EXP-002 vs EXP-003" under the project's earlier
numbering scheme; the primary (combined) model's value is then judged
against whichever baseline is strongest, not against a strawman.
Disadvantages: three baselines plus the primary model is more
experiment surface area than one, but each is cheap (interpretable
models, no tuning burden — DEC-015) and this is exactly the ablation
this project's own decisions already called for.

## Decision

**EXP-003's primary feature set is every IMPLEMENTED feature in
feature-inventory.md** (10 sentence-level + 13 essay-level stylometric
features, 5 sentence-level + 1 essay-level LM-derived features),
computed exactly as already implemented — no new feature is added for
EXP-003.

**Three baselines, defined precisely:**
1. **Baseline 1 (majority/random)**: predict the majority class from
   `train`; report what accuracy that alone achieves per class-pair
   (EXP-003A/B/C have different class balances — see EXP-003.md).
2. **Baseline 2 (stylometric-only)**: the 23 non-LM features above,
   simplest interpretable model (DEC-015).
3. **Baseline 3 (LM-only)**: the 6 LM-derived features above (mean/
   median log-prob, log-prob variance, perplexity, token count,
   predictability delta), same model class as Baseline 2.

The primary model (DEC-015) uses the full combined feature set.

## Why

This directly operationalizes DEC-004's standing, previously-unresolved
question ("does the LM instrument help beyond stylometry?") as a
concrete, three-way comparison instead of leaving it as an assertion,
and reuses only already-implemented, tested code — no fabricated
features, per explicit instruction.

## Evidence

**EXP-003A executed 2026-08-15** (see
[reports/EXP-003A.md](../../reports/EXP-003A.md)): Baseline A (majority)
50.0% validation accuracy; Baseline B (stylometric-only, 23 features)
100.0%; Baseline C (LM-only, 6 features) 79.5%; primary (combined, 29
features) 100.0%. The stylometric-vs-LM comparison this decision exists
to enable produced a clear, honestly-reported answer for this task:
stylometry alone already saturates performance, and the LM group adds
nothing measurable.

**Updated 2026-08-15 — EXP-003B-R1, EXP-003C, GEN-001 all executed**:
the same pattern held across every subsequent design — EXP-003B-R1
(sentence-level localization: genuine LM-predictability features
weakest of 5 groups tested), EXP-003C (three-class: stylometric-only
and combined tied exactly on validation), GEN-001 (LM-only degraded
under cross-generator transfer while stylometric-only/combined
transferred perfectly). This feature set is now the one frozen into
production (`backend/app/services/feature_spec.py`,
`essay_detector_v1.joblib`, `sentence_detector_v1.joblib`) — see
[production-detector.md](../production-detector.md). See DEC-004's
Evidence section for the full four-experiment record.

Originally: none yet — this is a pre-registration of the feature set
and baselines, written before EXP-003 runs, specifically so the
comparison can't be
adjusted after seeing results.

## Trade-offs

Including known-crude features (e.g. `punctuation_count`) in the
primary set risks diluting a clean signal with noise; accepted because
pre-filtering by intuition would itself be an unevidenced judgment call
this project's discipline avoids. If a feature shows no signal in
EXP-003, DEC-006's "Revisit When" already establishes the process for
dropping it.

## Consequences

Positive: every choice here is traceable to already-implemented,
already-tested code — nothing invented for this experiment.
Negative: 29 total features for a dataset of 425 essay-level samples
(fewer at sentence-level for the `ai_assisted`-vs-`human` localization
task) risks overfitting with a flexible model — this is exactly why
DEC-015 prefers simple, regularized models for this round.

## Revisit When

1. After EXP-003A/B/C run: which features show real separation (and in
   which direction — not assumed here) determines whether DEC-006's
   provisional feature set graduates to validated, and whether any
   PROPOSED feature (feature-inventory.md) becomes worth implementing.
2. If Baseline 3 (LM-only) matches or beats Baseline 2 (stylometric-only)
   or the combined model, that is a real, reportable finding about this
   project's LM instrument's value — not a result to suppress.

## Implementation

`backend/app/services/feature_spec.py` (the canonical 29-field
name/order spec, Phase B) — the frozen production artifacts
(`essay_detector_v1.joblib`, `sentence_detector_v1.joblib`) both use
exactly this feature set. Underlying feature computation:
`backend/app/services/feature_extractor.py`,
`backend/app/services/language_model.py`.

## Tests / Experiments

`backend/tests/test_feature_extractor.py`,
`backend/tests/test_language_model.py` (feature computation
correctness), `backend/tests/test_essay_feature_vector.py` /
`test_sentence_feature_vectors.py` (production feature-vector
equivalence to the research computation). Signal validation:
EXP-003A/B/B-R1/C, GEN-001 (see Evidence above).
