# FAIR-001 — Fairness Evaluation

**Status: EXECUTED 2026-08-15.** Design:
[docs/experiments/FAIR-001.md](../docs/experiments/FAIR-001.md).
Decision record: [DEC-018](../docs/decisions/DEC-018-fairness-evaluation-methodology.md).

**This is an evaluation of the already-frozen detector, not a new
training experiment.** No retraining, refitting, tuning, threshold
change, feature change, or preprocessing change occurred anywhere in
this experiment.

## 1. Research question

Does the frozen detector's error behavior (false-positive rate,
false-negative rate, score distribution) differ across English-
language-proficiency subgroups, for reasons unrelated to actual AI
involvement?

## 2. Fairness variables

**Primary**: PERSUADE 2.0's `ell_status` field (`Yes` / `No` /
unlabeled) — binary, self/institution-reported.

**Secondary, exploratory only**: ELLIPSE's continuous proficiency
subscores (`Overall`, `Cohesion`, `Syntax`, `Vocabulary`,
`Phraseology`, `Grammar`, `Conventions`), available for a subset of
families that appear in both corpora. No new demographic grouping was
invented; no incompatible variables were merged to inflate sample size.

## 3. Data sources

| Variable | Source file | Join key |
|---|---|---|
| `ell_status` | `data/raw/persuade_2.0/persuade_2.0_human_scores_demo_id_github.csv` | `family_id == essay_id_comp` |
| ELLIPSE proficiency | `data/raw/ellipse_corpus/ELLIPSE_Final_github.csv` | `family_id == text_id_kaggle` |

A validity check: all 9 PRIMARY-DATASET-v1 families with an ELLIPSE
match have `ell_status == "Yes"` in PERSUADE, exactly as expected since
ELLIPSE is by construction an English-language-learner corpus — an
internal consistency confirmation, not an assumption.

## 4. Sample counts

`ell_status` distribution across all 150 PRIMARY-DATASET-v1 families
(re-verified programmatically, matching the design-phase feasibility
finding exactly):

| Group | n families |
|---|---|
| `Yes` | 10 |
| `No` | 132 |
| unlabeled | 8 |

Per DEC-018/FAIR-001.md's already-established feasibility finding, the
**frozen test split alone contains only 1 `Yes` family** — confirmed
still true, and confirmed still insufficient for any comparison on its
own. This is why the approved design scores all 150 families instead.

## 5. Detector configuration (frozen, unchanged)

Two detectors evaluated, both exactly as frozen previously — no
retraining:

| Detector | Task | Frozen threshold | Reproduction check |
|---|---|---|---|
| EXP-003A primary (combined) | human vs. `full_ai` | 0.47 | `chosen_C=0.005994842503189409` — **matches recorded value exactly** |
| EXP-003B essay-level primary (combined) | human vs. `ai_assisted` | 0.34 | `chosen_C=21.54434690031882` — **matches recorded value exactly** |

Both models were refit deterministically from the exact same train
split / `random_state=42` / code path as their original scripts
(`run_exp003a.py`, `run_exp003b.py`) — a reproduction, not a new fit —
and the refit is asserted to reproduce the recorded `chosen_C` before
any scoring happens (`scripts/run_fair001_score_all.py` raises
`AssertionError` otherwise).

## 6. Confirmation: fairness metadata not used as features

Verified programmatically (`verify_no_demographic_leakage()`,
re-run every execution, not a one-off design-time claim) against every
feature file this project has produced:
`experiments/EXP-003A/features.jsonl`,
`experiments/EXP-003B/features_essay.jsonl`,
`experiments/EXP-003B/features_sentence.jsonl`,
`experiments/EXP-003C/features_essay.jsonl`,
`experiments/GEN-001/features_phi.jsonl`. **Zero occurrences** of
`gender`, `race_ethnicity`, `economically_disadvantaged`,
`student_disability_status`, or `ell_status` in any of them. The
`ell_status`/ELLIPSE join used by this experiment happens exclusively
in `scripts/run_fair001_fairness_analysis.py`, in memory, and is never
written back into any feature file or used by any model-fitting code.

## 7. Methodology

