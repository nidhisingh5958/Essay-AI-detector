# Project Status

## Current Phase

Phase 4 — Language Model Instrumentation (complete)

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Phase 3 — Linguistic feature extraction, sentence + essay level
      (DEC-006, Provisional)
- [x] `backend/app/services/language_model.py`:
  - Loads `distilgpt2` once per process (DEC-007)
  - `compute_token_log_probs(text)` — whole-essay single-pass scoring,
    chunked only if the essay exceeds the 1024-token context window
    (DEC-008); character-offset-based, so tokens can be attributed back
    to sentences without re-tokenizing
  - `compute_sentence_lm_features(sentence, token_log_probs)` — mean/
    median log-probability, log-probability variance, perplexity; returns
    `None` (not a fabricated value) when a sentence has no scorable
    tokens
  - `compute_predictability_deltas(...)` — change in mean log-probability
    between neighboring sentences (Section 6A), propagating `None`
    correctly when either side lacks evidence
- [x] DEC-007 (Accepted): local LM choice, `distilgpt2` over `gpt2`/
      gpt-neo-125M/larger modern models/n-gram models
- [x] DEC-008 (Accepted): whole-essay single-pass scoring over
      per-sentence isolated scoring, so the neighboring-sentence
      predictability-change signal reflects real document context
- [x] 9 new tests covering empty/single-token input, valid log-probability
      ranges and offset correctness, the "first token of essay is never
      scored" invariant, sentence-level aggregation correctness
      (perplexity = exp(-mean_log_prob)), the `None`-on-insufficient-
      evidence path, predictability-delta computation and `None`
      propagation, and chunking on a long (~1500-word) essay — all
      passing (43 total across the backend, full suite runs in ~14s on a
      normal laptop CPU)
- [x] Documentation updated: `architecture.md`, `methodology.md`,
      `decisions.md`, `decision-summary.md`, `final-decision-guide.md`,
      `README.md`

## In Progress

- [ ] None — Phase 4 is complete. Phase 5 has not started.

## Experiments

None yet. Phase 4, like Phase 3, produces measurable feature *values*
with correctness tests, not evidence of discriminative signal — that is
EXP-003, blocked on the Phase 5 dataset (see DEC-007/DEC-008 "Revisit
When").

## Current Known Problems

- No LM-derived feature has been validated against real human/AI data.
- distilgpt2 is a small, relatively weak model — its probability
  estimates are noisier than a larger model's. Documented as an accepted
  trade-off (DEC-007), with `gpt2` as a low-cost escalation path if
  EXP-003 shows the signal is too weak.
- Essays long enough to require chunking lose one token of context at
  each chunk boundary (DEC-008) — bounded, documented, not yet known to
  matter in practice (no long-essay evaluation has been run).
- The application still does not classify or score essays.
- `docs/dataset.md`, `docs/evaluation.md`, `docs/failure-analysis.md`,
  and `docs/fairness.md` remain intentional placeholders.

## Decisions Pending

- Dataset sources and generation approach (Phase 5)
- Which Phase 3/4 features are actually retained once EXP-002/EXP-003 can
  be run (Phase 5/6)
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps

1. Phase 5: dataset construction — this is now the blocking prerequisite
   for validating any feature built in Phases 3–4. Needs its own set of
   decisions (source selection, machine/mixed-sample generation approach,
   leakage-safe splitting) before any code is written, per
   [dataset.md](dataset.md).
2. Run EXP-001 (baseline) once a minimal labeled dataset exists, then
   EXP-002 (linguistic features) and EXP-003 (+ LM features) to actually
   test DEC-006/007/008's provisional assumptions.
3. Update this file at the end of Phase 5.
