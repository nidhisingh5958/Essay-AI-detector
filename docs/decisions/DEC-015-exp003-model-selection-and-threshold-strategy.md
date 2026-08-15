# DEC-015 — EXP-003 Primary Model Selection and Threshold-Selection Strategy

## Status
Provisional (validated by EXP-003A/B/C and GEN-001, frozen into
production — see [production-detector.md](../production-detector.md);
kept Provisional per the degenerate-threshold risk documented below,
not yet resolved)

## Date
2026-08-15

## Context

PRIMARY-DATASET-v1 is frozen at 425 samples (150 human / 148 full_ai /
127 ai_assisted). This is a small dataset by machine-learning standards.
A model choice and a threshold-selection procedure both need to be fixed
**before** any training happens, so the choice can't be adjusted
reactively based on which model happens to score best on data it
shouldn't have seen yet (test-set freeze, DEC problem below).

## Problem

1. What model class(es) should EXP-003 train, and why?
2. How is a decision threshold (or, for multiclass, a decision rule)
   selected, and from which split?

## Alternatives Considered

### Model class

**Alternative A — Deep neural network (e.g. a small transformer
classifier head over the features, or fine-tuning).**
Advantages: highest theoretical capacity.
Disadvantages: 425 samples (fewer per class, fewer still per split) is
far too small to train a deep model without severe overfitting risk;
uninterpretable relative to this project's core requirement (Section
14/the brief: evidence must map to actual measured features, not an
opaque score) — rejected for this round.

**Alternative B — Gradient boosting / random forest (ensemble tree
methods).**
Advantages: handles nonlinear feature interactions, reasonably
interpretable via feature importances, robust to feature scale.
Disadvantages: more hyperparameters to (potentially) overfit against
validation with this little data; feature importances are a coarser
explanation primitive than a linear model's coefficients for the
evidence-mapping requirement (DEC-017).

**Alternative C (chosen as primary) — Regularized logistic regression
(L2, and L1 as a comparison for sparsity/feature selection).**
Advantages: directly interpretable (a coefficient per feature, sign and
magnitude both meaningful — exactly what DEC-017's evidence mapping
needs); well-behaved with small n; regularization strength itself is a
single, well-understood knob tuned only on train+validation (not test);
a natural, standard first model for a small tabular dataset.
Disadvantages: cannot capture nonlinear feature interactions a tree
ensemble might; if EXP-003 shows real nonlinear structure the linear
model misses, that's a finding to report, not a reason to switch models
mid-experiment.

**Alternative D — Shallow decision tree.**
Advantages: maximally interpretable (a readable rule path).
Disadvantages: high variance on small datasets (a single tree can flip
substantially with small data changes); less standard for the confidence
score this project's evidence-strength framing needs
(feature-inventory.md; DEC-016).

**Decision: Alternative C (regularized logistic regression) as the
primary model.** Alternative B (a single random-forest configuration,
not tuned as a primary path) is trained as a secondary comparison point
alongside the primary model — using **train + validation only**, same
as the primary model — specifically to check whether nonlinear
structure exists that the linear model misses. It is not itself a
baseline (DEC-014) and is not automatically preferred if it scores
higher; per Trade-offs below, interpretability is weighed explicitly,
not just accuracy.

### Threshold/decision-rule selection

**Alternative A — Select the threshold that maximizes an aggregate
metric (e.g. F1) on the test set directly.**
Rejected outright — this is test-set leakage by definition (using test
to choose a model parameter), explicitly forbidden by the review
instruction and this project's own test-set-freeze protocol (DEC-016 —
wait, see below, this is actually part of this same decision).

**Alternative B (chosen) — Select threshold/decision rule using
validation only, after the model is fit on train, then freeze it before
touching test.**
Advantages: the standard, leakage-safe procedure; matches the explicit
train → validation → freeze → test protocol now mandated for this
project (see EXP-003.md's test-set-freeze section).
Disadvantages: with only 65 validation samples (22 families ×
categories present), the threshold choice itself has meaningful
sampling noise — acknowledged as a limitation of this dataset's size,
not hidden.

## Decision

**Primary model: L2-regularized logistic regression** (`scikit-learn`
`LogisticRegression`), regularization strength selected via
cross-validation **within train** (e.g. `LogisticRegressionCV`, or an
explicit train-internal k-fold — decided at implementation time, not
here) — validation is reserved for threshold/decision-rule selection
and model comparison, not hyperparameter search, to avoid re-using it
for two different purposes without accounting for that.

**Secondary comparison model: random forest** (fixed, reasonable
default configuration — not tuned to avoid consuming validation budget
on a model that is not the primary path), trained on the same
train/validation split, for the nonlinearity check described above.

**Threshold/decision rule**: fit on train, selected on validation,
frozen before any test-set evaluation. For EXP-003A/B (binary), this
means a probability threshold (default 0.5 unless validation shows a
better precision/recall trade-off is warranted for this project's
stated preference — see evaluation.md's precision/recall discussion,
itself not yet resolved and out of scope to resolve here). For EXP-003C
(three-class), the decision rule is `argmax` over calibrated class
probabilities unless validation shows a reason to do otherwise.

**No model is chosen based on test-set performance**, per the explicit
stop condition and the test-set-freeze protocol (EXP-003.md).

## Why

Logistic regression is the model whose interpretability most directly
serves DEC-017's evidence-mapping requirement (a coefficient is already
a "how much and in which direction" statement), is well-suited to this
dataset's small size, and is the standard, unsurprising first choice —
consistent with the explicit instruction to prefer lightweight,
interpretable models and not default to complexity.

