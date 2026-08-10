# DEC-003 — Single Repository (Monorepo) Layout

## Status
Accepted

## Date
2026-08-10

## Context

The project has a Python backend/ML pipeline, a TypeScript frontend, a
dataset pipeline (`scripts/`, `data/`), and reproducible experiments
(`experiments/`). All of these evolve together — a change to the
`/api/analyze` response shape affects the frontend types, and a change to
feature extraction affects both experiments and the API.

## Problem

Should the frontend, backend, dataset pipeline, and experiments live in one
repository or be split across multiple repositories?

## Alternatives Considered

### Alternative A: Single repository with top-level `backend/`, `frontend/`,
`data/`, `scripts/`, `experiments/`, `reports/`, `docs/`
Advantages:
- One PR can change the API contract and the frontend consumer together.
- Documentation (`docs/`) and decision records can reference code across
  both halves of the stack without cross-repo links.
- Simpler for a hackathon-scale project: one clone, one place to look.

Disadvantages:
- Backend and frontend dependency installs are separate regardless
  (Python venv vs npm), so the monorepo doesn't unify tooling — it's
  purely an organizational choice.

### Alternative B: Separate repositories (`ai-detector-backend`,
`ai-detector-frontend`, `ai-detector-experiments`)
Advantages:
- Independent versioning/release cycles — irrelevant here since both
  halves ship together as one product.

Disadvantages:
- Splits the reasoning trail (Section 24 of the brief) across
  repositories, making it harder for an evaluator to see the full
  decision history in one place.
- Adds coordination overhead (matching commits/branches across repos)
  with no corresponding benefit at this project's size and single-team
  ownership.

## Decision

Single repository, organized as `backend/`, `frontend/`, `data/`,
`scripts/`, `experiments/`, `reports/`, `docs/`.

## Why

The project is developed and evaluated as one product by one team; nothing
requires independent deployment or versioning of its parts. A single repo
keeps the documentation-code-experiment traceability the brief requires
(Section 34) inside one browsable tree.

## Evidence

Structural decision, not empirically tested — driven directly by the
project brief's traceability requirements (Sections 24, 29, 34).

## Trade-offs

Backend and frontend still need separate dependency installs and separate
dev servers (no unified build tool like Turborepo/Nx was introduced) —
accepted because the project doesn't have enough shared tooling need to
justify that additional complexity.

## Consequences

Positive:
- One place for an evaluator to read code, docs, decisions, and
  experiments together.

Negative:
- No enforced type-sharing between backend Pydantic models and frontend
  TypeScript types; they must be kept in sync by hand (documented as a
  known limitation, not solved with a codegen tool, since the API surface
  is currently a single endpoint).

## Revisit When

If the API surface grows large enough that manual type-syncing between
`backend/app/models/` and `frontend/types/` becomes error-prone — at that
point, consider generating TypeScript types from the Pydantic/OpenAPI
schema.

## Implementation

Repository root layout: `backend/`, `frontend/`, `data/`, `scripts/`,
`experiments/`, `reports/`, `docs/`.

## Tests / Experiments

N/A — structural decision.
