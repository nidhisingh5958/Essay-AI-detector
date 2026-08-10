# Project Status

## Current Phase

Phase 1 — Repository and Architecture (complete)

## Completed

- [x] Repository structure established (`backend/`, `frontend/`, `data/`,
      `scripts/`, `experiments/`, `reports/`, `docs/`, `docs/decisions/`)
- [x] Backend skeleton: FastAPI app with `/api/health`, config module,
      one passing test (`backend/tests/test_health.py`)
- [x] Frontend skeleton: Next.js (App Router) + TypeScript + Tailwind,
      builds cleanly (`npm run build`), landing page with a functional
      textarea (`components/EssayInput/`) and an intentionally-disabled
      "Analyze" button (no backend endpoint exists to call yet)
- [x] Documentation structure created: `architecture.md`, `methodology.md`,
      `dataset.md`, `evaluation.md`, `failure-analysis.md`, `fairness.md`,
      `decisions.md`, `decision-summary.md`, `final-decision-guide.md`,
      `alternatives-considered.md`, this file
- [x] Initial decision log: DEC-001 (FastAPI), DEC-002 (Next.js), DEC-003
      (monorepo layout), DEC-004 (local LM as instrument only, never
      classifier)
- [x] Root README

## In Progress

- [ ] None — Phase 1 is complete. Phase 2 has not started.

## Experiments

None yet. No feature or model exists to experiment on.

## Current Known Problems

- The application does not analyze essays yet — this is expected at
  Phase 1, not a bug. The "Analyze" button is disabled deliberately.
- `docs/methodology.md`, `docs/dataset.md`, `docs/evaluation.md`,
  `docs/failure-analysis.md`, and `docs/fairness.md` are intentionally
  placeholders — they state what will be documented and when, and contain
  no fabricated numbers or conclusions.

## Decisions Pending

- Sentence segmentation approach (Phase 2)
- Which linguistic features to retain after measuring signal (Phase 3)
- Local causal LM choice and loading/caching strategy (Phase 4)
- Dataset sources and generation approach (Phase 5)
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps

1. Phase 2: text normalization, sentence segmentation, input validation
   (`backend/app/services/sentence_segmenter.py`), with tests covering
   edge cases (empty input, very short/long essays, Unicode, punctuation-
   heavy text).
2. Record the sentence-segmentation approach as a decision once
   alternatives are actually compared.
3. Update this file at the end of Phase 2.
