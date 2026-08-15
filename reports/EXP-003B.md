# EXP-003B — Human vs. ai_assisted (Essay-Level + Sentence-Level Localization)

**Date**: 2026-08-15
**Status**: Executed exactly once, per the frozen protocol below.
**Detector work stops here** — EXP-003C, fairness, cross-generator, and
NLI experiments are explicitly NOT run as part of this report.

**Headline, stated up front per the explicit instruction not to bury
negative results**: **essay-level detection of `ai_assisted` essentially
fails on this benchmark (chance-level, and the frozen-threshold test
result is worse than the majority baseline). Sentence-level localization
shows real, above-chance signal, but at a steep precision cost using a
fixed decision threshold, and a moderate, noisy ranking signal when
evaluated per-essay.** Full-AI detection (EXP-003A: ~98–100% test
accuracy) does **not** transfer to this lightly-AI-assisted case — this
is the central, expected-to-be-possible negative result this experiment
exists to surface, and it is reported plainly, not minimized.

## 1. Research question

Can the detector distinguish **human** writing from **realistically
AI-assisted** writing (`sentence_light_controlled_v2`) when both
originate from the same human source essay? Evaluated as two
**separate, never-combined** questions:

**(A) Essay-level**: given a whole essay, is it `human` or does it
contain a light AI-assisted edit (`ai_assisted`)?

**(B) Sentence-level localization**: within an `ai_assisted` essay,
which specific sentence was AI-touched?

## 2. Dataset composition

PRIMARY-DATASET-v1's inclusion manifest, `human` + `ai_assisted`
categories.

**Essay-level**: 277 essays (150 human, 127 ai_assisted).

| Split | human | ai_assisted | Total |
|---|---|---|---|
| train | 105 | 90 | 195 |
| validation | 22 | 21 | 43 |
| test | 23 | 16 | 39 |

**Sentence-level (localization)**: every sentence of every included
`ai_assisted` essay, labeled via exact `modified_spans` provenance
(DEC-016) — never inferred by similarity, embeddings, difflib, or the
semantic screen. 1,707 raw sentences across 127 essays; **1,578
retained** after excluding sentences with an undefined
`predictability_delta` (§4).

| Split | human sentences | ai_assisted sentences | Total |
|---|---|---|---|
| train | 1,033 | 84 | 1,117 |
| validation | 244 | 20 | 264 |
| test | 182 | 15 | 197 |

**Note on the essay-level `ai_assisted` count (127) vs. the number of
essays actually contributing a positive-labeled sentence to
localization (119)**: 8 essays have their AI-edited sentence at
position 0 (the essay's very first sentence), which is excluded from
localization for missing-value reasons (§4) — those 8 essays still
count normally in the essay-level task (§7), only their sentence-level
target is unavailable.

**No family leakage**: `find_family_split_violations()` returns **0**
for both the essay-level and sentence-level datasets — sentence rows
inherit their essay's (and thus family's) split field directly; no
sentence was ever independently re-split.

## 3. Advantage and remaining confounds (per explicit instruction)

Because every `ai_assisted` essay is derived from a specific `human`
seed essay, this experiment removes several confounds present in
EXP-003A: topic, prompt, and most underlying content and structure are
now shared between the two classes being compared for most families —
**though not paired 1:1 in the classification itself**: `human` and
`ai_assisted` rows are still classified independently (not as matched
pairs), and only ~90% of the `ai_assisted` essay's text is literally
identical to its human source (one sentence differs). **This does not
eliminate confounding**: `ai_assisted` essays are still drawn from a
different (fresher, non-overlapping) set of 150 seeds than EXP-003A's
`full_ai`/`human` pair, and any residual seed-selection variance across
rounds is a possible, uncontrolled factor — not assumed to be zero.

## 4. Limitations

- Single generation model (Qwen2.5-1.5B-Instruct), single mechanism
  (`sentence_light_controlled_v2`) — see §18. Not evidence about
  `sentence_moderate_controlled_v2` or paragraph-level assistance,
  entirely absent from this dataset.
- **Missing-value handling (documented, not silent)**: a sentence's
  `predictability_delta` is undefined for the essay's first sentence
  (no preceding sentence). 127 such rows excluded (one per essay), plus
  2 additional sentences (the trailing sentence in 2 essays) with no
  scorable LM tokens — **129 total excluded of 1,707 raw sentences**,
  consistent with `language_model.py`'s existing "insufficient evidence,
  not a fabricated delta" philosophy (no imputation). This cost 8
  essays their only positive-labeled sentence entirely (§2).
