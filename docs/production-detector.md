# Production Detector — Phase B

**Status: Phase B executed 2026-08-15.** This document describes the
production inference artifacts derived from the frozen EXP-003A
(essay-level) and EXP-003B (sentence-localization) research results.
This is an **inference-only engineering artifact** — no new model, no
new experiment, no retraining. See
[PRODUCT-AUDIT.md](PRODUCT-AUDIT.md) §6 for the configuration-selection
reasoning and [docs/decisions/DEC-015](decisions/DEC-015-exp003-model-selection-and-threshold-strategy.md)
for the underlying model/threshold-selection discipline this respects.

## Two STOP-and-report findings (per the approved Phase B spec)

Before describing what was built, two items were explicitly **not**
invented, per instruction:

1. **§8 — Essay-level three-state result bands.** The product audit
   (PRODUCT-AUDIT.md §5) *proposed* a three-state UI ("Strong signal" /
   "No strong signal" / "Inconclusive"), but inspection of
   `experiments/EXP-003A/results.json`'s `threshold_selection` block
   confirms **no band edges were ever computed or frozen by any
   research protocol** — only a single point threshold (0.47) exists,
   selected by maximizing F1 on validation. No validation-score
   overlap region, no confidence band, nothing resembling a second/
   third cutoff was ever calculated. **This is a missing calibration
   decision, not implemented here.** `EssayDetectionResult` therefore
   exposes only the raw `score` and the single frozen `label_at_threshold`
   (`"machine"`/`"human"` at 0.47) — no `band` field exists. Computing
   band edges (an analysis-only task reusing already-computed
   validation scores, no new fitting) is explicitly deferred to Phase D.
2. **§9 — Sentence-localization top-K.** No approved product
   specification fixed a value for K (how many ranked sentences to
   surface). The product audit only *proposed* "K=1–3, tunable in UI
   copy" as a suggestion, not a frozen decision. **This is also not
   implemented here.** `rank_sentences()` returns every scorable
   sentence, sorted by score descending, uncapped — K-selection is a
   Phase D/UI decision.

## Model artifact rule (§2)

**No serialized model artifact existed anywhere in the repository
before this phase.** Every prior use of EXP-003A's/EXP-003B's frozen
models (the original experiments, GEN-001, FAIR-001) refit the exact
same scaler + `LogisticRegressionCV` deterministically at run time
(`StandardScaler` on the recorded train split, `random_state=42`,
`fit_logreg_cv` from `scripts/run_exp003a.py`) — this is a documented,
already-three-times-verified reproducible procedure, not a new fitting
method invented for this phase.

`scripts/build_essay_detector_artifact.py` and
`scripts/build_sentence_detector_artifact.py` perform that **same**
refit one more time and serialize the result via `joblib`, so
production code never refits anything or needs training data at
runtime. Both scripts **verify** the refit before writing anything:

- **Essay-level** (`essay_detector_v1.joblib`): refit `chosen_C`
  matches `experiments/EXP-003A/results.json` exactly
  (`0.005994842503189409`), AND every one of the 46 frozen TEST
  samples' scores reproduces the recorded score in
  `results.json`'s `test_predictions` to within `5e-5` (the precision
  those scores were originally rounded to). **Both checks passed.**
- **Sentence-localization** (`sentence_detector_v1.joblib`): refit
  `chosen_C` matches `experiments/EXP-003B/results.json`'s
  `sentence_level.primary_combined_logreg` value exactly
  (`166.81005372000558`), AND the refit model reproduces EXP-003B's
  recorded top-1 localization test accuracy **exactly** (9/15 correct,
  60.0%). **Both checks passed.**

If either verification had failed, the build scripts raise
`RuntimeError` and refuse to write an artifact — this did not happen.

**Artifact storage**: `backend/app/ml/*.joblib`, gitignored (consistent
with this project's existing policy of never committing model weights —
`*.pt`/`*.bin`/`*.safetensors` were already excluded; `*.joblib` was
added to the same rule). **Disclosed trade-off**: this means a fresh
clone must run both build scripts once before the detector service can
load anything — a deliberate choice consistent with "never commit model
artifacts," not an oversight. If a team prefers committing a small
(few-KB) logistic-regression artifact for demo reliability, that is a
legitimate alternative not adopted here without further discussion.

## Frozen configuration (exact)

| | Essay-level (`EXP-003A`) | Sentence-localization (`EXP-003B`) |
|---|---|---|
| Model | `LogisticRegression` via `LogisticRegressionCV`, L2 | Same |
| `C` | `0.005994842503189409` | `166.81005372000558` |
| Feature group | Combined, 29 features | Combined, 29 features |
| Preprocessing | `StandardScaler`, fit on EXP-003A's 208-row train split | `StandardScaler`, fit on EXP-003B's 1117-row sentence-level train split |
| Decision rule | Threshold 0.47 (`score >= 0.47` → `"machine"`) | **Ranking only** — no threshold; EXP-003B's own raw 0.34 threshold is degenerate (near-universal positive) and is never used for a per-sentence binary decision |
| `random_state` | 42 | 42 |
| Reference | `experiments/EXP-003A/results.json` | `experiments/EXP-003B/results.json` |

**Not rounded internally anywhere** — `C` is stored and used as the
full-precision float shown above throughout (`chosen_C` from
`LogisticRegressionCV.C_[0]`, never re-typed by hand).

## Feature ordering (§3)

