# Decision Log — Index

Individual decision records live in [`decisions/`](decisions/), one file
per decision, using the format described below. This index just lists them
in order; see [decision-summary.md](decision-summary.md) for a quick
skim-table and [alternatives-considered.md](alternatives-considered.md) for
approaches that were evaluated and rejected outright (rather than adopted
with trade-offs, as recorded here).

## Format

Each decision record (`DEC-XXX-title.md`) follows: Status, Date, Context,
Problem, Alternatives Considered, Decision, Why, Evidence, Trade-offs,
Consequences, Revisit When, Implementation, Tests/Experiments.

## Records

| ID | Title | Status |
|----|-------|--------|
| [DEC-001](decisions/DEC-001-backend-framework.md) | Backend framework: FastAPI | Accepted |
| [DEC-002](decisions/DEC-002-frontend-framework.md) | Frontend framework: Next.js | Accepted |
| [DEC-003](decisions/DEC-003-monorepo-layout.md) | Single repository layout | Accepted |
| [DEC-004](decisions/DEC-004-no-llm-classifier.md) | LM as instrument, never classifier | Accepted |
| [DEC-005](decisions/DEC-005-sentence-segmentation.md) | Sentence segmentation: spaCy statistical pipeline | Accepted |
| [DEC-006](decisions/DEC-006-phase3-feature-scope.md) | Phase 3 feature scope and computation methods | Provisional |

This table grows as later phases introduce feature-selection, scoring,
calibration, dataset, and fairness-methodology decisions.