- Small, and for the positive class very small, evaluation sets: 16–21
  `ai_assisted` essays per split for (A); 15–20 locatable positive
  sentences per split for (B)'s top-1 metric. Every rate below should
  be read with this in mind.
- Severe class imbalance at the sentence level (~8% positive) — accuracy
  alone is close to meaningless here (§9); precision/recall/F1 for the
  positive class are the metrics that matter.

## 5. Preprocessing

Same procedure as EXP-003A: `StandardScaler` fit on **train only** for
each of the two datasets (essay-level, sentence-level) independently —
two separate scalers, never mixed. No scaler ever fit on validation or
test.

## 6. Feature groups

Per DEC-014, the same pre-registered 29 features (23 stylometric + 6
LM-derived) as EXP-003A, no additions. **For the sentence-level task**,
the 10 `SentenceFeatures` + 5 `SentenceLMFeatures` + 1
`predictability_delta` fields are the sentence's own (not essay-mean-
pooled) values; the 13 `EssayFeatures` fields are the sentence's
parent essay's values (shared across every sentence in that essay,
providing essay-level context). This is the same 29-dimension
inventory at its natural per-sentence granularity — not a new feature
set — mirroring EXP-003A's own documented mean-pooling adaptation for
the essay-level task. Column names are retained verbatim from EXP-003A
for pipeline reuse; at sentence granularity `stylo_mean_*`/`lm_mean_*`
hold the sentence's own single value, not a pooled mean — noted here
explicitly so the naming isn't misread.

## 7. Model

Same model family as EXP-003A (DEC-015): L2-regularized logistic
regression (primary, `C` via 5-fold CV on train), random forest
(secondary, fixed config, comparison only). Applied independently to
the essay-level and sentence-level datasets — two separate fits, two
separate frozen configurations.

## 8. Validation / model-selection procedure

Same discipline as EXP-003A: baselines, primary, and the random-forest
comparison all fit on train, compared on validation only, for each of
the two evaluations independently. No test data used in either
comparison.

## 9. Essay-level results

### 9a. Baselines and primary (validation)

| | Features | Validation accuracy |
|---|---|---|
| Baseline A (majority, predicts `ai_assisted` — the train-majority given 90/105 split is close) | — | 51.2% (22/43) |
| Baseline B (stylometric-only) | 23 | 51.2% |
| Baseline C (LM-only) | 6 | 51.2% |
| Primary (combined) | 29 | 53.5% (23/43) |
| Secondary (random forest) | 29 | 48.8% |

**Every feature group performs at essentially chance level (majority
baseline: 51.2%)** — the single light sentence edit does not shift
whole-essay aggregate stylometrics enough to be detectable this way, by
any feature group tested. This is expected, in hindsight: ~90%+ of an
`ai_assisted` essay's text is unmodified original human writing: any
essay-wide mean is dominated by the unchanged majority of sentences.

### 9b. Threshold selection

Swept 0.01–0.99 on validation, argmax F1. **Chosen: 0.34** (validation
F1 = 0.667) — but this number should be read with real skepticism: at
0.34, the model predicts `ai_assisted` for 21 of 22 validation `human`
essays too (confusion matrix: tn=1, fp=21, fn=0, tp=21) — **a degenerate,
near-always-positive rule**, not a meaningful decision boundary. This is
what F1-argmax optimization produces when the underlying validation
signal is close to chance: it finds the threshold that trades away
almost all specificity for recall, because with no real separating
signal, that is one of the ways to maximize F1 on an imbalanced-toward-
the-minority-class validation fold. **Reported honestly as a limitation
of applying this threshold-selection procedure to a near-chance
problem, not hidden or re-selected after the fact.**

### 9c. Frozen test result

**At the frozen threshold (0.34): 18/39 = 46.2%** — **worse than the
majority baseline (23/39 = 59.0%)**, a direct consequence of §9b's
degenerate threshold. Confusion matrix: tn=3, fp=20, fn=1, tp=15.

**For reference only** (not the official result, not a retroactive
substitution): at the unselected default 0.5, test accuracy would have
been 25/39 = 64.1% — still weak, but notably better than the frozen
result, illustrating concretely how much a bad-but-honestly-arrived-at
threshold choice can cost on a low-signal task.

