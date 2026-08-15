# Production API — Phase E

**Status: executed 2026-08-15.** Exposes the already-frozen Phase B/C/D
pipeline through a single FastAPI endpoint. This layer contains **no
detection logic** — it validates, orchestrates, and serializes; every
number in a response comes from
[production-detector.md](production-detector.md) /
[evidence-mapping.md](evidence-mapping.md)'s already-verified pipeline.

## Endpoint

```
POST /api/analyze
GET  /api/health
```

## Request schema

```json
{ "text": "string, required" }
```

No other fields are accepted or needed. Model configuration (`C`,
threshold, feature set) is never client-configurable — the detector is
frozen (Phase B/immutable constraints).

## Response schema

```json
{
  "analysis_id": "uuid4 string — an opaque request identifier only, NOT part of the analysis result",
  "normalized_text": "the exact string every char_start/char_end offset below refers to",
  "essay": {
    "state": "machine_signal_detected | no_strong_signal_detected | inconclusive",
    "score": 0.49,
    "state_explanation": "fixed disclaimer text — see 'Score semantics' below",
    "evidence": [
      {
        "feature": "stylo_type_token_ratio",
        "human_label": "vocabulary diversity",
        "observed_value": 0.926,
        "reference_mean": 0.464,
        "reference_std": 0.066,
        "direction": "higher",
        "contribution": 0.448,
        "statement": "This shows a higher level of vocabulary diversity than the reference range used by the detector (observed 0.926 vs. a human-reference average of 0.464)."
      }
    ],
    "limitation_note": "fixed scope-limitation text"
  },
  "sentences": {
    "candidates": [
      { "sentence_index": 4, "rank": 1, "text": "...", "char_start": 120, "char_end": 210, "score": 0.71, "label": "potentially_ai_assisted", "evidence": [ /* same EvidenceItem shape as above */ ] }
    ],
    "skipped": [
      { "sentence_index": 0, "text": "...", "char_start": 0, "char_end": 45, "reason": "missing features: ('lm_mean_predictability_delta',)" }
    ],
    "top_k": 3,
    "total_scorable_sentences": 12,
    "has_evidence": true,
    "no_evidence_reason": null,
    "disclaimer": "The highlighted passages indicate statistical patterns associated with the detector's reference data. They are not proof that AI wrote the passage."
  },
  "metadata": {
    "essay_model_version": "essay-detector-v1-2026-08-15",
    "essay_source_experiment": "EXP-003A",
    "sentence_model_version": "sentence-detector-v1-2026-08-15",
    "sentence_source_experiment": "EXP-003B"
  }
}
```

**Deliberately NOT exposed** (item 3/18): the model's `C`, its raw
numeric threshold (0.47), the full 29-feature vector, or any model
artifact file path. `state` alone conveys the threshold relationship
qualitatively. Verified by test
(`test_response_never_exposes_model_C_threshold_or_raw_feature_vector`)
that these values/strings never appear in a real response body.

## Example request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Your essay text here..."}'
```

## Error responses

| Status | Cause | Example detail |
|---|---|---|
| 422 | Empty or whitespace-only text; missing/malformed `text` field | `"Essay text is empty."` |
| 413 | Text exceeds `max_essay_chars` (20,000 — existing, already-tested Phase 1 limit, not newly invented) | `"Essay exceeds the maximum supported length of 20000 characters (received 20001)."` |
| 503 | Detector artifact unavailable (should only occur if the service is misconfigured — startup fails loudly if this is the case at boot) | `"Analysis service is not ready. Please try again shortly."` |
| 500 | Any unexpected internal error | `"An unexpected error occurred while analyzing this essay."` — never a raw stack trace or file path |

No case returns a fake/fabricated analysis — every non-200 response
carries no `essay`/`sentences` payload at all.

## Score semantics

*"This score reflects the detector's learned distinction between the
human-written and AI-generated essays in its reference data
(PRIMARY-DATASET-v1, EXP-003A) — it is not a universal probability that
AI wrote this specific essay."* (returned verbatim as
`essay.state_explanation`.)

## Sentence semantics

Every ranked candidate carries `label: "potentially_ai_assisted"` —
never `"ai_written"`, `"definitely_ai"`, or any authorship-certainty
claim. *"The highlighted passages indicate statistical patterns
associated with the detector's reference data. They are not proof that
AI wrote the passage."* (returned verbatim as `sentences.disclaimer`.)

## Privacy behavior

Essay text is processed **in memory only** — never written to disk, a
database, or any persistent store by this API. Server-side logging
records only the essay's character length, never its content
(`app/api/analyze.py`'s `logger.info` call). No telemetry or external
analytics of any kind.

## Model limitations (carried forward, not softened)

*The detector identifies statistical patterns associated with its
reference data. It does not establish authorship.* Specifically: scoped
to full-essay AI-generation detection against PERSUADE-derived human
essays and Qwen2.5-1.5B-Instruct/Phi-3.5-mini-instruct generated essays
(EXP-003A, GEN-001); does not reliably classify lighter AI-assistance/
editing at the essay level (EXP-003B/C); sentence-level candidates carry
real but imprecise signal (60% top-1 accuracy, EXP-003B/B-R1) — most
essays will surface at most `top_k` (default 3) candidates, not an
exhaustive or certain list.

## Determinism

The same input text produces an identical `essay`/`sentences`/`metadata`
payload on every call — `analysis_id` is the sole exception (a fresh
UUID per request, explicitly documented as an identifier, not part of
the analysis). Verified by test
(`test_L_repeated_identical_requests_produce_identical_analysis`).

## Model loading / lifecycle

Both frozen model artifacts are loaded once, at FastAPI's `lifespan`
startup event (`app/main.py`) — not on the first request, and never
reloaded per-request (verified:
`test_P_repeated_requests_reuse_the_same_loaded_artifact_object`). If
an artifact is missing or unloadable, **application startup fails
loudly** — the service never starts in a partially-loaded state. A
mid-process failure (e.g. filesystem issue after a successful start)
returns 503 on the affected request rather than a fabricated result.

## Performance (measured, not optimized)

| Scenario | Time |
|---|---|
| `GET /api/health` | ~2 ms |
| First `/api/analyze` request (cold spaCy/distilgpt2 load — model artifacts already preloaded at startup, but spaCy/distilgpt2 are lazy-loaded on first actual use) | ~2.9 s |
| Second request, short essay (warm) | ~63 ms |
| Representative multi-paragraph essay (~1,576 chars, 23 sentences, warm) | ~330 ms |
| Same essay, repeated (warm) | ~297 ms |

No caching was added — not required by these measurements (item 17: "do
not add caching unless required by actual measurements"). The
essay-level and sentence-level detectors each require their own
feature-extraction pass over the same text (different granularity, two
separate frozen models per the Phase B/C design) — this is an inherent,
disclosed cost of the two-detector architecture, not something Phase E
attempted to restructure (out of scope: "orchestration and
serialization ONLY... must NOT contain new detection logic").

## Health endpoint

`GET /api/health` returns `{"status": "ok", "app": "...",
"detector_loaded": true|false}` — a cheap, in-memory check
(`lru_cache.cache_info().currsize`) that never triggers model
inference (verified:
`test_Q_health_endpoint_does_not_run_inference`).

## CORS

Unchanged from Phase 1: `http://localhost:3000` only (the local Next.js
dev server), all methods/headers allowed for that single origin — no
wildcard origin. Documented as a development configuration to be
tightened before any real deployment (existing comment in `main.py`,
not modified by this phase).
