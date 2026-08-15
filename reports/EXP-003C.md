# EXP-003C — Three-Class (human / full_ai / ai_assisted), Essay-Level

**Date**: 2026-08-15
**Status**: Executed exactly once, per the approved protocol
(experiments/EXP-003.md §9). **Sentence-level three-class was NOT run**
— explicitly out of scope for this execution, remains deferred per the
design.

**Headline, stated up front**: **`full_ai` remains essentially perfectly
separable (23/23 test recall) even inside the three-class problem.
`ai_assisted` collapses completely — 0 of 16 test essays correctly
classified, all absorbed into `human` (15) or `full_ai` (1).** This
directly confirms and extends EXP-003B's essay-level chance-level
finding: the three-class setting does not rescue `ai_assisted`
detection — if anything, it demonstrates concretely *how* it fails
(indistinguishable from `human` by this feature set, not spread evenly
across errors). This is reported as the expected, legitimate,
informative outcome the protocol anticipated, not a disappointing
result to soften.

## 1. Research question

Can the current measurable feature set distinguish `human`, `full_ai`,
and `ai_assisted` within PRIMARY-DATASET-v1 — and specifically, where do
the three classes get confused with each other? Not run to maximize
accuracy.

## 2. Dataset composition

**PRIMARY-DATASET-v1, unmodified.** No new generation, no changes to
family assignments, splits, or the inclusion manifest.
**Dataset version**: the frozen manifest,
`data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json` (425
included samples, unchanged since approval).

