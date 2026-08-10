# DEC-002 — Frontend Framework

## Status
Accepted

## Date
2026-08-10

## Context

The product's core experience is "paste essay → analyze → inspect
highlighted sentences/passages with evidence." This is a single, fairly
rich interactive page (essay viewer with inline highlighting, an evidence
panel, feature breakdown bars) rather than a multi-page site or a
CRUD-heavy dashboard.

## Problem

Which frontend framework should build the essay input and results UI?

## Alternatives Considered

### Alternative A: Next.js (App Router) + TypeScript + Tailwind
Advantages:
- Explicitly recommended by the project brief (Section 3).
- App Router gives file-based routing for the small number of
  views we actually need (landing/input, results) without extra setup.
- TypeScript gives shared, checked types for the `/api/analyze` response
  shape (`frontend/types/`), reducing drift between backend and frontend.
- Tailwind is a good fit for the evidence bars / highlighting UI, which is
  mostly small, composable, utility-styled pieces rather than a heavy
  component library.

Disadvantages:
- Server-rendering machinery (RSC, server actions) is mostly unused here
  since the real work happens via a separate FastAPI backend — Next.js is
  being used largely as a SPA-style client. This is acceptable overhead,
  not a good fit mismatch.

### Alternative B: Plain React + Vite
Advantages:
- Lighter weight, faster dev server cold start, no unused SSR machinery.

Disadvantages:
- More manual setup (routing, TypeScript config, Tailwind wiring) for no
  functional benefit at this project's scope.
- Diverges from the brief's explicit recommendation without a concrete
  reason to.

### Alternative C: SvelteKit / other framework
Advantages:
- Smaller bundle sizes, different reactivity model.

Disadvantages:
- No team/project familiarity assumed, no ecosystem advantage for this
  specific UI (text highlighting + evidence panels), and again diverges
  from the brief without a driving reason.

## Decision

Use Next.js (App Router) + TypeScript + Tailwind CSS.

## Why

It is the framework named in the project brief, is well suited to the
actual UI shape (a handful of views built from composable pieces), and its
main theoretical downside (unused SSR features) has no real cost at this
scale.

## Evidence

Scaffolded via `create-next-app` and verified with `npm run build` — see
`frontend/`. Structural decision; no comparative experiment was run since
the brief already specifies this stack and no conflicting constraint
emerged during setup.

## Trade-offs

Server Components / server actions are available but not the primary
interaction model here — the frontend calls the FastAPI backend directly.
We accept a small amount of "unused framework surface" in exchange for
following the recommended, well-documented default.

## Consequences

Positive:
- Fast to scaffold, TypeScript end-to-end on the frontend, good Tailwind
  integration out of the box.

Negative:
- None identified yet at Phase 1.

## Revisit When

If the results UI grows complex enough that client-state management
becomes a real problem (unlikely at this project's scope — one input, one
results view).

## Implementation

`frontend/app/`, `frontend/components/`.

## Tests / Experiments

`npm run build` (verified during Phase 1 setup).