## Evidence

**EXP-003A executed 2026-08-15** (see
[reports/EXP-003A.md](../../reports/EXP-003A.md)): the primary
(logistic regression, `C=0.00599` via 5-fold CV on train) and the
random-forest comparison scored identically on validation (100.0%
each) — exactly the tie case this decision's Trade-offs section
anticipated, and it resolved as designed: no switch, since there was no
performance argument to weigh against interpretability. Threshold
selection (sweep on validation, argmax F1) landed on 0.47 largely by an
arbitrary tie-break, since validation's perfect separation made many
threshold values score identically — a real, disclosed limitation of
selecting a threshold from an easily-separated validation set. The
frozen threshold's test result (45/46) differed from what the
unselected default 0.5 would have given (46/46) — reported
transparently in EXP-003A rather than treated as grounds to revisit
the frozen choice after the fact.

**EXP-003B executed 2026-08-15** (see
[reports/EXP-003B.md](../../reports/EXP-003B.md)) surfaces a sharper,
important instance of the same threshold-plateau risk noted above, this
time on a genuinely low-signal problem rather than an easily-separated
one: the essay-level task's validation set was near chance-level for
every feature group (~51%), and the argmax-F1 threshold sweep landed on
0.34 — a **degenerate, near-always-predict-positive rule** (21 of 22
validation `human` essays misclassified at that threshold). The frozen
test result (46.2%) was **worse than the majority baseline (59.0%)** as
a direct, disclosed consequence. This was reported honestly in
EXP-003B rather than hidden or the threshold quietly re-picked — the
procedure did exactly what it was designed to do (freeze before test,
never touch test to pick a better number), and the resulting bad number
is real, disclosed information about this task's actual difficulty, not
a bug in the procedure. The sentence-level localization task's
threshold (0.06) behaved more sensibly — genuine signal existed there
(EXP-003B §10) for the sweep to find.

## Trade-offs

If the random-forest comparison scores meaningfully higher than logistic
regression on validation, this decision does not automatically switch
primary models — the trade-off between accuracy and interpretability is
made explicitly and documented at that point, not silently resolved by
picking whichever number is higher.

## Consequences

Positive: threshold/model selection process is fully specified before
any number exists, closing off the possibility of post-hoc rationalized
choices.
Negative: with 425 samples split three ways, both the CV-based
hyperparameter selection and the validation-based threshold selection
have real sampling variance — flagged as a standing limitation, not
resolved by this decision.

## Revisit When

1. After EXP-003A/B/C run with the frozen procedure above: if logistic
   regression underperforms the random-forest comparison by a
   meaningful, reportable margin, revisit whether interpretability is
   worth the accuracy cost, with real numbers instead of a hypothetical.
2. If PRIMARY-DATASET-v1 is superseded by a larger v2 (per its freeze
   policy), reconsider whether more data justifies a higher-capacity
   model.
3. **New, from EXP-003B's essay-level result**: consider whether future
   threshold selection should include a validation-signal-strength
   check (e.g. only trust the argmax-F1 threshold if validation
   performance clears the majority baseline by some margin; otherwise
   report the default threshold as primary and flag the task as
   low-signal) — **not adopted now**, since deciding this reactively
   after seeing EXP-003B's specific bad number would itself be exactly
   the kind of after-the-fact procedure change this project's discipline
   avoids. Flagged for deliberate design before EXP-003C, not decided
   here.

## Implementation

`scripts/build_essay_detector_artifact.py` /
`build_sentence_detector_artifact.py` (Phase B/C) — deterministically
reproduce (not retrain) EXP-003A's/EXP-003B's frozen
`LogisticRegressionCV` fits and serialize them for production use
(`backend/app/services/detector.py`). The essay-level frozen threshold
(0.47) is used exactly as selected; the sentence-level model is used in
ranking mode only, explicitly never via its own degenerate raw
threshold (0.34) — see [production-detector.md](../production-detector.md).

## Tests / Experiments

`scripts/run_exp003a.py` / `run_exp003b.py` / `run_exp003c.py` (the
original model-fitting/threshold-selection runs);
`backend/tests/test_detector.py` (production reproduction: refit
`chosen_C` and every frozen test-sample score match the recorded
research results exactly, within `5e-5`).
