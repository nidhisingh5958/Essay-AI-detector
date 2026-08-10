# Architecture

> Status: Phase 1 (scaffold). This document describes both what exists
> today and what the planned pipeline is; each section is labeled.
> See [project-status.md](project-status.md) for the authoritative
> phase-by-phase progress.

## System overview (planned)

```
                    ESSAY
                      |
                      v
             Text Normalization
                      |
                      v
             Sentence Segmentation
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Linguistic Features      Language Model
          |                 (instrument only —
          |                  see DEC-004)
          |                       |
          +-----------+-----------+
                      |
                      v
                Feature Vector
                      |
                      v
              Feature Normalization
                      |
                      v
     Comparison to Reference Distributions
                      |
                      v
             Explainable Scoring
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Sentence-Level Scores      Passage Analysis
          |                       |
          +-----------+-----------+
                      |
                      v
              Evidence Generation
                      |
                      v
              Overall Assessment
                      |
                      v
                   WEB UI
```

The scoring and evidence-generation stages are our own code, not an LLM
call — see [decisions/DEC-004-no-llm-classifier.md](decisions/DEC-004-no-llm-classifier.md)
for why.

## What exists today (Phase 1)

- **Backend** (`backend/app/`): FastAPI app with a single `/api/health`
  endpoint. No analysis pipeline yet — `services/`, `models/`, `ml/`
  directories exist as placeholders for Phases 2–7.
- **Frontend** (`frontend/`): Next.js (App Router) + TypeScript + Tailwind.
  A landing page with a working textarea (`components/EssayInput/`) and a
  disabled "Analyze" button — there is no `/api/analyze` endpoint to call
  yet.
- **Data/experiments/scripts/reports**: empty directories reserved for
  Phases 5, 10 per [project-status.md](project-status.md).

## Backend layout (planned, per Section 4 of the project brief)

```
backend/
├── app/
│   ├── main.py            # FastAPI app, routing (exists — health check only)
│   ├── config.py          # settings (exists)
│   ├── api/                # route handlers (Phase 8)
│   ├── models/             # Pydantic request/response schemas (Phase 8)
│   ├── services/
│   │   ├── analyzer.py           # orchestrates the pipeline (Phase 7)
│   │   ├── sentence_segmenter.py # Phase 2
│   │   ├── feature_extractor.py  # Phase 3
│   │   ├── language_model.py     # Phase 4
│   │   ├── scoring.py            # Phase 6
│   │   ├── passage_analyzer.py   # Phase 7
│   │   └── evidence.py           # Phase 6/7
│   ├── ml/                 # reference distributions, calibration artifacts (Phase 5/6)
│   └── config.py
└── tests/
```

Directories are created ahead of the code that fills them so the intended
module boundaries are visible from Phase 1, but empty placeholder files
are not committed speculatively — each `services/*.py` file is added in
the phase that actually implements it.

## Frontend layout

```
frontend/
├── app/                 # routes: landing/input (exists), results (Phase 9)
├── components/
│   ├── EssayInput/       # exists (Phase 1)
│   ├── EssayViewer/      # Phase 9 — sentence/passage highlighting
│   ├── EvidencePanel/    # Phase 9
│   ├── FeatureBreakdown/ # Phase 9
│   └── ResultsSummary/   # Phase 9
├── lib/                  # API client (Phase 8/9)
└── types/                # shared response types (Phase 8/9)
```

## API flow (planned)

`POST /api/analyze` — see [decisions.md](decisions.md) and the root
README for the target request/response shape. Not implemented yet; will
be added in Phase 8 once scoring (Phase 6) and passage analysis (Phase 7)
exist to actually populate the response.

## Model loading and performance (planned constraints)

- The local causal LM is loaded once at process startup and reused across
  requests (no per-sentence reload) — see Section 5/21 of the project
  brief. To be implemented in `backend/app/services/language_model.py`
  (Phase 4), with its own decision record once a concrete loading/caching
  strategy is chosen.
- Input length is capped (`Settings.max_essay_chars`, currently 20,000
  characters) to bound worst-case latency; this limit may be revisited
  once real inference latency is measured in Phase 4.
