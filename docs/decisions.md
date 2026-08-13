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
| [DEC-007](decisions/DEC-007-local-language-model-choice.md) | Local LM choice: distilgpt2 | Accepted |
| [DEC-008](decisions/DEC-008-lm-scoring-method.md) | LM scoring: whole-essay single pass, not per-sentence | Accepted |
| [DEC-009](decisions/DEC-009-human-dataset-source.md) | Human dataset source: PERSUADE 2.0 + ELLIPSE | Provisional |
| [DEC-010](decisions/DEC-010-machine-generation-model.md) | Machine text generation model: Qwen2.5-1.5B-Instruct | Provisional (pilot-tested) |
| [DEC-011](decisions/DEC-011-mixed-text-generation.md) | Mixed/AI-assisted text generation methodology | Provisional — category-specific (sentence-light confirmed at scale, promising; paragraph not ready; sentence-moderate not ready, redesign drafted) |
| [DEC-012](decisions/DEC-012-semantic-preservation-screen.md) | Automated semantic-preservation screening signal | Accepted (screening only, never ground truth) |
| [DEC-013](decisions/DEC-013-claim-survival-screen.md) | Paragraph-level claim-survival screening signal | Accepted (screening only — validated R3: 1 true positive caught, 2 false negatives on reversal-type drift) |

This table grows as later phases introduce feature-selection, scoring,
calibration, dataset, and fairness-methodology decisions.