**Stage 1** (`scripts/run_fair001_score_all.py`): apply the frozen
EXP-003A and EXP-003B essay-level models — refit-reproduced, not newly
fit — to **every** row in their respective feature files, regardless of
`split` (train/validation/test all included). This raises the
`ell_status=Yes` subgroup from 1 (test-only) to 10 (all families) —
the deliberate, DEC-018-approved departure from "touch test only",
justified because it reads the already-frozen model's output on more
inputs without touching model development in any way.

**Stage 2** (`scripts/run_fair001_fairness_analysis.py`): join
`ell_status`/ELLIPSE to the scored predictions by `family_id`, and
compute, per subgroup: `n`, error count, error rate, a Wilson 95% CI
(only when `n >= 10`), and the raw score distribution
(mean/median/std/min/max). Below `n=10`, the entry is labeled
`INSUFFICIENT DATA` and no rate is presented as reliable — fixed in
advance (DEC-018), not adjusted after seeing results.

## 8. Subgroup metrics — EXP-003A (human vs. `full_ai`, the working detector)

**Human false-positive rate** (human essays incorrectly flagged as
`machine`), by `ell_status`:

| Group | n | FP | FPR | 95% CI |
|---|---|---|---|---|
| `Yes` | 10 | 0 | 0.0% | [0.0%, 27.8%] |
| `No` | 132 | 1 | 0.76% | [0.13%, 4.17%] |
| unlabeled | 8 | 0 | — | **INSUFFICIENT DATA** (n=8 < 10) |

**AI false-negative rate** (`full_ai` essays missed, i.e. predicted
`human`), by the source human writer's `ell_status`:

| Group | n | FN | FNR | 95% CI |
|---|---|---|---|---|
| `Yes` | 10 | 0 | 0.0% | [0.0%, 27.8%] |
| `No` | 131 | 0 | 0.0% | [0.0%, 2.85%] |
| unlabeled | 7 | 0 | — | **INSUFFICIENT DATA** (n=7 < 10) |

The single false positive in the `No` group is the same recurring
family (`302DC21A6DEE`) flagged in EXP-003A/B/C/GEN-001 — **that
family's `ell_status` is `No`**, so this pre-existing, generator-
independent quirk is not related to English-proficiency status.

## 9. Subgroup metrics — EXP-003B essay-level (human vs. `ai_assisted`, near-chance detector)

**Reported with the mandatory caveat, stated in advance**: EXP-003B's
essay-level detector performs at near-chance level (its own frozen
threshold, 0.34, flags almost every essay `ai_assisted` — validation
`recall_machine=1.0`, `precision_machine=0.5`). Any pattern below
answers "does a near-random classifier's randomness happen to
correlate with subgroup," **not** "does a working detector treat
subgroups differently" — per FAIR-001.md §A.4, these are different
questions, and only the first is answerable given this detector's
current performance.

**Human false-positive rate**, by `ell_status`:

| Group | n | FP | FPR | 95% CI |
|---|---|---|---|---|
| `Yes` | 10 | 10 | 100.0% | [72.2%, 100.0%] |
| `No` | 132 | 126 | 95.45% | [90.4%, 97.9%] |
| unlabeled | 8 | 8 | — | **INSUFFICIENT DATA** (n=8 < 10) |

**`ai_assisted` false-negative rate**, by `ell_status`:

| Group | n | FN | FNR | 95% CI |
|---|---|---|---|---|
| `Yes` | 8 | 0 | — | **INSUFFICIENT DATA** (n=8 < 10) |
| `No` | 113 | 2 | 1.77% | [0.49%, 6.22%] |
| unlabeled | 6 | 0 | — | **INSUFFICIENT DATA** (n=6 < 10) |

Both groups' FP rates sit near ceiling (100% vs. 95.45%), consistent
with — not distinguishable from — this detector's known near-universal
"flag as `ai_assisted`" behavior at its frozen threshold. **This
pattern is not treated as a fairness finding**: with both groups
already near 100%, the 4.5-point gap is exactly what a detector with
essentially no discriminative power would be expected to produce by
chance, and the small `Yes`-group `n` (10) cannot distinguish a real
effect from noise here regardless.