**Conclusion for (A): essay-level detection of light, single-sentence
AI assistance does not work on this benchmark with these features.**
This is the correct, most informative use of this experiment's design —
discovering a real negative result, not a flaw to explain away.

## 10. Sentence-level localization results

### 10a. Baselines and primary (validation, at default threshold 0.5)

| | Accuracy | Precision (ai_assisted) | Recall (ai_assisted) | F1 (ai_assisted) |
|---|---|---|---|---|
| Baseline A (majority = human) | 92.4% (244/264) | 0.0 | 0.0 | 0.0 |
| Baseline B (stylometric-only) | 92.4% | 0.0 | 0.0 | 0.0 |
| Baseline C (LM-only) | 92.4% | 0.0 | 0.0 | 0.0 |
| Primary (combined) | 92.0% | 0.0 | 0.0 | 0.0 |
| Secondary (random forest) | 92.4% | 0.0 | 0.0 | 0.0 |

**At the default 0.5 threshold, every feature group predicts `human`
for essentially every sentence** — with only ~8% positive prevalence,
0.5 is far too conservative a bar; this table is reported for
completeness but is **not informative** about whether real signal
exists (see §10b–c, which show it does).

### 10b. Threshold selection

Swept 0.01–0.99 on validation, argmax F1. **Chosen: 0.06** (a much
lower threshold than EXP-003A's 0.47 or (A)'s 0.34 — expected, given
the ~8% positive prevalence here). Validation at this threshold: 16/20
true positives caught (80% recall), but at real precision cost (15.8%
precision, 85 false positives among 244 negatives).

### 10c. Frozen test result

**At the frozen threshold (0.06): 13/15 true positives caught (86.7%
recall), 17.6% precision (61 false positives among 182 negatives), F1 =
0.292.** Confusion matrix: tn=121, fp=61, fn=2, tp=13.

