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

## What exists today (Phase 4)

- **Backend** (`backend/app/`): FastAPI app with a single `/api/health`
  endpoint (Phase 1). Phase 2 added text preprocessing:
  - `services/text_normalizer.py` — Unicode NFC normalization, line-ending
    normalization, control-character stripping. Deliberately does not
    touch punctuation/quote style, since those are candidate features.
  - `services/validation.py` — rejects empty/whitespace-only input and
    input over `Settings.max_essay_chars`.
  - `services/sentence_segmenter.py` — splits normalized text into
    sentences with character offsets, using a shared spaCy
    (`en_core_web_sm`) pipeline; also exposes `parse_document()` so the
    parsed `Doc` can be reused by feature extraction instead of
    re-parsing. See
    [decisions/DEC-005-sentence-segmentation.md](decisions/DEC-005-sentence-segmentation.md).

  Phase 3 adds linguistic feature extraction:
  - `services/feature_extractor.py` — `extract_sentence_features(span)`
    (word/char/punctuation counts, POS ratios, dependency-tree depth) and
    `extract_essay_features(doc, sentences)` (sentence-length statistics,
    type-token ratio, moving-average TTR, rare-word ratio via `wordfreq`,
    repeated-bigram/trigram ratios, repeated-sentence-opening ratio). See
    [decisions/DEC-006-phase3-feature-scope.md](decisions/DEC-006-phase3-feature-scope.md)
    — this feature set is explicitly **provisional**, not yet validated
    against real human/AI data.

  Phase 4 adds local language-model instrumentation:
  - `services/language_model.py` — loads `distilgpt2` once per process
    (see [decisions/DEC-007-local-language-model-choice.md](decisions/DEC-007-local-language-model-choice.md)),
    computes per-token log-probabilities for the whole essay in one
    (chunked-if-needed) forward pass, then attributes tokens back to
    sentences by character offset to produce per-sentence mean/median
    log-probability, perplexity, and log-probability variance, plus the
    change in predictability between neighboring sentences. See
    [decisions/DEC-008-lm-scoring-method.md](decisions/DEC-008-lm-scoring-method.md)
    for why whole-essay scoring was chosen over scoring each sentence in
    isolation. Per [DEC-004](decisions/DEC-004-no-llm-classifier.md), this
    model never classifies anything — it only produces the numbers above.

  `models/`, `ml/` still exist as placeholders for Phases 5–8. There is
  still no `/api/analyze` endpoint or orchestrating `analyzer.py` — Phase
  2/3/4 output (sentences, linguistic features, LM features) is not yet
  wired into a request/response flow, and no scoring exists yet to
  interpret any of these numbers.
- **Frontend** (`frontend/`): unchanged since Phase 1 — a landing page
  with a working textarea (`components/EssayInput/`) and a disabled
  "Analyze" button.
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
│   │   ├── text_normalizer.py    # exists (Phase 2)
│   │   ├── validation.py         # exists (Phase 2)
│   │   ├── sentence_segmenter.py # exists (Phase 2)
│   │   ├── feature_extractor.py  # exists (Phase 3)
│   │   ├── language_model.py     # exists (Phase 4)
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

## Model loading and performance

- Both the spaCy pipeline (`sentence_segmenter.get_nlp()`) and the
  distilgpt2 model/tokenizer (`language_model._load_model()`) are loaded
  once per process via `functools.lru_cache` and reused across requests —
  no per-sentence or per-request reload (Section 5/21).
- distilgpt2 is downloaded from the Hugging Face Hub on first use and
  cached locally (`~/.cache/huggingface/`) — the first run after a fresh
  environment setup needs network access; subsequent runs are fully
  offline.
- Essays are scored by the LM in a single forward pass in the common case
  (under ~1024 tokens); longer essays are chunked (DEC-008). The full test
  suite, including a ~1500-word chunked-essay test, runs in about 14
  seconds on a normal laptop CPU with both models loaded — no GPU
  required.
- Input length is capped (`Settings.max_essay_chars`, currently 20,000
  characters) to bound worst-case latency; not yet re-validated against
  measured end-to-end request latency, since there is no `/api/analyze`
  endpoint yet to measure (Phase 8).
