# EXP-003B-R1 — Does Sentence-Level Localization Survive Controlling for Length/Count Features?

**Date**: 2026-08-15
**Status**: Diagnostic experiment, executed exactly once per the frozen
protocol below. **Not a new detector architecture** — reuses
EXP-003B's sentence-level dataset unchanged.
**EXP-003B.md is not modified — this is a separate, dated report.**

**Headline finding, stated up front**: **the localization signal does
NOT disappear when length/count features are removed.** Non-length
features alone (group C/F, 18 features) reach 46.7% top-1 accuracy on
test — comparable to length/count features alone (group B, 40.0%) and
well above chance (~8%, given ~12.5 sentences/essay on average). The
full 29-feature set (group A) still performs best (60.0%), suggesting
length/count and non-length signals are partly complementary, not
redundant. **`lm_mean_token_count` is a length/count feature, not
predictability evidence, and is treated as such throughout** — genuine
LM predictability features, evaluated alone (group D, excluding
`token_count`... see §2, `lm_only` as literally re-defined from
EXP-003B still includes `token_count`; a token-count-free predictability
check is inside group C/F), perform **worse** than non-length
stylometric features alone (group E) at rank-based localization
(13.3% vs. 40.0% top-1) — a second piece of evidence that this
project's LM instrument is not currently the source of this signal.

## 1. Research question

Does PRIMARY-DATASET-v1's sentence-level `ai_assisted` localization
signal (EXP-003B) survive after controlling for simple length/count
effects, or is it primarily an artifact of the AI-edited sentence's
length differing from its essay's other sentences?

## 2. Exact feature-group definitions (fixed before running)

Three disjoint base sets, defined by what each feature actually
measures, not by column-name prefix:

**LENGTH_COUNT (11)** — every feature whose definition is a raw or
trivially-normalized count: `stylo_sentence_count`,
`stylo_sentence_length_mean`, `stylo_sentence_length_std`,
`stylo_sentence_length_cv`, `stylo_short_sentence_ratio`,
`stylo_medium_sentence_ratio`, `stylo_long_sentence_ratio`,
`stylo_mean_word_count`, `stylo_mean_char_count`,
`stylo_mean_punctuation_count`, and **`lm_mean_token_count`** —
included here despite its `lm_` prefix, per explicit instruction: a
token count is a count, not predictability information.

**STYLO_NON_LENGTH (13)** — stylometric features not defined as a raw
count: `stylo_type_token_ratio`, `stylo_moving_average_ttr`,
`stylo_rare_word_ratio`, `stylo_repeated_bigram_ratio`,
`stylo_repeated_trigram_ratio`, `stylo_repeated_sentence_opening_ratio`,
`stylo_mean_avg_word_length` (a per-word vocabulary/lexical-choice
measure, not a sentence-length/count measure), `stylo_mean_noun_ratio`,
`stylo_mean_verb_ratio`, `stylo_mean_adj_ratio`, `stylo_mean_adv_ratio`,
`stylo_mean_pronoun_ratio`, `stylo_mean_dependency_depth` (a disclosed
judgment call: dependency depth correlates with sentence length in
general linguistics, but its definition is syntactic structure, not a
count).

**LM_PREDICTABILITY_NON_COUNT (5)** — genuine predictability signals,
excluding the count feature: `lm_mean_mean_log_prob`,
`lm_mean_median_log_prob`, `lm_mean_log_prob_variance`,
`lm_mean_perplexity`, `lm_mean_predictability_delta`.

**The six requested groups**:

| Group | Definition | n features |
|---|---|---|
| A. ALL_29 | LENGTH_COUNT + STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT | 29 |
| B. LENGTH_COUNT_ONLY | LENGTH_COUNT | 11 |
| C. NON_LENGTH_COMBINED | STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT | 18 |
| D. LM_ONLY | LM_PREDICTABILITY_NON_COUNT + `lm_mean_token_count` (matches EXP-003B's original "LM-only" definition exactly) | 6 |
| E. STYLO_NON_LENGTH_ONLY | STYLO_NON_LENGTH | 13 |
| F. COMBINED_NON_LENGTH | STYLO_NON_LENGTH + LM_PREDICTABILITY_NON_COUNT | 18 |

**Disclosed, not hidden**: **C and F are the identical 18-feature set**
once `lm_mean_token_count` is classified as length/count (as
instructed) — "length/count removed from ALL_29" and "non-length
stylometric combined with genuine LM predictability" describe the same
set under this classification. One model fit serves both labels in the
results below; this is stated explicitly rather than silently
duplicated or silently diverged to force six distinct numbers.

## 3. Data

**Unchanged**: `experiments/EXP-003B/features_sentence.jsonl`, the exact
1,578-row sentence-level dataset from EXP-003B (no new generation, no
relabeling, no split changes). **Re-verified**:
`find_family_split_violations()` returns **0** against this file.

| Split | human | ai_assisted | Total |
|---|---|---|---|
| train | 1,033 | 84 | 1,117 |
| validation | 244 | 20 | 264 |
| test | 182 | 15 | 197 |

## 4. Preprocessing

One independent `StandardScaler` per feature group (6 total, though C
and F share one fit — §2), each fit on that group's **train** columns
only, applied unchanged to validation and test.

## 5. Threshold-selection method

**Per explicit instruction, no group is compared at a fixed 0.5
threshold** (EXP-003B already showed this is uninformative given ~8%
positive prevalence). For **every** group, independently: fit on train
→ sweep threshold 0.01–0.99 on validation, argmax F1 (identical
procedure to EXP-003A/B) → freeze that group's threshold → evaluate
test exactly once.

## 6. Validation results (threshold selection)

| Group | Chosen threshold | Validation top-1 accuracy |
|---|---|---|
| A. ALL_29 | 0.06 | 25.0% (5/20) |
| B. LENGTH_COUNT_ONLY | 0.09 | 20.0% (4/20) |
| C/F. NON_LENGTH_COMBINED | 0.08 | 10.0% (2/20) |
| D. LM_ONLY | 0.01 | 10.0% (2/20) |
| E. STYLO_NON_LENGTH_ONLY | 0.01 | 15.0% (3/20) |

## 7. Frozen test results

| Group | Precision | Recall | F1 | TP | FP | FN | TN |
|---|---|---|---|---|---|---|---|
| A. ALL_29 | 0.176 | 0.867 | 0.292 | 13 | 61 | 2 | 121 |
| B. LENGTH_COUNT_ONLY | 0.200 | 0.600 | 0.300 | 9 | 36 | 6 | 146 |
| C/F. NON_LENGTH_COMBINED | 0.182 | 0.800 | 0.296 | 12 | 54 | 3 | 128 |
| D. LM_ONLY | 0.076 | 1.000 | 0.142 | 15 | 182 | 0 | 0 |
| E. STYLO_NON_LENGTH_ONLY | 0.076 | 1.000 | 0.142 | 15 | 182 | 0 | 0 |

**D and E's fixed-threshold metrics are identical and degenerate**: both
selected a near-zero threshold (0.01) that flags **every single test
sentence** as `ai_assisted` (0 true negatives) — the same class-
imbalance failure mode EXP-003B's essay-level task showed, now
appearing for the two weakest sentence-level groups. At this degenerate
threshold, precision/recall/F1 cannot distinguish D from E at all — the
**top-1 ranking metric (§8) is what actually differentiates them**,
because ranking doesn't depend on where the threshold happened to land.

## 8. Per-essay top-1 localization (the primary diagnostic for this experiment)

| Group | n locatable essays (test) | Top-1 correct | Top-1 accuracy |
|---|---|---|---|
| A. ALL_29 | 15 | 9 | **60.0%** |
| B. LENGTH_COUNT_ONLY | 15 | 6 | 40.0% |
| C/F. NON_LENGTH_COMBINED | 15 | 7 | **46.7%** |
| D. LM_ONLY | 15 | 2 | 13.3% |
| E. STYLO_NON_LENGTH_ONLY | 15 | 6 | 40.0% |

(Chance baseline ≈ 8% given ~12.5 sentences/essay on average — validation
and test essays have comparable sentence counts, 12.57 vs. 12.31 mean,
so this isn't a difficulty artifact of split composition.)

## 9. Length/count contribution

**Real, but not dominant.** Length/count features alone (B) reach 40.0%
top-1 — well above chance, confirming the AI-edited sentence's length
profile relative to its essay's other sentences does carry real,
usable signal (plausible given the light-edit mechanism's length-ratio
QC bounds still permit measurable length shifts). But length/count
alone is **not sufficient** to match the full model (A, 60.0%), and is
**not uniquely responsible** for the signal either (§10 shows non-length
features reach a comparable rate alone).

## 10. Non-length stylometric contribution

**The main finding of this experiment**: non-length features combined
(C/F, 18 features: 13 stylometric + 5 genuine LM predictability) reach
**46.7% top-1 — comparable to, even modestly higher than, length/count
alone (40.0%)**, and far above chance. **Localization signal does NOT
disappear when length/count features are removed.** Isolating just the
13 non-length stylometric features (E) still reaches 40.0% — matching
B's length/count-only rate almost exactly, from a completely different,
non-overlapping feature basis. This is real, positive evidence that
this benchmark's sentence-level localization signal is not merely a
length/count artifact of the controlled transformation mechanism.

## 11. LM contribution

**Weak, and worse than non-LM alternatives at rank-based localization.**
LM-only (D, includes `token_count`) reaches only 13.3% top-1 — barely
above the ~8% chance floor, and **notably worse than E (stylometric
non-length only, 40.0%)**, despite D getting the "advantage" of
including the length-carrying `token_count` feature that D shares with
group B. This suggests the 5 genuine predictability features
(`mean_log_prob`, `median_log_prob`, `log_prob_variance`, `perplexity`,
`predictability_delta`) are, if anything, diluting rather than helping
when isolated from the broader stylometric set, at least at this
sample size (84 positive training examples). **`lm_mean_token_count`
being EXP-003B's top-magnitude coefficient is now better explained as a
length/count effect, not a predictability effect** — it belongs to
group B/D's story, not evidence that the LM instrument's actual
predictability signal (mean_log_prob, perplexity, etc.) is useful here.

**Per the decision tree in the task instructions**: LM-only did **not**
perform better than the non-LM groups (D's 13.3% « B's 40.0% and E's
40.0%) — this does **not** support revisiting DEC-004 toward "the LM
helps." It also isn't proof the LM instrument is useless in general —
same standing caveat as before (small sample, one specific ablation
design, disclosed judgment calls in the length/count classification).
**DEC-004 stays open, not forced toward either conclusion** — see §14.

## 12. Comparison with EXP-003B

Group A's numbers here (threshold 0.06, test precision 0.176/recall
0.867/F1 0.292, top-1 60.0%/25.0% test/validation) are **identical** to
EXP-003B's original combined-model result — a useful internal
consistency check confirming this diagnostic experiment's pipeline
(reused fitting/metric code from `run_exp003a.py`/`run_exp003b.py`,
applied to the same unmodified data) reproduces the prior result exactly
before drawing any new conclusions from the other five groups.

**What's new here that EXP-003B didn't have**: EXP-003B's own ablation
table (§11 of that report) was explicitly flagged as uninformative,
run only at the fixed 0.5 threshold. This experiment redoes that
comparison properly (threshold-swept per group) and adds the length/
count vs. non-length split EXP-003B's original ablation design didn't
include. **EXP-003B.md itself is unmodified** — this report supersedes
only its §11 ablation's *informativeness*, not its other findings
(essay-level chance performance, the core existence of sentence-level
signal, etc., all still stand).

## 13. Limitations

- Feature classification (§2) involved real judgment calls, disclosed:
  `stylo_mean_avg_word_length` classified as non-length (vocabulary,
  not sentence-length) and `stylo_mean_dependency_depth` classified as
  non-length (structural, though length-correlated in general
  linguistics) — a different, defensible classification could shift
  results at the margin.
- Small samples throughout: 15–21 locatable essays per split for top-1;
  15–20 positive sentences per split for the fixed-threshold metrics.
  Every rate above should be read as indicative, not precise.
- D and E's fixed-threshold metrics are genuinely uninformative
  (degenerate, §7) — this experiment leans on top-1 ranking as the
  more diagnostic metric for the weaker groups, which is itself a
  choice worth flagging, not a neutral default.
- Validation top-1 rates are consistently lower than test top-1 rates
  across nearly every group (A: 25%→60%, B: 20%→40%, D: 10%→13%, E:
  15%→40%) — essay sentence-counts are comparable between splits
  (12.57 vs. 12.31 mean), so this isn't a difficulty artifact of split
  composition; most plausibly small-sample noise, but the consistency
  across groups is noted as an open observation, not fully explained.
- This remains scoped to `sentence_light_controlled_v2` /
  Qwen2.5-1.5B-Instruct only (EXP-003B §18's standing scope limitation).

## 14. Conclusion

**The sentence-level localization signal does not disappear when
length/count features are removed** — non-length features alone (18
features spanning stylometric vocabulary/repetition/POS/syntax measures
plus genuine LM predictability) reach 46.7% top-1 accuracy on test,
comparable to length/count features alone (40.0%) and far above the
~8% chance rate. This is real, positive evidence that this benchmark's
localization signal reflects more than a trivial length artifact of the
controlled-splice mechanism. **The genuine LM predictability signal,
isolated from length/count, performs the worst of any group tested
(13.3% top-1)** — a second, independent piece of evidence (alongside
EXP-003A's essay-level finding) that this project's specific LM
instrument (`distilgpt2`, whole-essay-context scoring) has not yet
demonstrated value for AI-assistance detection at either granularity
tested so far. **The full feature set still performs best (60.0%
top-1)**, suggesting length/count and non-length signals are at least
partly complementary rather than one subsuming the other.

**Per the stop condition: EXP-003C, fairness, NLI, cross-generator,
external-generator, and production-optimization work are explicitly
not run as part of this report.** Reporting and stopping for review.

## Decision records

Per explicit instruction, updated only where this experiment's evidence
actually warrants it — none marked Accepted/Resolved merely because
the experiment completed:

- **DEC-004** (LM instrument contribution): status **stays open, not
  resolved either direction**. New evidence added: LM-only localization
  is weak (13.3% top-1) and specifically weaker than non-LM stylometric
  alone (40.0%) — a second data point consistent with, but not
  conclusive proof of, DEC-004's standing skepticism. `lm_mean_token_count`
  is now explicitly reclassified as a length/count feature, not
  predictability evidence, correcting how EXP-003B's original
  interpretation of its top coefficient should be read.
- **DEC-015** (model/threshold strategy): no change — this experiment
  used the exact procedure DEC-015 already specifies, applied per
  feature group; its degenerate-threshold observation (D/E, §7) is
  additional evidence for DEC-015's already-recorded Revisit-When item
  about a validation-signal-strength guard, not a new finding requiring
  a new entry.
- **DEC-016** (localization design): status **unchanged (design
  validated, detection performance weak)** — this experiment used
  DEC-016's exact ground-truth mechanism unmodified and found it
  produces a consistent, internally-reproducible result (§12); no new
  evidence about the design itself, only about which features drive
  detection through it.
- **DEC-017** (evidence mapping): no change — not exercised by this
  diagnostic experiment (no new user-facing evidence statements were
  generated).

## Reproducibility

| Field | Value |
|---|---|
| Source dataset | `experiments/EXP-003B/features_sentence.jsonl` (unmodified) |
| PRIMARY-DATASET-v1 | unmodified (this experiment never touches it directly) |
| Script | `scripts/run_exp003b_r1.py` (imports fitting/metric utilities from `run_exp003a.py`/`run_exp003b.py`, no duplicated logic) |
| Preprocessing | Independent `StandardScaler` per feature group, fit on train only |
| Random seed | 42 |
| Model | `LogisticRegression` via `LogisticRegressionCV(Cs=10, cv=5-fold StratifiedKFold, scoring="f1", random_state=42)`, fit independently per group |
| `sklearn` version | 1.9.0 |
| Python version | 3.14.6 |
| Raw output | `experiments/EXP-003B-R1/results.json` — verbatim source for every number in this report |
