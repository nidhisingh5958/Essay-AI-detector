# Sentence Localization & Deterministic Evidence Mapping — Phases C + D

**Status: executed 2026-08-15.** Builds directly on Phase B (frozen
detector integration — see [production-detector.md](production-detector.md)).
This document distinguishes, throughout, **experimentally validated
behavior** from **product presentation decisions** — the two are never
the same thing here.

## Sentence ranking (Phase C)

| | Experimentally validated | Product presentation decision |
|---|---|---|
| Model, feature group, `C=166.81005372000558` | ✅ EXP-003B/B-R1 | — |
| Ranking (not thresholding) as the decision rule | ✅ EXP-003B's own raw 0.34 threshold is documented-degenerate | — |
| Top-1 test accuracy = 60.0% (9/15) | ✅ reproduced exactly by the production artifact (Phase B) and now by `rank_sentences()` end-to-end (Phase C) | — |
| **Top-K = 3** | ❌ never calibrated by any research protocol | ✅ `evidence_mapper.DEFAULT_TOP_K_SENTENCES = 3` — a caller-overridable UI default |
| Deterministic tie-break (score desc., then sentence index asc.) | — | ✅ a presentation-stability rule, not a research finding |

**K is never used to select or evaluate anything against the test set**
— no code path in this phase computes "accuracy at K" or optimizes K
against any research data. If a future research pass wants to evaluate
different K values, that must be its own separate, pre-registered
experiment (not silently folded into this presentation layer).

**Label**: every ranked sentence carries the fixed string
`"potentially_ai_assisted"` — never `"ai_written"` or `"ai_generated"`
anywhere in the codebase (verified: `grep` finds no such string
assigned as a label; `test_evidence_mapper.py`'s evidence-language tests
enforce cautious phrasing generally).

## Offsets (Phase C item 4)

`SentenceRankingResult.normalized_text` is the single string every
`char_start`/`char_end` in `ranked`/`skipped` refers to.
`app.services.detector.rank_sentences()` normalizes text exactly once,
internally, and returns that exact string — callers must never
re-derive or re-normalize separately and apply these offsets to a
different representation (normalization can change string length via
CRLF→LF collapsing and control-character stripping, so this is not a
theoretical concern). Regression-tested
(`backend/tests/test_sentence_ranking_offsets.py`) against punctuation,
Unicode (accents, emoji), multi-paragraph text, quotation marks,
apostrophes, irregular whitespace, and consecutive short sentences —
every case slices `normalized_text[start:end]` back to the exact
sentence text.

## Ranking correctness guarantees

- **No NaN/invalid scores enter the ranking** — every score is a
  `predict_proba` output on a *complete* feature vector; sentences with
  any missing feature are diverted to `skipped` before scoring is ever
  attempted (never scored with a placeholder).
- **Deterministic tie-break, documented exactly**: sort key
  `(-score, sentence_index)` — ties broken by original sentence
  position, ascending.
- **`rank` is 1-indexed and contiguous** across the *scorable* sentences
  only (skipped sentences do not consume a rank number).

## Deterministic evidence mapping (Phase D)

```
feature (raw extracted value)
  -> observed value
  -> reference interpretation (vs. human-population reference stats,
     computed once from EXP-003A's frozen TRAIN-split human essays --
     scripts/build_feature_reference_stats.py; descriptive statistics
     of already-frozen data, NOT a new model or fit)
  -> fixed template (FEATURE_LABELS + a single statement-building
     function, backend/app/services/evidence_mapper.py)
  -> evidence statement
```

**No LLM, chat API, or generative model is called anywhere in
`evidence_mapper.py`** — enforced by an AST-based import-scan test
(`test_K_evidence_mapper_module_has_no_llm_or_network_imports`), not
just a code-review claim.

### Model contribution (Phase D item 11) — exact formula

```
contribution[i] = model.coef_[i] * standardized_value[i]
standardized_value[i] = (observed_value[i] - scaler.mean_[i]) / scaler.scale_[i]
```

This is exactly the per-feature term the frozen `LogisticRegression`
sums (plus intercept) to produce its decision-function logit — verified
structurally by test (`test_J_sum_of_all_contributions_plus_intercept_equals_the_model_logit`):
summing every feature's contribution plus the model intercept
reproduces sklearn's own `decision_function` output exactly (tolerance
`1e-6`). This is a deterministic linear decomposition of the
already-frozen model — **not** a new computation, **not** retraining,
and (per explicit instruction) **not** presented as causal importance —
UI/API language must use "contributed to the detector score," never
"caused the detector to flag this."

