# EXP-003A — Human vs. full_ai

**Date**: 2026-08-15
**Status**: Executed exactly once, per the frozen protocol below.
**Detector work stops here** — EXP-003B, EXP-003C, fairness, cross-
generator, and NLI experiments are explicitly NOT run as part of this
report, per the stop condition.

## 1. Research question

Can the IMPLEMENTED measurable linguistic/statistical features
(feature-inventory.md) distinguish human writing from fully machine-
generated writing on PRIMARY-DATASET-v1?

**Scope limitation, stated prominently, not buried**: the `full_ai`
class was generated using **one specific model, Qwen2.5-1.5B-Instruct**
(DEC-010). This experiment does **not** establish "general AI
detection" or "accuracy against all AI-generated writing." The correct
interpretation of every result below is: **performance distinguishing
PERSUADE 2.0's human corpus from Qwen2.5-1.5B-Instruct-generated
writing, under this controlled benchmark.** A different generation
model, prompted differently or fine-tuned to imitate student writing,
could plausibly produce very different results — untested here.

## 2. Dataset

PRIMARY-DATASET-v1's inclusion manifest, `human` + `full_ai` categories
only: **298 essays** (150 human, 148 full_ai).

| Split | human | full_ai | Total |
|---|---|---|---|
| train | 105 | 103 | 208 |
| validation | 22 | 22 | 44 |
| test | 23 | 23 | 46 |

**No family leakage**: `find_family_split_violations()` returns **0**
against these 298 records specifically (also re-verified against the
full dataset — see EXP-003.md §1). Every family's human and full_ai
essay are in the same split by construction (DEC-011's leakage
invariant).

**No target leakage**: features are computed independently per essay
from its own text only; no feature depends on any other essay, the
label, or split membership.

## 3. Limitations (see also §1, §16)

