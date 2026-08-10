# Project Status

## Current Phase

Phase 3 — Linguistic Feature Extraction (complete)

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Refactored `sentence_segmenter.py` to expose `parse_document()` and
      attach the spaCy `Span` to each `Sentence`, so Phase 3 feature
      extraction reuses the existing parse instead of re-parsing text
      (Section 5/21: load/parse once, reuse)
- [x] `backend/app/services/feature_extractor.py`:
  - Sentence-level: word/char/punctuation counts, average word length,
    noun/verb/adj/adv/pronoun ratios, dependency-tree depth
  - Essay-level: sentence-length mean/std/coefficient-of-variation,
    short/medium/long sentence-length distribution, type-token ratio,
    moving-average type-token ratio, rare-word ratio (via `wordfreq`),
    repeated-bigram ratio, repeated-trigram ratio, repeated-sentence-
    opening ratio
- [x] DEC-006 recorded (**Provisional**): feature scope and computation
      methods, including why `wordfreq` was chosen for word rarity over
      spaCy's own (unpopulated, in the small model) lexeme probabilities
- [x] 12 new tests covering sentence-level counts/ratios, dependency
      depth, essay-level length statistics, bucket ratios summing to 1,
      TTR sensitivity to repetition, bigram-repetition detection (present
      and absent), sentence-opening repetition, rare-word-ratio contrast,
      and empty-essay input — all passing (34 total across the backend)
- [x] Documentation updated: `architecture.md`, `decisions.md`,
      `decision-summary.md`, `final-decision-guide.md`

## In Progress

- [ ] None — Phase 3 is complete. Phase 4 has not started.

## Experiments

None yet. Phase 3's feature *values* are computed and unit-tested for
correctness, but their actual discriminative signal (human vs. AI vs.
mixed) has not been measured — that requires the Phase 5 dataset and is
tracked as EXP-002 (see DEC-006, status: Provisional, "Revisit When").

## Current Known Problems

- No feature has been validated against real data yet. DEC-006 is
  explicitly Provisional for this reason — do not treat the current
  feature list as final or as evidence of anything until EXP-002 runs.
- The application still does not classify or score essays.
- `docs/methodology.md`, `docs/dataset.md`, `docs/evaluation.md`,
  `docs/failure-analysis.md`, and `docs/fairness.md` remain intentional
  placeholders.
- `extract_essay_features` takes the whole `Doc` for essay-wide token
  stats (TTR, rare-word ratio) but per-sentence word counts for the
  length-distribution features come from each `Sentence.span` — this is
  intentional (keeps essay-level stats and sentence-level stats
  consistent with the same filtered token set) but means the function
  signature couples to `sentence_segmenter.Sentence` rather than being
  fully generic; acceptable at this scope, noted in case it becomes
  awkward once `analyzer.py` (Phase 7) orchestrates everything.

## Decisions Pending

- Local causal LM choice and loading/caching strategy (Phase 4)
- Dataset sources and generation approach (Phase 5)
- Which Phase 3 features are actually retained once EXP-002 can be run
  (Phase 5/6, per DEC-006)
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps

1. Phase 4: local language-model instrumentation —
   `backend/app/services/language_model.py`:
   - Choose and load a small local causal LM (e.g. distilgpt2), once per
     process (mirroring the spaCy loading pattern already used in
     `sentence_segmenter.get_nlp()`)
   - Compute per-sentence mean/median token log-probability, perplexity,
     token-probability variance, and predictability change between
     neighboring sentences
   - Record the model choice and loading/caching strategy as a decision
2. Begin Phase 5 (dataset) planning in parallel where needed, since real
   signal validation for both Phase 3 and Phase 4 features depends on it.
3. Update this file at the end of Phase 4.