**No new feature extraction**: built by merging two already-cached,
already-tested files
(`experiments/EXP-003A/features.jsonl`,
`experiments/EXP-003B/features_essay.jsonl`) via
`scripts/exp003c_merge_features.py`. The 150 `human` rows present in
both source files were verified **byte-identical** before merging (not
assumed) — see script output. Merged dataset:
`experiments/EXP-003C/features_essay.jsonl`, 425 rows, 29 columns each
(DEC-014's pre-registered feature set).

| Split | human | full_ai | ai_assisted | Total |
|---|---|---|---|---|
| train | 105 | 103 | 90 | 298 |
| validation | 22 | 22 | 21 | 65 |
| test | 23 | 23 | 16 | 62 |
| **Total** | **150** | **148** | **127** | **425** |

No class was discarded. No sample became unusable during preprocessing
— missingness check confirmed 0 missing values across all 425×29
feature values (would have stopped and reported if any were found, per
the approved protocol).

## 3. Split verification

`find_family_split_violations()` re-run against the merged 425-row
dataset: **0 violations.**

## 4. Feature groups

Same three pre-registered groups, no additions (DEC-014): stylometric-
only (23), LM-only (6), combined (29).

## 5. Model

**Multinomial L2-regularized logistic regression**
(`sklearn.LogisticRegressionCV`, native 3-class support, `penalty="l2"`,
5-fold `StratifiedKFold` on train, `scoring="f1_macro"` — the one
necessary, disclosed adaptation from DEC-015's binary procedure:
macro-F1 replaces the binary-only `"f1"` scorer, matching this
experiment's own headline metric, not a new invented criterion). Random
forest was **not** included — per DEC-015, it is a comparison "only if
already part of the approved protocol"; the approved EXP-003C protocol
(experiments/EXP-003.md §9C) named it as "available," not required for
this specific run, and it was not added here to keep this execution
strictly to the approved scope. No neural classifier, no LLM classifier.

## 6. Preprocessing

One `StandardScaler`, fit on the 298 **train** rows only, applied
unchanged to validation (65) and test (62).

## 7. Validation / model-selection procedure

All three feature groups fit on train, compared on validation only —
**test was not touched during this comparison.** The **combined**
group is the pre-registered primary model (DEC-014) — used because it
was pre-registered, not because it "won" the validation comparison
(though in this case it also matched stylometric-only's score exactly,
§9).

## 8. Baseline

**Majority-class baseline** (predicts `human`, the train-majority
class, 105/298): validation accuracy 33.8%, macro-F1 0.169. This is
the honest floor every feature group is compared against.

## 9. Frozen test results

**Decision rule**: `argmax` over the three predicted class
probabilities (no per-class threshold introduced, per the approved
protocol).

**Overall**: 45/62 correct = **72.6%** accuracy (95% Wilson CI
[60.4%, 82.1%]). **Macro-F1 = 0.564** (headline metric, per protocol).
**Weighted-F1 = 0.628.**

### Per-class metrics

| Class | Precision | Recall | F1 |
|---|---|---|---|
| `human` | 0.595 | **0.957** | 0.733 |
| `full_ai` | 0.920 | **1.000** | 0.958 |
| `ai_assisted` | **0.000** | **0.000** | **0.000** |

`ai_assisted` recall 0/16, 95% Wilson CI [0.0%, 19.4%] — genuinely,
not just numerically, zero: every one of the 16 test `ai_assisted`
essays was misclassified.

### 3×3 confusion matrix

| Actual \\ Predicted | human | full_ai | ai_assisted |
|---|---|---|---|
| **human** (23) | 22 | 1 | 0 |
| **full_ai** (23) | 0 | 23 | 0 |
| **ai_assisted** (16) | 15 | 1 | 0 |

## 10. Pairwise confusion analysis (explicit, as required)

| Pair | Count |
|---|---|
| `human` → `full_ai` | 1 |
| `human` → `ai_assisted` | **0** |
| `full_ai` → `human` | 0 |
| `full_ai` → `ai_assisted` | 0 |
| `ai_assisted` → `human` | **15** (dominant failure mode) |
| `ai_assisted` → `full_ai` | 1 |

**`human` ↔ `ai_assisted` confusion is real but asymmetric**: zero
`human` essays were mistaken for `ai_assisted`, but 15 of 16
`ai_assisted` essays were mistaken for `human`. This is not a
symmetric "these two classes look alike" problem — it specifically
means the model's decision boundary strongly favors `human` whenever a
sample isn't clearly `full_ai`-like, which is exactly what a ~90%-
unchanged-human-text sample (`ai_assisted`'s actual composition) would
produce given how the features are constructed (essay-wide means,
diluted by the ~90% unmodified content — the same explanation
EXP-003B already gave for its own essay-level chance-level result).

**`full_ai` ↔ `ai_assisted` confusion is minimal** (1 case total, both
directions combined) — `full_ai` remains cleanly separated from both
other classes.

## 11. Feature-group comparison

| Group | Features | Validation accuracy | Validation macro-F1 | Validation weighted-F1 |
|---|---|---|---|---|
| Stylometric-only | 23 | 67.7% | 0.559 | 0.568 |
| LM-only | 6 | 53.8% | 0.432 | 0.439 |
| **Combined** | 29 | 67.7% | **0.559** | 0.568 |

**Combined and stylometric-only are identical** on validation — same
accuracy, same macro-F1, same chosen regularization strength (`C`).
**Reported plainly, consistent with every prior EXP-003 result**: the
LM feature group adds no measurable value here either, extending the
pattern from EXP-003A (essay-level `full_ai`) and EXP-003B-R1 (sentence-
level `ai_assisted` localization) to this three-class essay-level
setting — the third independent confirmation of the same finding, not
a new one.

## 12. Failure analysis

**Dominant failure mode**: `ai_assisted` → `human` (15/16 cases).
Inspecting the actual predicted class probabilities (not just the
final decision) shows this is **not a confident, one-sided call** —
for most of the 15 misclassified `ai_assisted` essays, the model's
`ai_assisted` probability sits around 0.40–0.45, meaningfully above the
30.2% base rate for that class in training, and often within ~0.05–0.13
of the winning `human` probability:

| Sample | Predicted | P(human) | P(full_ai) | P(ai_assisted) |
|---|---|---|---|---|
| `2723DB12AC00` | human | 0.457 | 0.165 | 0.378 |
| `6B933220124E` | human | 0.494 | 0.060 | 0.446 |
| `ECF63F6AB48E` | human | 0.408 | 0.209 | 0.383 |

**This nuance matters**: the model is not confidently declaring these
essays human — it is picking `human` as *more likely than* `ai_assisted`
by a real but often narrow margin, in a three-way competition where
`ai_assisted`'s probability is consistently elevated above chance but
not enough to win. Stated precisely, not overstated: this is weak,
partial signal that the current decision rule (plain `argmax`, no
per-class threshold) cannot yet convert into correct classifications —
consistent with EXP-003B/B-R1's own finding that real, if imprecise,
`ai_assisted` signal exists.

**The one `full_ai` error and the one `human` error are the same
family**: `302DC21A6DEE`. Its `human` sample was predicted `full_ai`
(P(full_ai)=0.354 vs. P(human)=0.348 — an extremely narrow margin,
0.006), and its `ai_assisted` sample was predicted `full_ai` as well
(the only `ai_assisted`→`full_ai` case). **This is the same family that
was EXP-003A's one test error and among EXP-003B's essay-level errors**
— now a third, independent experiment where this specific human essay
(elevated lexical diversity, per EXP-003A §13) behaves atypically.
Flagged again, explicitly, as a property of this one essay's writing
style, not three unrelated coincidences.

**No `human`→`ai_assisted` confusion at all (0 cases)** and **no
`full_ai`↔`ai_assisted` confusion beyond the one case above** — the
failure is concentrated and specific (`ai_assisted` being absorbed into
`human`), not diffuse across all class pairs.

## 13. Evidence examples (DEC-017, applied to the three-class case)

`2723DB12AC00__sentence_light_controlled_v2` (true `ai_assisted`,
predicted `human`, P(ai_assisted)=0.378): the same essay whose
sentence-level localization was correctly flagged as `ai_assisted` in
EXP-003B/B-R1 (this sample's ID matches EXP-003B-R1 §13's "correct
catch" example). Evidence statement (template-generated, cautious
language per DEC-017): *"This essay's overall stylometric profile is
closer to this benchmark's typical human writing than to its
AI-generated writing, though the model's AI-assisted-class probability
(0.38) is elevated above the base rate for that class — the essay-level
signal was insufficient to override the human-leaning majority of its
content."* No claim of certainty; states what was measured and its
direction, nothing more.

## 14. Limitations

- **Scoped to PRIMARY-DATASET-v1**: its PERSUADE 2.0 human corpus,
  Qwen2.5-1.5B-Instruct `full_ai` data, and Qwen2.5-1.5B-Instruct
  `sentence_light_controlled_v2` `ai_assisted` data. **Not** "general
  AI detection accuracy" — precise language used throughout this report
  for exactly this reason.
- Test set is small (62 essays, as few as 16 for `ai_assisted`) — the
  95% CI on `ai_assisted` recall spans the entire plausible range
  [0%, 19.4%] at this sample size.
- Sentence-level three-class was not run — the essay-level result above
  says nothing about whether sentence-granularity features would
  perform differently (deferred per the approved protocol, §9F of
  experiments/EXP-003.md).
- `ai_assisted`'s complete collapse (0/16) is consistent with, not an
  independent confirmation beyond, EXP-003B's own essay-level chance-
  level finding — this experiment demonstrates the same underlying
  limitation in a three-way setting, not a new one.
- Per-class probability nuance (§12) is informative but should not be
  read as "the model almost got it right" in a way that understates the
  practical result: **the frozen decision rule produced 0 correct
  `ai_assisted` classifications**, and that is the number that would
  reach a user under the current, approved decision procedure.

## 15. Conclusion

**`full_ai` remains essentially perfectly detectable (23/23 test
recall) even when `ai_assisted` is added as a third, competing class —
the signal EXP-003A found is robust to this harder setting.
`ai_assisted` detection collapses completely at the essay level (0/16),
concentrated almost entirely into `ai_assisted`→`human` confusion (15
of 16 errors), not spread across all class pairs.** The LM feature
group again added no measurable value (identical to stylometric-only
on validation) — the third independent experiment to find this
(EXP-003A, EXP-003B-R1, now EXP-003C), strengthening rather than
resolving DEC-004's standing open status. Per-sample probability
analysis shows the model carries real, if weak, `ai_assisted` signal
that the plain-argmax decision rule cannot yet convert into correct
predictions — an actionable, disclosed direction for future work
(e.g. class-weighted training, a different decision rule, or more
`ai_assisted` training data), not attempted or recommended for
adoption in this report.

**Per the stop condition: GEN-001, FAIR-001, sentence-level three-class,
NLI, and cross-generator work are explicitly NOT run as part of this
report.** Reporting and stopping for review.

## Decision records

- **DEC-004** (LM instrument contribution): status **stays open**. Third
  independent data point (essay-level 3-class) showing no measurable
  LM contribution, alongside EXP-003A (essay-level binary) and
  EXP-003B-R1 (sentence-level binary). Still not treated as conclusive
  proof the LM instrument is universally useless — but the pattern is
  now consistent across three separate experimental designs.
- **DEC-014** (feature/baseline strategy): no change — the three
  pre-registered groups and majority baseline were used exactly as
  specified; no new evidence changes the feature-selection strategy
  itself.
- **DEC-015** (model/threshold strategy): no change to the decision —
  the multinomial extension and `f1_macro` scoring adaptation were
  already anticipated in the approved EXP-003C protocol, not new
  methodology requiring a status change. Noted for a future revisit:
  whether a non-argmax, class-weighted, or cost-sensitive decision rule
  should be designed for the `ai_assisted` class specifically, given
  §12's finding that real signal exists but doesn't win the plain
  argmax — **not decided or implemented here.**
- **DEC-017** (evidence mapping): no change — one additional worked
  example (§13) applied the existing template design to a three-class
  case; no new template category was needed.

## Reproducibility

| Field | Value |
|---|---|
| Dataset | `PRIMARY-DATASET-v1`, `data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json` (unmodified) |
| Source features | `experiments/EXP-003A/features.jsonl`, `experiments/EXP-003B/features_essay.jsonl` (merged, no new extraction) |
| Merge script | `scripts/exp003c_merge_features.py` |
| Modeling script | `scripts/run_exp003c.py` |
| Split counts | train 298 (105/103/90), validation 65 (22/22/21), test 62 (23/23/16) |
| Preprocessing | `StandardScaler`, fit on train only |
| Random seed | 42 |
| Model | `LogisticRegression` via `LogisticRegressionCV(Cs=10, cv=5-fold StratifiedKFold, scoring="f1_macro", random_state=42)`, multinomial, chosen `C` in `results.json` |
| Decision rule | `argmax` over predicted class probabilities |
| `sklearn` version | 1.9.0 |
| Python version | 3.14.6 |
| Raw output | `experiments/EXP-003C/features_essay.jsonl`, `experiments/EXP-003C/results.json` — verbatim source for every number in this report |