**For reference**: at 0.5, test accuracy is a misleadingly high 92.9%
(183/197 correct) but recall collapses to 26.7% (4/15 caught) — this
is the class-imbalance trap the threshold-selection step exists to
avoid, and here it worked as intended: the frozen, lower threshold
trades a large number of false positives for catching most of the real
positives, which — depending on the product's actual precision/recall
preference (evaluation.md's still-unresolved question) — may or may not
be the right trade-off, but it is a **real, above-chance signal**, not
noise: 86.7% recall from a feature set that has no access to which
sentence was touched is meaningfully better than the ~8% a random guess
would catch.

### 10d. Per-essay ranking metric (top-1 localization)

Added this round specifically to address "do not let essays with more
sentences silently dominate the aggregate" (per explicit instruction):
within each essay's sentences, does the model's single highest-scored
sentence match the true AI-touched one?

| Split | Essays with a locatable positive sentence | Top-1 correct | Top-1 accuracy |
|---|---|---|---|
| validation | 20 | 5 | 25.0% |
| test | 15 | 9 | **60.0%** |

**Both rates are well above the ~7–8% a uniform-random guess would
achieve** (essays average roughly 12–13 sentences), but the two splits
disagree substantially (25% vs. 60%) — with only 15–20 essays per
split, this is a real, honestly-reported instability, not a stable,
precise rate. Directionally, this supports the same conclusion as
§10c: the model carries real, non-trivial ranking signal about which
sentence is most likely AI-touched, even though it cannot yet do so
with high confidence or precision at a fixed threshold.

## 11. Feature ablation (train + validation only)

**Essay-level**:

| Ablation | Validation accuracy |
|---|---|
| All 29 | 53.5% |
| Stylometric only | 51.2% |
| LM only | 51.2% |
| Combined minus 5 within-sentence LM features | 51.2% |
| Combined minus predictability_delta only | 48.8% |

All within a few points of the 51.2% majority baseline — **no feature
group shows a real signal at the essay level**; differences here are
noise on an unlearnable-with-these-features problem, not meaningful
ablation findings.

**Sentence-level**: at the default 0.5 threshold, every ablation
collapses to the same all-negative behavior as §10a (0.0 recall/F1 for
every group) — **this specific comparison is uninformative at this
threshold**, for the same class-imbalance reason noted in §10a. A
threshold-swept per-ablation comparison (mirroring §10b's procedure for
each feature subset) was **not** run this round — noted as a real gap,
not silently skipped: the single frozen primary model's own threshold-
sweep (§10b–d) is the informative result this round produced for
"does signal exist," while "which specific feature subset drives it"
at the sentence level remains an open question for a future round.

## 12. Interpretability (standardized coefficients)

**Essay-level** (max |coefficient| = 0.37) — given §9's near-chance
performance, these coefficients describe a model that is not actually
separating the classes well; listed for completeness, **not
interpreted as a real signal**: `sentence_length_mean`/`mean_word_count`
(+0.37), `lm_mean_token_count` (−0.36), `type_token_ratio` (+0.27).

**Sentence-level** (max |coefficient| = 2.83, notably larger scale than
either EXP-003A or (A) above — a sign of a model fit against a much
smaller positive-class sample, 84 training examples, and prone to
higher-variance coefficient estimates): dominated by **length/count-
related features** — `lm_mean_token_count` (−2.83), `stylo_mean_char_count`
(+2.42), `lm_mean_perplexity` (−1.70), `sentence_length_std` (−1.27),
`sentence_length_mean` (+1.16). **Caution, stated explicitly**: this
looks like a comparatively surface-level signal (the AI-edited
sentence's length/token-count relative to the essay's other sentences)
rather than EXP-003A's broader lexical-diversity signal — plausible
given the light-edit mechanism's length-ratio QC bounds ([0.7, 1.3])
still permit real length shifts, and a single sentence's length
relative to its neighbors is an easier statistical regularity to latch
onto with only 84 positive training examples than a subtler stylistic
signal would be. Not interpreted as "AI writing is measurably shorter/
longer" in general — only as what this specific fitted model, on this
specific small sample, weighted most.

## 13. Evidence examples (DEC-017)

**Sentence-level, a correct catch** (`2723DB12AC00__sentence_light_controlled_v2`,
sentence index 4, score 0.204 ≥ threshold 0.06): flagged correctly.
Evidence statement (template-generated): *"This sentence's length and
token-count measures differ from the pattern typical of this essay's
other sentences, exceeding this benchmark's decision threshold for
flagging."* — deliberately cautious phrasing per explicit instruction:
**not** "AI wrote this sentence," only what was actually measured.

**Sentence-level, a miss** (`7185FB63F21B__sentence_light_controlled_v2`,
sentence index 11, score 0.030, well below threshold 0.06): the true
AI-touched sentence scored low — i.e., on this specific sentence, the
implemented features found nothing unusual relative to its essay's
other sentences. Evidence statement: *"No measured feature for this
sentence exceeded this benchmark's flagging threshold; the model found
it statistically unremarkable relative to its context."* — an honest
statement of absence-of-evidence, not a claim the sentence is
definitely human.

## 14. Confidently-wrong examples

**Essay-level**: 21 of 39 test essays were misclassified at the frozen
(degenerate, §9b) threshold — too many, and too close to a coin flip,
for "confidently wrong" to be a meaningful category here; per explicit
instruction, not calling borderline/near-random cases "confidently
wrong." The three furthest from the threshold (all human essays
predicted `ai_assisted`, scores 0.53–0.58): `302DC21A6DEE__human`
(0.58), `ECF63F6AB48E__human` (0.56), `9662807AD672__human` (0.53) —
still fairly close to the boundary in absolute terms (max margin 0.24),
not strongly confident errors.

**Notable cross-experiment observation**: `302DC21A6DEE__human` is
**also** EXP-003A's one test error (predicted `full_ai` there). The
same human essay reads as atypical (elevated lexical diversity, §12's
EXP-003A findings) across two independent experiments — worth flagging
as a property of this specific essay, not two unrelated coincidences.