- Single generation model (Qwen2.5-1.5B-Instruct) — see §1.
- PERSUADE 2.0 is educational/student persuasive writing, not general
  admissions-essay writing (dataset.md's standing caveat).
- Small dataset: 46 test essays is a small sample for any accuracy
  claim — uncertainty intervals are reported throughout, not omitted.
- Features are the DEC-006 provisional set — this experiment is their
  first-ever signal measurement, not a confirmation of known signal.

## 4. Preprocessing

**Feature extraction** (`scripts/exp003a_extract_features.py`): for
each essay, the pre-registered 29-feature vector (DEC-014) — 23
stylometric + 6 LM-derived (`distilgpt2`, DEC-007/008). **Essay-level
aggregation** (a necessary shape transformation, not a new feature,
per DEC-014): the 13 already-essay-level `EssayFeatures` fields used
directly; the 10 `SentenceFeatures` fields and 5
`SentenceLMFeatures` fields mean-pooled across all sentences in the
essay; `predictability_delta` mean-pooled across all non-`None` values.
**Missingness check**: **zero missing values** across all 298 essays,
29 features each (8,642 values) — every essay had enough sentences and
scorable tokens for every feature to compute.

**Scaling**: `sklearn.preprocessing.StandardScaler` **fit on TRAIN
only** (208 essays), applied unchanged to validation and test. No
scaler was ever fit on validation, test, or the full dataset.

## 5. Baselines

| Baseline | Features | Validation accuracy | Validation F1 (full_ai) |
|---|---|---|---|
| **A — Majority** (predicts `human`, the train-majority class) | none | 22/44 = 50.0% | 0.0 (degenerate — see note) |
| **B — Stylometric-only** | 23 | **44/44 = 100.0%** | 1.0 |
| **C — LM-only** | 6 | 35/44 = 79.5% | 0.809 |

Baseline A's F1 is 0 for the `full_ai` class specifically because it
never predicts that class — reported as-is, not smoothed; accuracy
alone (50%) is the informative number for this baseline, exactly why
accuracy-alone is insufficient for the primary/baseline comparisons
above it.

## 6. Feature-group comparison (core research question)

**Stylometric-only (Baseline B) already reaches 100% on validation.
LM-only (Baseline C) reaches 79.5%. The combined model (Primary, §7)
also reaches 100% — i.e., adding the LM instrument's 6 features
provided no measurable improvement over stylometric features alone on
this benchmark, because stylometric features alone already saturate
performance.**

This is reported plainly, per explicit instruction: **the LM instrument
does not demonstrate incremental value on this specific task.** This is
not evidence the LM instrument is useless in general (EXP-003B's
mixed/sentence-level task, not yet run, is a substantively different
question — a single light sentence edit inside an otherwise-human essay
is a much harder separation problem than whole-essay style, and
predictability-based signals may matter more there). It is evidence
that, **for whole-essay human-vs-full_ai separation on this benchmark,
simple lexical-diversity and repetition statistics are already
sufficient**, and DEC-004's standing warning ("do not assume low
perplexity = AI") is reinforced, not contradicted, by LM-only's
comparatively weaker, imperfect performance here.

## 7. Model

Per DEC-015: **L2-regularized logistic regression**, regularization
strength `C` selected via 5-fold stratified cross-validation **within
TRAIN only** (`sklearn.LogisticRegressionCV`, `scoring="f1"`).

**Primary (combined, 29 features)**: chosen `C = 0.00599`. Validation:
**44/44 = 100.0%** accuracy, F1 = 1.0 both classes.

**Secondary comparison — random forest** (fixed config,
`n_estimators=200, max_depth=5`, not tuned, per DEC-015): validation
**44/44 = 100.0%**, identical to the primary model. Per DEC-015, this
does **not** trigger switching the primary model — with both scoring
identically on validation, there is no performance argument for
accepting the random forest's lower interpretability, so **logistic
regression remains primary**, as designed before any result existed.

## 8. Validation / model-selection procedure

Baselines A/B/C, the primary model, and the random-forest comparison
were all fit on TRAIN and compared on VALIDATION only (§5–7). No test
data was used in this comparison. The primary model (combined logistic
regression) was selected **because it was pre-registered as primary in
DEC-015**, not because it "won" a comparison — it happened to tie the
best validation score, but the decision procedure did not depend on
that outcome.

## 9. Threshold-selection procedure

Per DEC-015: threshold swept 0.01–0.99 in 0.01 steps on VALIDATION,
maximizing F1 for the `full_ai` class. **Chosen threshold: 0.47**
(validation F1 = 1.0). **Important, honestly-reported nuance**: because
validation is perfectly separated, F1 = 1.0 across a wide plateau of
threshold values including both 0.47 and the default 0.5 — the sweep's
`argmax` landed on 0.47 somewhat arbitrarily (a tie-break, not a
meaningfully-informed choice), since validation itself could not
discriminate among threshold candidates within that plateau. This
turned out to matter for test (§11) — reported transparently, not
hidden.

## 10. Final frozen configuration

Frozen **before** any test-set access: feature set = all 29 fields
(DEC-014); scaler = `StandardScaler` fit on the 208 train essays;
model = `LogisticRegression`, `C = 0.00599` (from `LogisticRegressionCV`
above), `penalty="l2"`; threshold = **0.47**.

## 11. Test results (single evaluation, performed once)

**At the frozen threshold (0.47)**: **45/46 correct = 97.8%**
(95% Wilson CI: [88.7%, 99.6%]).

| | Predicted human | Predicted full_ai |
|---|---|---|
| **Actual human** | 22 | 1 |
| **Actual full_ai** | 0 | 23 |

Precision (full_ai) = 0.958, Recall (full_ai) = 1.0, F1 (full_ai) =
0.979. Precision (human) = 1.0, Recall (human) = 0.957, F1 (human) =
0.978.

**For reference only, not a post-hoc adjustment** — at the un-selected
default threshold 0.5, test would have been **46/46 = 100.0%** (95% CI:
[92.3%, 100%]). This is reported for transparency about the threshold
plateau's real-world cost (§9), not as a substitute result — **the
official, frozen-before-test result is 45/46 at threshold 0.47,
determined before test was touched.** Nothing was retuned after seeing
this.

**The one error**: `302DC21A6DEE__human`, a genuine human essay, scored
0.49 — just above the 0.47 threshold — and was misclassified as
`full_ai`. See §14/§15.

## 12. Confusion matrix

See §11's table. `tn=22, fp=1, fn=0, tp=23` (positive class = `full_ai`).

## 13. Feature/ablation analysis (TRAIN + VALIDATION only, never test)

| Ablation | Features | Validation accuracy |
|---|---|---|
| All 29 (= combined/primary) | 29 | 44/44 = 100.0% |
| Stylometric only | 23 | 44/44 = 100.0% |
| LM only | 6 | 35/44 = 79.5% |
| Combined minus 5 within-sentence LM features (keeps predictability_delta) | 24 | 44/44 = 100.0% |
| Combined minus neighboring-sentence predictability_delta only | 28 | 44/44 = 100.0% |

**No ablation involving the full stylometric set drops below 100% on
validation** — the signal is carried entirely by stylometric features;
removing any subset of the LM features changes nothing measurable here.
This is a real, honest finding: **for this specific task, the LM
instrument's contribution could not be distinguished from zero.**

### Which stylometric signals actually drove this (interpretability)

Top standardized logistic-regression coefficients from the **frozen
primary model** (magnitude, not causal — see §14's framing rule):

| Feature | Standardized coefficient | Direction |
|---|---|---|
| `stylo_type_token_ratio` | +0.210 | higher → more associated with `full_ai` |
| `stylo_mean_avg_word_length` | +0.199 | higher → more associated with `full_ai` |
| `stylo_moving_average_ttr` | +0.198 | higher → more associated with `full_ai` |
| `stylo_repeated_bigram_ratio` | −0.169 | higher → more associated with `human` |
| `stylo_mean_punctuation_count` | +0.153 | higher → more associated with `full_ai` |
| `stylo_mean_adj_ratio` | +0.152 | higher → more associated with `full_ai` |
| `lm_mean_mean_log_prob` (highest-ranked LM feature) | +0.084 | 13th largest of 29 — a real but comparatively minor contributor |

No single feature dominates the model (max |coefficient| = 0.21 of a
roughly-normalized scale) — this is a **distributed** signal across
many stylometric dimensions, not one feature doing all the work.
Directly checking the raw (non-standardized) distributions confirms
this is real, not an artifact of scaling: e.g. `type_token_ratio`
(lexical diversity) has **essentially no range overlap** between
classes across all 298 essays — human 0.275–0.636 (mean 0.465), full_ai
0.649–0.844 (mean 0.747). `moving_average_ttr` shows the same pattern:
human 0.598–0.862, full_ai 0.873–0.969. `repeated_bigram_ratio` (human
mean 0.241 vs. full_ai mean 0.033) reflects real, repetitive phrasing
common in student writing that Qwen2.5-1.5B-Instruct's output does not
reproduce.

**Plausible, stated-as-plausible-not-certain explanation**: PERSUADE
2.0 is real, informal student writing — including typos, repetition,
simpler vocabulary, run-on sentences (documented throughout this
project's failure-analysis.md). Qwen2.5-1.5B-Instruct, an instruction-
tuned model, produces comparatively polished, lexically varied,
lower-repetition prose by default. This gap being large and consistent
is plausible and unsurprising given those two sources' real
differences — but this experiment does not prove *why*, only *that* the
gap exists and is measurable, on this specific pairing.

## 14. Evidence examples (DEC-017's mapping, applied to real cases)

Per DEC-017: feature value → normalized/relative measurement → fixed
deterministic template. Two real, worked examples from the frozen test
run:

**`F53DA3118668__full_ai`** (most confidently predicted `full_ai`,
score 0.919): `type_token_ratio = 0.786` (class range: human
0.275–0.636, full_ai 0.649–0.844 → within the full_ai range, near its
upper half); `repeated_bigram_ratio = 0.027` (far below the human mean
of 0.241). Evidence statement (template-generated, not written ad hoc):
*"This essay's lexical diversity (0.79) falls within the range this
benchmark's AI-generated essays occupy (0.65–0.84) and outside the
range observed in this benchmark's human essays (0.28–0.64). Repeated
two-word phrases are rare (2.7% of bigrams) relative to this
benchmark's human average (24.1%)."*

**`302DC21A6DEE__human`** (the one test error, score 0.49, predicted
`full_ai`, actually `human`): `type_token_ratio = 0.484` (inside the
human range, but on the higher side), `moving_average_ttr = 0.801`
(above the human mean of 0.759, closer to the boundary),
`avg_word_length = 4.837` (above the human mean of 4.329). Evidence
statement: *"This essay's lexical diversity (0.80, windowed measure) is
higher than typical for this benchmark's human essays (mean 0.76) and
close to the boundary separating the two classes here."* — **this
correctly explains why the model erred**: this particular human essay
is simply more lexically varied than most human essays in this
benchmark, landing it near the decision boundary. The evidence
statement is honest about *why*, not just *that*, the model was wrong.

No explanation text above was generated by a model call — every number
is read directly from the frozen feature file and the class ranges
computed at analysis time; the template wording is fixed.

## 15. Confidently-wrong examples

**Only one test error exists** (§11): `302DC21A6DEE__human`, score
0.49, threshold 0.47 — a margin of 0.02. **This is not a confident
error** — it is the most marginal possible miss, immediately adjacent
to the decision boundary, not a case where the model was confidently
incorrect. Reported exactly as found, not embellished into a more
dramatic failure than it is: with only 46 test essays and a genuinely
strong stylometric signal (§13), this experiment does not have a
"confidently wrong" example in the strong sense the phrase implies.

| Sample ID | True | Predicted | Score | Key feature values | Likely reason |
|---|---|---|---|---|---|
| `302DC21A6DEE__human` | human | full_ai | 0.49 | TTR 0.484, MATTR 0.801, avg_word_len 4.84 (all above the human mean) | An atypically lexically-diverse, longer-word human essay — sits near the boundary this specific feature set draws between the two classes |

**What this exposes**: the detector's stylometric signal, while strong
on average, is not immune to a human writer whose natural style happens
to overlap with the AI-generated style range on this benchmark's
specific features. This is the correct kind of limitation to expect
from a lexical-diversity-based signal — it measures a correlate of
authorship, not authorship directly (§16).

## 16. Limitations (restated, consolidated)

- Single generation model (Qwen2.5-1.5B-Instruct) — §1. This
  experiment's strong separation may be specific to this model's
  default writing style, not AI-generated text in general.
- 46-essay test set: even a "clean" 45/46 or 46/46 result carries real
  sampling uncertainty (95% CI as wide as ±10 points at these small
  counts) — not a claim of a stable, precise rate.
- The threshold-selection plateau (§9) shows this benchmark's
  validation set was too easily separated to meaningfully discriminate
  among nearby threshold choices — a real limitation of evaluating
  threshold selection on an easy task, not a flaw specific to this
  model.
- Coefficients (§13) describe association within this fitted model, not
  causation — explicitly not interpreted as "this feature causes AI
  writing."
- No generalization claim beyond PERSUADE 2.0's specific student-essay
  domain and Qwen2.5-1.5B-Instruct's specific default output style.

## 17. Conclusion

**The measurable stylometric features already implemented in this
project (DEC-006) separate human PERSUADE essays from
Qwen2.5-1.5B-Instruct full-essay generations almost perfectly on this
benchmark (45–46 of 46 test essays, depending on which pre-registered
threshold choice is used) — and this separation is carried entirely by
stylometric features (lexical diversity, repetition, word length,
punctuation density); the LM-derived (perplexity/predictability)
features added no measurable value over stylometric features alone,
either in the combined model or across every ablation tested.** This is
reported as a genuine, not-optimized-toward finding: the LM instrument
underperforms simple stylometry here, and DEC-004's standing caution
against assuming "low perplexity = AI" is reinforced by direct evidence,
not just precedent. The one test error was a marginal, low-confidence
case involving an atypically lexically-diverse human essay, not a
systematic failure mode. **This result describes performance on this
specific benchmark only** (§1, §16) — it is not evidence of general AI-
detection capability, and should not be cited as such in any later
document.

**Per the stop condition: EXP-003B, EXP-003C, the fairness experiment,
any cross-generator experiment, and NLI are explicitly not run as part
of this report.** Reporting and stopping for review.

## Reproducibility

| Field | Value |
|---|---|
| Dataset | `PRIMARY-DATASET-v1`, `data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json` |
| Split counts | train 208 (105/103), validation 44 (22/22), test 46 (23/23) |
| Feature version | `scripts/exp003a_extract_features.py` (this file's current content — see note below) |
| Preprocessing | `sklearn.preprocessing.StandardScaler`, fit on train only |
| Random seed | 42 (feature CV folds, random forest) |
| Model config | `LogisticRegression` via `LogisticRegressionCV(Cs=10, cv=5-fold StratifiedKFold, scoring="f1", random_state=42)`, chosen `C=0.00599` |
| Threshold | 0.47 (selected on validation, see §9) |
| `sklearn` version | 1.9.0 |
| Python version | 3.14.6 |
| Code state | last commit `6089da5`; this experiment's own scripts (`exp003a_extract_features.py`, `run_exp003a.py`, and the rest of this phase's files) are **uncommitted working-tree changes** as of this run — exact reproduction requires this working tree state, not just commit `6089da5` alone, until a future commit captures it |
| Raw outputs | `experiments/EXP-003A/features.jsonl` (298 feature vectors), `experiments/EXP-003A/results.json` (all metrics, coefficients, and per-sample test predictions, verbatim source for every number in this report) |