### Evidence selection (Phase D item 12) — exact rule

1. Discard any feature with a missing (`None`) observed value.
2. Rank remaining features by `abs(contribution)`, descending.
3. **No experimentally-established contribution floor exists** — none
   invented. (If research later establishes one, it replaces step 3;
   until then, no cutoff beyond "top N" is applied.)
4. Take the top `N` (`evidence_mapper.DEFAULT_TOP_N_EVIDENCE = 3` — a
   documented UI default, not a research threshold, same status as K
   above).
5. Deterministic tie-break: canonical `ALL_FIELDS` index order,
   ascending.

### Essay-level result states (Phase D item 14)

Per the explicit instruction not to invent a second numerical
threshold, this uses **the safe two-state-plus-evidence-gated-third
alternative**, not a score-banded three-state model:

| State | Trigger |
|---|---|
| `machine_signal_detected` | `score >= 0.47` (the one, already-frozen EXP-003A threshold) |
| `no_strong_signal_detected` | `score < 0.47` |
| `inconclusive` | **Only** when the 29-feature vector could not be completed (e.g. no LM-scorable tokens) — an evidence-availability trigger, never a score-range trigger |

**No score band/second threshold was invented.** If a future,
separately-authorized calibration pass computes real validation-score
band edges, that would justify a genuine three-way *score*-based split
— not done here.

### Language discipline (Phase D items 10, 16, 19)

- Every evidence statement uses the fixed pattern: *"This shows a
  {higher/lower} level of {feature label} than the reference range used
  by the detector (observed X vs. a human-reference average of Y)."* —
  measured, comparative, never causal or psychological.
- `ESSAY_SCORE_EXPLANATION`, `SENTENCE_DISCLAIMER`, and
  `ESSAY_LIMITATION_NOTE` are fixed constants (see
  `evidence_mapper.py`) carrying the required disclaimers — e.g. *"They
  are not proof that AI wrote the passage."*
- Research performance metrics (86.7% recall, 97.8% test accuracy, 60%
  top-1) **never appear as per-input confidence anywhere in this
  layer** — the only per-input numbers exposed are the essay's own
  `score` (a probability under the frozen model, explicitly qualified)
  and each sentence's own `score`. No test asserts a research metric
  appears in any evidence/result string, and manual review of every
  template confirms none does.

## Tests (Phase C + D)

`backend/tests/test_sentence_ranking_offsets.py` (14 tests) and
`backend/tests/test_evidence_mapper.py` (16 tests) — **30 new tests,
all passing**. Covering, per the approved item list: deterministic
output (A), known-ranking reproduction for a real EXP-003B essay (B),
top-K ordering (C), tie-breaking (D), missing-feature behavior (E),
no-scorable-sentence behavior (F), Unicode/offset correctness (G),
evidence reproducibility (H), evidence ordering (I), contribution
calculation (J, including the structural logit-sum proof), no-LLM/
network dependency (K), and family `302DC21A6DEE`'s known borderline
case (L) — its essay-level evidence is still honestly produced (not
suppressed) even though it's the known, documented false positive.

**Regression check (item 18)**: `rank_sentences()`'s end-to-end output
for a real EXP-003B test essay (`2723DB12AC00__sentence_light_controlled_v2`)
was inspected before asserting, then locked in as an assertion — the
production pipeline (including every Phase C change: normalization,
tie-break, rank assignment) reproduces the cached-feature/sklearn-level
top-1 result exactly. Ranking behavior is unchanged by Phase C/D.

## Known limitations carried forward

- Sentence-localization top-1 accuracy (60%, research-validated) means
  roughly 2 in 5 essays' true AI-touched sentence will not be the
  top-ranked candidate — K=3 (a presentation default, not a
  calibrated recall target) mitigates but does not eliminate this.
- Evidence statements describe association with reference-population
  averages, not proof of any individual claim.
- The essay-level `inconclusive` state is currently reachable only via
  the missing-feature path — most essays will resolve to one of the two
  score-based states; a genuinely ambiguous *score* (e.g. very close to
  0.47) is reported as whichever side of 0.47 it falls on, honestly, not
  softened into "inconclusive" without an evidence-availability reason.