**Sentence-level**: 2 missed positives, 61 false positives at the
frozen threshold. Given the volume of false positives at this
deliberately low, recall-favoring threshold, they are not individually
itemized here as "confidently wrong" — a false positive at threshold
0.06 with a score of, say, 0.07 is a marginal call, not a confident one.
The 2 missed positives are more informative: both scored **very** low
(§13's example scored 0.030), suggesting these are essays where the
light edit was, in this benchmark's own terms, unusually well-blended
— consistent with EXP-DATA-001-R3's own finding that
`sentence_light_controlled_v2` achieves strong semantic preservation
specifically because the edits are subtle.

## 15. Comparison with EXP-003A (descriptive, not combined into one number)

1. **Which features worked for full_ai (A)?** Stylometric features
   (lexical diversity, repetition, word length) — strong, clean,
   near-perfect separation.
2. **Which features worked for ai_assisted (B)?** At the essay level:
   none, meaningfully. At the sentence level: a weaker, length/token-
   count-leaning signal recovers real but imprecise localization
   ability.
3. **Did LM-derived features become more useful in B?** No — if
   anything, `lm_mean_token_count` (arguably more a length proxy than
   a genuine LM-instrument signal) is the top sentence-level
   coefficient, but the LM-only baseline showed no advantage over
   stylometric-only at any point in either experiment.
4. **Did performance collapse when human and ai_assisted text shared
   the same source essay?** Yes, dramatically, at the essay level —
   from ~98–100% (A) to chance level (B's essay task). This is the
   central, expected-to-be-discoverable finding of this experiment.
5. **Did sentence localization perform substantially worse than essay
   classification?** Differently, not simply "worse" — essay
   classification in (B) failed outright (chance level); sentence
   localization, on the *harder-sounding* task of finding one sentence
   among ~13, actually shows *more* real signal (86.7% recall, 60%
   top-1 accuracy on test) than essay-level classification did in (B).
   This is a genuinely interesting, non-obvious finding: the aggregate
   essay signal is washed out, but a targeted, sentence-level, in-
   context comparison recovers real information the essay-level
   aggregate destroys.
6. **Which errors were unique to ai_assisted writing?** Essay-level (B)
   errors are dominated by false positives (human essays flagged as
   ai_assisted) at the frozen threshold — a different error profile
   than EXP-003A's single, marginal false positive.

## 16. Conclusion

**Full-AI detection (EXP-003A) does not transfer to lightly AI-assisted
writing at the essay level — this benchmark shows chance-level
performance there, and the frozen threshold-selection procedure,
applied honestly to a low-signal problem, produced a result worse than
simply guessing the majority class.** This is reported as a real,
important negative finding, not a flaw in the experiment.

**Sentence-level localization tells a more encouraging, still limited
story**: real, above-chance signal exists (86.7% test recall at a
validation-selected threshold; 60% top-1 per-essay ranking accuracy on
test, though noisy against validation's 25%), but at a steep precision
cost (17.6%) that would need substantial improvement — better features,
more training data, or a different modeling approach — before this
could be presented to a user as a confident, low-false-positive
localization signal. **The signal that does exist leans on sentence
length/token-count relative to an essay's other sentences**, a more
surface-level regularity than EXP-003A's broad lexical-diversity
finding — worth investigating further, not yet a robust explanation.

**This result is scoped to one generation model
(Qwen2.5-1.5B-Instruct), one mechanism (`sentence_light_controlled_v2`),
and this specific benchmark** — see §18. It does not establish
universal AI-assisted-writing detection or localization capability.

**Per the stop condition: EXP-003C, the fairness experiment, any
cross-generator/external-generator evaluation, and production
optimization are explicitly not run as part of this report.** Reporting
and stopping for review.

## Reproducibility

| Field | Value |
|---|---|
| Dataset | `PRIMARY-DATASET-v1`, `data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json` |
| Essay-level split counts | train 195 (105/90), validation 43 (22/21), test 39 (23/16) |
| Sentence-level split counts | train 1,117 (1,033/84), validation 264 (244/20), test 197 (182/15) |
| Missing-value handling | 129/1,707 sentences excluded (undefined `predictability_delta`); 8 essays lost their positive sentence-level label entirely — see §4 |
| Feature extraction | `scripts/exp003b_extract_features.py` |
| Modeling | `scripts/run_exp003b.py` (imports EXP-003A's `run_exp003a.py` fitting/metric utilities directly, no duplicated logic) |
| Preprocessing | Two independent `StandardScaler`s (essay-level, sentence-level), each fit on that dataset's train split only |
| Random seed | 42 |
| Model config | `LogisticRegression` via `LogisticRegressionCV(Cs=10, cv=5-fold StratifiedKFold, scoring="f1", random_state=42)`, fit independently for essay-level (chosen `C` in results.json) and sentence-level (chosen `C` in results.json) |
| Thresholds | Essay-level: 0.34 (validation argmax F1 — see §9b's honesty note about its degeneracy). Sentence-level: 0.06 (validation argmax F1). **Neither reuses EXP-003A's 0.47.** |
| `sklearn` version | 1.9.0 |
| Python version | 3.14.6 |
| Code state | uncommitted working-tree changes as of this run, same caveat as EXP-003A |
| Raw outputs | `experiments/EXP-003B/features_essay.jsonl`, `experiments/EXP-003B/features_sentence.jsonl`, `experiments/EXP-003B/results.json` — verbatim source for every number in this report |
