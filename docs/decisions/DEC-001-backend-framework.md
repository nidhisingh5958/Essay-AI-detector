# DEC-001 — Backend Framework

## Status
Accepted

## Date
2026-08-10

## Context

The backend needs to serve a REST API (`/api/analyze`) and host the NLP/ML
pipeline: sentence segmentation, feature extraction, a local language model,
and a scoring system. The ML ecosystem we plan to use (Hugging Face
Transformers, PyTorch, spaCy, scikit-learn) is Python-native.

## Problem

Which backend framework and language should serve the API and host the
analysis pipeline?

## Alternatives Considered

### Alternative A: FastAPI (Python)
Advantages:
- Same language as the ML/NLP stack — no cross-process/cross-language
  serialization needed to call Transformers, spaCy, or scikit-learn.
- Async support for I/O-bound work; typed request/response models via
  Pydantic map directly onto the structured `/api/analyze` response shape.
- Automatic OpenAPI docs, useful for iterating on the response schema.

Disadvantages:
- Python's GIL means CPU-bound inference (LM forward passes) blocks the
  event loop unless offloaded to a worker/thread — needs explicit handling
  once real inference is added (Phase 4).

### Alternative B: Node.js / Express (or Next.js API routes only)
Advantages:
- One language across frontend and backend.
- Simpler deployment (single Next.js app for a demo).

Disadvantages:
- No mature first-party equivalent to Transformers/spaCy/scikit-learn.
  Running the LM and NLP pipeline would require shelling out to Python
  anyway, or using less mature JS ML bindings — adds complexity rather
  than removing it.

### Alternative C: Django (Python)
Advantages:
- Batteries-included (ORM, admin), good for larger CRUD-heavy apps.

Disadvantages:
- The project has no real persistence/CRUD requirements yet (SQLite usage
  is limited to experiment/reference-distribution storage). Django's
  weight is not justified. FastAPI is a better fit for a
  request-in/JSON-out analysis API.

## Decision

Use FastAPI (Python) for the backend.

## Why

The dominant constraint is that the entire ML/NLP pipeline (Transformers,
PyTorch, spaCy, scikit-learn) is Python-only. Keeping the API layer in the
same language avoids an unnecessary process boundary between "serve HTTP"
and "run inference," which would otherwise force IPC or a second service
just to reach the model.

## Evidence

No experiments were needed for this decision — it follows directly from
the required ML stack (Section 3 of the project brief) being Python-based.
This is a structural/ecosystem decision, not one to be resolved empirically.

## Trade-offs

- We give up a single-language (TypeScript) full stack.
- CPU-bound inference must be explicitly kept off the main event loop
  (thread pool / process pool) — deferred to Phase 4 when the LM is wired
  in, and will get its own decision record if a non-trivial approach is
  needed.

## Consequences

Positive:
- Direct, in-process access to Transformers/spaCy/scikit-learn without
  serialization overhead.
- Pydantic models double as API schema and internal data contracts.

Negative:
- Two languages in the repo (Python backend, TypeScript frontend) —
  acceptable, this is a normal ML-product split.

## Revisit When

If profiling in Phase 4 shows FastAPI's async model fighting the inference
workload badly enough that a worker-queue architecture (e.g. separate
inference service) becomes necessary. Not expected at this project's scale
(single essay, on-demand analysis, no high concurrency requirement).

## Implementation

`backend/app/main.py`, `backend/app/config.py`.

## Tests / Experiments

`backend/tests/test_health.py`.