## 10. Score distributions

Raw `P(machine)` / `P(ai_assisted)` score means, by group (EXP-003A):

| Group | Human mean score | `full_ai` mean score |
|---|---|---|
| `Yes` (n=10) | 0.179 | 0.804 |
| `No` (n=131–132) | 0.185 | 0.800 |

The `Yes` and `No` groups' human-score means (0.179 vs. 0.185) and
`full_ai`-score means (0.804 vs. 0.800) are close, with the `Yes`
group's small standard deviation (0.096) overlapping substantially
with `No`'s (0.090) — **no visible shift in the underlying score
distribution**, not just the thresholded decision. This is meaningful
because two subgroups could show identical classification *rates*
while differing systematically in *confidence* — that was checked for
here and not found, within the limits of n=10.

## 11. ELLIPSE secondary/exploratory analysis

**n=9** — smaller than even the primary `ell_status=Yes` group (one of
the 10 `Yes` families lacks an ELLIPSE match). Per the design's own
threshold, this is below `MIN_SUBGROUP_N=10` — **no correlation
statistic is computed or claimed.** Raw rows only, for descriptive
reference:

| ELLIPSE Overall proficiency | Detector `P(machine)` score (human essay) |
|---|---|
| 2.5 | 0.105 |
| 2.5 | 0.330 |
| 3.0 | 0.081 |
| 3.0 | 0.127 |
| 3.5 | 0.101 |
| 3.5 | 0.284 |
| 3.5 | 0.316 |
| 4.0 | 0.121 |
| 4.0 | 0.239 |

No visible monotonic pattern is claimed or should be inferred from 9
points — included for transparency and as a pointer for future,
better-powered work, not as evidence.

## 12. Uncertainty

Every rate above is reported with its raw counts and, where `n >= 10`,
a Wilson 95% CI. The `Yes`-group intervals are wide (e.g. [0.0%,
27.8%] for EXP-003A) — a difference as large as ~28 percentage points
in either direction would not be reliably distinguishable from the
observed 0% at this sample size. Point-estimate differences smaller
than a few percentage points (e.g. "0% vs. 0.76%") are reported as raw
counts, not framed as a substantive disparity — consistent with the
explicit instruction not to inflate "2/10 vs. 1/10"-scale differences
into disparity claims.

## 13. Insufficient-data cases (explicit list)

- EXP-003A human FP, unlabeled group (n=8)
- EXP-003A AI FN, unlabeled group (n=7)
- EXP-003B human FP, unlabeled group (n=8)
- EXP-003B `ai_assisted` FN, `Yes` group (n=8) and unlabeled group (n=6)
- ELLIPSE secondary analysis (n=9, entire analysis)

None of these were given a computed rate presented as reliable; all are
labeled `INSUFFICIENT DATA` in `experiments/FAIR-001/results.json`.

## 14. Findings

**For the working detector (EXP-003A, human vs. `full_ai`)**: within
the available data, **no disparity is observed** — both the human
false-positive rate (0.0% `Yes` vs. 0.76% `No`) and the AI false-
negative rate (0.0% `Yes` vs. 0.0% `No`) are near zero for both
groups, and the underlying score distributions largely overlap. This
is a genuinely clean result, not a marginal one requiring
interpretation.

**For the near-chance detector (EXP-003B essay-level, human vs.
`ai_assisted`)**: no interpretable fairness finding — the detector's
own near-universal-positive behavior at its frozen threshold makes any
subgroup comparison here uninformative about *fairness* specifically
(both groups are near-ceiling regardless of subgroup), consistent with
the caveat stated in advance (§9, FAIR-001.md §A.4).

**ELLIPSE secondary analysis**: descriptive only, n=9, no claim made.

## 15. Limitations

- `ell_status` is binary and self/institution-reported, not an
  independently verified or continuous proficiency measure.
- The `Yes` subgroup (n=10) is small even after scoring all 150
  families — the pre-registered maximum this dataset can currently
  support. Confidence intervals are correspondingly wide; **absence of
  a detected disparity is not proof of fairness**, only an absence of
  evidence for one within this dataset's limits.
