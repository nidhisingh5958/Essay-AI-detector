# Project Status

## Current Phase

Phase 2 — Text Preprocessing (complete)

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004 (see git history /
      earlier revision of this file for the full Phase 1 checklist)
- [x] Text normalization (`backend/app/services/text_normalizer.py`):
      Unicode NFC normalization, line-ending normalization, control-
      character stripping — deliberately preserves punctuation/quote style
      as candidate features
- [x] Input validation (`backend/app/services/validation.py`): rejects
      empty/whitespace-only text and text over `Settings.max_essay_chars`
- [x] Sentence segmentation (`backend/app/services/sentence_segmenter.py`):
      spaCy `en_core_web_sm` statistical pipeline, returns sentences with
      character offsets into the normalized text
- [x] DEC-005 recorded: sentence segmentation approach and why regex/NLTK/
      blank-spaCy alternatives were rejected
- [x] 17 new tests covering empty input, whitespace-only input, very short
      and very long essays, punctuation-heavy text (ellipses, multiple
      exclamation/question marks), abbreviations, Unicode (accents, emoji),
      duplicate sentences, and repeated phrases — all passing (22 total
      across the backend)
- [x] Documentation updated to reflect Phase 2: `architecture.md`,
      `decisions.md`, `decision-summary.md`, `final-decision-guide.md`,
      root `README.md`

## In Progress

- [ ] None — Phase 2 is complete. Phase 3 has not started.

## Experiments

None yet. Phase 2 is preprocessing infrastructure, not a measurable
feature/model choice — nothing here required an experiment (see DEC-005's
Evidence section for why sentence segmentation didn't need one either).

## Current Known Problems

- The application still does not classify or score essays — Phase 2 only
  produces normalized text and sentence boundaries. This is expected, not
  a bug.
- `docs/methodology.md`, `docs/dataset.md`, `docs/evaluation.md`,
  `docs/failure-analysis.md`, and `docs/fairness.md` remain intentional
  placeholders — nothing in Phase 2 changes that.
- The full `en_core_web_sm` pipeline (tagger, parser, attribute_ruler,
  lemmatizer, ner, tok2vec) is loaded even though only parser-derived
  sentence boundaries are used so far. This is intentional (see DEC-005:
  the same pipeline will be reused for Phase 3 POS/dependency features),
  not an oversight, but it does mean Phase 2 alone pays for pipeline
  components it doesn't yet use.

## Decisions Pending

- Which linguistic features to retain after measuring signal (Phase 3)
- Local causal LM choice and loading/caching strategy (Phase 4)
- Dataset sources and generation approach (Phase 5)
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps

1. Phase 3: linguistic feature extraction —
   `backend/app/services/feature_extractor.py`:
   - Sentence rhythm (length, variance, coefficient of variation,
     punctuation distribution)
   - Vocabulary (type-token ratio, moving-average TTR, rare-word ratio)
   - Repetition (repeated n-grams, repeated sentence openings)
   - POS/dependency features using the same spaCy pipeline already loaded
     for segmentation
2. Investigate which of these features actually carry signal before
   committing to a final feature set (Section 6 of the project brief) —
   this requires at least a small reference dataset, so Phase 3 and the
   start of Phase 5 (dataset) may need to interleave in practice; record
   that as a decision if/when it happens rather than silently reordering
   phases.
3. Update this file at the end of Phase 3.