Single canonical specification: `backend/app/services/feature_spec.py`
— `ALL_FIELDS` (29 names, `STYLO_FIELDS` 23 + `LM_FIELDS` 6, in the
exact order `scripts/run_exp003a.py` has used since before any
experiment ran). Both `.joblib` artifacts store their own
`feature_order` at build time; `detector.py` asserts the artifact's
stored order matches `feature_spec.ALL_FIELDS` at load time and raises
if they ever diverge — **feature order can never silently mismatch**.
`FeatureVectorResult.as_ordered_vector()` raises `ValueError` if any
field is missing, rather than ever producing a partially-filled vector.

## Preprocessing path (§4)

```
essay text
  -> app.services.text_normalizer.normalize_text        (existing, unchanged)
  -> app.services.sentence_segmenter.segment_sentences   (existing, unchanged)
  -> app.services.feature_extractor.{extract_essay_features, extract_sentence_features}
     + app.services.language_model.{compute_token_log_probs, compute_sentence_lm_features,
       compute_predictability_deltas}                    (existing, unchanged)
  -> app.services.essay_feature_vector.extract_essay_feature_vector          (NEW, essay-level pooling)
     or app.services.sentence_feature_vectors.extract_sentence_feature_vectors (NEW, per-sentence)
  -> StandardScaler.transform (from the loaded artifact)
  -> LogisticRegression.predict_proba (from the loaded artifact)
  -> threshold comparison (essay-level only) / sort by score (sentence-level)
```

**No research feature calculation was rewritten.** The two new modules
(`essay_feature_vector.py`, `sentence_feature_vectors.py`) reproduce
`scripts/exp003a_extract_features.py`'s and
`scripts/exp003b_extract_features.py`'s exact computations, verified
equivalent by regression test (`backend/tests/test_essay_feature_vector.py`,
`backend/tests/test_sentence_feature_vectors.py`) against real recorded
feature values, not just re-implemented and trusted.

## Model loading (§5)

`backend/app/services/detector.py`: `_load_essay_artifact()` /
`_load_sentence_artifact()`, both `@lru_cache(maxsize=1)` — loaded once
per process, reused for every call. `DetectorArtifactMissingError` is
raised immediately (not deferred to first prediction) if the `.joblib`
file doesn't exist. No training/fitting code exists anywhere in this
module. Two functions expose inference only: `predict_essay(text) ->
EssayDetectionResult`, `rank_sentences(text) -> SentenceRankingResult`.

## Score semantics (§7)

The essay-level `score` is **the frozen classifier's estimated
probability of the positive class ("machine") under the EXP-003A
combined model, applied to this input's 29-feature vector** — nothing
more. It is explicitly **not**: a probability the essay is definitely
AI-written, a probability of AI *assistance* (that is a different,
essentially-unmeasurable task per EXP-003B/EXP-003C — see
PRODUCT-AUDIT.md §3), a universal AI-detection probability, or proof of
authorship. Any UI surface displaying this number must carry this exact
qualification (see PRODUCT-AUDIT.md §10 for exact proposed wording,
finalized in a later phase).

## Missing evidence (§11)

Every feature-extraction function returns explicit `None` for a value
it cannot compute (e.g. no LM-scorable tokens) — never `0.0`, never a
fabricated number. `predict_essay` raises `FeatureVectorIncompleteError`
if the 29-feature vector is incomplete, rather than scoring a partial
vector. `rank_sentences` returns incomplete sentences in a separate
`skipped` list with an explicit reason string, never silently dropped
and never assigned a score.

## Production input limits (§12)

Existing, already-tested boundaries reused, not reinvented:
`app.services.validation.validate_essay_text` already enforces
`min_essay_chars`/`max_essay_chars` (1 / 20,000, `app/config.py`) —
unchanged by this phase. Empty text: `extract_essay_feature_vector("")`
and `extract_sentence_feature_vectors("")` both handle this without
crashing (tested) — the former returns every field explicitly missing,
the latter returns an empty list. No sentence-segmentation-failure case
was observed in the existing 11 segmenter tests' edge cases (unicode,
punctuation-heavy, very long text) — no new boundary was invented here.

## Regression tests (§13) — results

`backend/tests/test_detector.py` (15 tests), plus
`test_essay_feature_vector.py` (5) and `test_sentence_feature_vectors.py`
(3) — **23 new tests, all passing**, covering every required area
(A–I): known human/full_ai/family-`302DC21A6DEE` reference-case score
reproduction against recorded EXP-003A output (tolerance `5e-5`,
matching the `round(score, 4)` precision those values were recorded
at), threshold-boundary logic, feature-order enforcement, model-loading
singleton/missing-artifact behavior, missing-feature refusal, repeated-
inference determinism, and fresh-artifact-load coefficient equality.
Full backend suite: **66/66 passing** (43 pre-existing + 23 new) — zero
pre-existing tests modified or weakened to pass.

## Known limitations

- Essay-level detector is binary human-vs-`full_ai` only — does not
  attempt `ai_assisted` classification (per EXP-003C's collapse,
  PRODUCT-AUDIT.md §5).
- LM-derived features (6 of 29) remain in the combined model despite no
  experiment ever showing they add value over stylometric-only — kept
  because the combined configuration is the only one with a complete,
  DEC-015-compliant threshold-sweep behind it (PRODUCT-AUDIT.md §6);
  not re-litigated in this phase.
- Sentence-localization model: 60% top-1 test accuracy means roughly 2
  in 5 essays' true AI-touched sentence will not be the top-ranked one.
- No band calibration, no fixed K — both explicitly deferred (see STOP-
  and-report items above).
- distilgpt2, spaCy `en_core_web_sm` must be available in the runtime
  environment (already a dependency of the existing, unchanged
  `feature_extractor.py`/`language_model.py`) — no new model-weight
  dependency introduced by this phase.