- 8 families (5.3%) have no `ell_status` label and are excluded from
  the group comparison, not imputed.
- `ell_status` describes the *source human writer's* subgroup for a
  whole family, including its AI-touched samples — this says nothing
  about the AI generation model's own behavior conditioned on a
  subgroup, only about detector error rates on writing originating
  from essays by writers in that subgroup.
- PRIMARY-DATASET-v1's `Yes`-labeled essays may not represent the
  broader population of English-language learners generally — a small,
  single-dataset sample.
- EXP-003B's near-chance essay-level detector makes its own subgroup
  numbers uninformative for fairness purposes, independent of sample
  size (§9) — a detector-quality limitation, not a data limitation.
- The ELLIPSE secondary analysis (n=9) is far below any threshold for
  a reliability claim and is included only for transparency/future
  reference.

## 16. Conclusion

**Category A — no material disparity detected within the available
data**, for the working detector (EXP-003A) specifically, on the
primary fairness variable (`ell_status`). This conclusion is reached
because the observed data genuinely shows no gap (not because the
result was rounded toward a favorable category): both false-positive
and false-negative rates are near zero and statistically
indistinguishable between the `Yes` and `No` groups, and score
distributions overlap substantially.

This is explicitly **not** a general "this detector is fair" claim.
It is bounded to: this specific detector configuration, this specific
dataset (PRIMARY-DATASET-v1), this specific fairness variable
(`ell_status`), and a sample size (`n=10` in the `Yes` group) that can
only rule out a large disparity (roughly >25–28 percentage points),
not a smaller one. The near-chance EXP-003B essay-level detector
produced no interpretable fairness signal at all, for reasons
unrelated to fairness (its own weak discriminative power) — reported
as such, not folded into the primary finding. A larger, more powered
`ell_status=Yes` sample (PRIMARY-DATASET-v2, or a purpose-built
ELLIPSE-based extension) would be needed to detect a smaller disparity
with confidence, per DEC-018's "Revisit When."

## Decision record

**DEC-018 updated** — see
[DEC-018](../docs/decisions/DEC-018-fairness-evaluation-methodology.md)'s
Evidence section. Status set to **Provisional (executed, Category A
finding — no material disparity detected, underpowered to rule out a
smaller one)** — explicitly **not** marked Accepted, per instruction not
to auto-resolve based on a single, small-sample execution.

## 17. Reproducibility

```json
{
  "scoring_script": "scripts/run_fair001_score_all.py",
  "analysis_script": "scripts/run_fair001_fairness_analysis.py",
  "exp003a_frozen_threshold": 0.47,
  "exp003b_essay_frozen_threshold": 0.34,
  "min_subgroup_n_threshold": 10,
  "fairness_variable_source": "PERSUADE 2.0 ell_status (primary), ELLIPSE_Final_github.csv proficiency subscores (secondary/exploratory)",
  "join_key": "family_id == essay_id_comp (PERSUADE) == text_id_kaggle (ELLIPSE)",
  "random_seed": 42
}
```

**Detector versions**: EXP-003A primary combined model (`chosen_C =
0.005994842503189409`, threshold 0.47); EXP-003B essay-level primary
combined model (`chosen_C = 21.54434690031882`, threshold 0.34). Both
refit-reproduced from `experiments/EXP-003A/features.jsonl` and
`experiments/EXP-003B/features_essay.jsonl` respectively — no new
feature extraction.

**Files**:
- `experiments/FAIR-001/scored_exp003a_all_families.jsonl` (298 records)
- `experiments/FAIR-001/scored_exp003b_essay_all_families.jsonl` (277 records)
- `experiments/FAIR-001/results.json` (full analysis output, source of
  every number in this report)
- `scripts/run_fair001_score_all.py`, `scripts/run_fair001_fairness_analysis.py`
- `scripts/tests/test_fair001_execution.py` (15 tests)

**What was explicitly NOT run in this experiment**: another generator,
sentence-level three-class, NLI, detector retraining/tuning,
PRIMARY-DATASET-v1 modification, frozen-test-set modification,
production/UI changes.
