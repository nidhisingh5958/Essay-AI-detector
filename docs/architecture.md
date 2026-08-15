# Architecture

> Status: **executed, 2026-08-15.** The pipeline below is built and
> running end-to-end (research → frozen models → API → frontend). This
> document is the high-level map; see
> [production-detector.md](production-detector.md),
> [evidence-mapping.md](evidence-mapping.md), [api.md](api.md), and
> [frontend.md](frontend.md) for full detail on each stage.
> [project-status.md](project-status.md) remains the authoritative,
> up-to-date phase-by-phase record.

## System overview (as built)

```
                    ESSAY (frontend textarea)
                      |
                      v
              POST /api/analyze  (backend/app/api/analyze.py — orchestration only)
                      |
                      v
             Text Normalization        (services/text_normalizer.py)
                      |
                      v
             Sentence Segmentation     (services/sentence_segmenter.py, spaCy)
                      |
          +-----------+-----------+
          |                       |
          v                       v
 Linguistic Features      Language Model
 (services/feature_        (services/language_model.py,
  extractor.py)             distilgpt2 — instrument only,
          |                 never a classifier — DEC-004)
          |                       |
          +-----------+-----------+
                      |
                      v
        29-feature vector (essay-mean-pooled or per-sentence —
        services/essay_feature_vector.py / sentence_feature_vectors.py)
                      |
                      v
        Frozen detector (services/detector.py)
        — essay-level: EXP-003A's frozen L2 logistic regression
        — sentence-level: EXP-003B's frozen ranking model
        (both loaded once from backend/app/ml/*.joblib, built by
        scripts/build_*_detector_artifact.py, verified to reproduce
        the exact frozen research results — see production-detector.md)
                      |
                      v
        Deterministic evidence mapping (services/evidence_mapper.py)
        — feature -> reference comparison -> fixed template -> statement
        — NEVER an LLM call (DEC-017) — see evidence-mapping.md
                      |
                      v
        Structured JSON response (models/api_schemas.py)
                      |
                      v
                   Frontend (Next.js) — ResultsSummary, EssayViewer,
                   EvidencePanel, Limitations — see frontend.md
```

The scoring and evidence-generation stages are entirely our own code —
never an LLM call for classification or explanation. See
[decisions/DEC-004-no-llm-classifier.md](decisions/DEC-004-no-llm-classifier.md)
and [decisions/DEC-017-evidence-explanation-mapping.md](decisions/DEC-017-evidence-explanation-mapping.md).

## Backend layout (as built)

```
backend/
├── app/
│   ├── main.py                     # FastAPI app, CORS, lifespan model preload, /api/health
│   ├── config.py                   # settings (max_essay_chars, etc.)
│   ├── api/
│   │   └── analyze.py              # POST /api/analyze — orchestration/serialization only
│   ├── models/
│   │   ├── api_schemas.py          # public request/response Pydantic schemas
│   │   ├── detector_results.py     # internal detector result dataclasses
│   │   └── evidence_results.py     # internal evidence-mapper result dataclasses
│   ├── services/
│   │   ├── text_normalizer.py      # Unicode/line-ending normalization
│   │   ├── validation.py           # length validation
│   │   ├── sentence_segmenter.py   # spaCy-based segmentation with offsets
│   │   ├── feature_extractor.py    # the 23 stylometric feature computations
│   │   ├── language_model.py       # distilgpt2 instrument (log-prob, perplexity)
│   │   ├── feature_spec.py         # THE canonical 29-feature name/order spec
│   │   ├── essay_feature_vector.py # essay-level (mean-pooled) 29-feature vector
│   │   ├── sentence_feature_vectors.py # per-sentence 29-feature vectors
│   │   ├── detector.py             # loads frozen .joblib artifacts, inference only
│   │   └── evidence_mapper.py      # deterministic feature -> evidence statements
│   └── ml/                         # frozen model artifacts (gitignored, built by scripts/)
└── tests/                          # 123 tests — unit + integration + API-level
```

`scripts/*.py` (research/experiment code — dataset construction, model
training/evaluation, artifact-building) is never imported by anything
under `backend/app/` — the one-way dependency is: `scripts/` may import
`backend/app/services/*` (research reuses production's tested feature
functions), never the reverse. Verified by an AST-based test
(`test_api_modules_do_not_import_research_or_training_code`).

## Frontend layout (as built)

```
frontend/
├── app/
│   └── page.tsx              # orchestrator: wires useEssayAnalysis to the components below
├── components/
│   ├── EssayInput/            # controlled textarea + Analyze button
│   ├── EssayViewer/            # normalized-text rendering + highlighted candidate passages
│   ├── EvidencePanel/          # reused for both essay- and sentence-level evidence
│   ├── ResultsSummary/         # essay-level state + score + evidence
│   ├── Limitations/            # fixed honesty section
│   ├── StatusMessage/          # loading/error banners
│   └── FeatureBreakdown/       # deliberately empty — folded into EvidencePanel (no separate dashboard)
├── lib/
│   ├── api.ts                  # the sole fetch() call in the app
│   ├── useEssayAnalysis.ts     # explicit state model
│   └── textOffsets.ts          # code-point-safe offset slicing (see frontend.md)
└── types/
    └── api.ts                  # types mirroring the backend response exactly
```

## API flow (as built)

`POST /api/analyze` — request `{text: string}`, response includes essay
state/score/evidence, ranked sentence candidates + skipped sentences +
`normalized_text`, and version metadata. Full schema, error codes, and
example request/response: [api.md](api.md).

## Model loading and performance

- Both frozen model artifacts (`backend/app/ml/*.joblib`) are loaded
  once at FastAPI `lifespan` startup and reused for every request — see
  `production-detector.md` for the build/verification process and
  `api.md`'s Performance section for measured (not estimated) latency:
  health ~2ms, warm short essay ~50-65ms, warm representative essay
  (~1,500 chars) ~270-330ms.
- The spaCy pipeline and distilgpt2 model/tokenizer are loaded once per
  process via `functools.lru_cache`, exactly as originally planned in
  Phase 4 — unchanged since then.
- distilgpt2 is downloaded from the Hugging Face Hub on first use and
  cached locally (`~/.cache/huggingface/`) — first run needs network
  access, subsequent runs are fully offline.
- Input length is capped at 20,000 characters
  (`Settings.max_essay_chars`), enforced both frontend and backend,
  returning HTTP 413 when exceeded (`api.md`).
