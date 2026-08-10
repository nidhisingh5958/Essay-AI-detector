# AI Detector for Admissions Essays

> **Status: Phase 1 of 15 (scaffold complete).** This README describes the
> full intended project. Sections describing analysis, results,
> evaluation, and fairness findings are explicitly marked "not yet
> implemented" where that's the case — see
> [docs/project-status.md](docs/project-status.md) for exactly what exists
> today versus what is planned.

## Overview

A web application that analyzes admissions essays for measurable,
explainable evidence about their writing characteristics — sentence by
sentence and passage by passage — instead of producing a single opaque
"AI probability."

## Problem statement

Admissions readers increasingly want to know whether an essay reflects a
student's own writing. Existing "AI detector" tools typically hide their
reasoning behind a single percentage with no supporting evidence, are
poorly calibrated, and are often just a wrapper around asking a large
language model for a verdict. That approach is not evaluable, not
explainable, and not something a reader can meaningfully act on.

This project instead builds a pipeline that:

- computes real, measurable features of the text (predictability,
  sentence rhythm, vocabulary, repetition, syntactic patterns),
- compares those features against reference distributions built from a
  documented dataset,
- produces sentence- and passage-level classifications with explicit
  uncertainty, and
- shows the actual numbers behind every flag.

## Why this is not an LLM wrapper

A local language model is used only as an **instrument** — to extract
measurable quantities like token log-probability and perplexity. It is
never asked "is this AI-written?" and it never generates the
explanations shown to the user. All classification, scoring, and evidence
text come from our own code operating on computed features and reference
distributions. See
[docs/decisions/DEC-004-no-llm-classifier.md](docs/decisions/DEC-004-no-llm-classifier.md)
for the full reasoning, and
[docs/alternatives-considered.md](docs/alternatives-considered.md) for
other rejected approaches (LLM-as-classifier, RAG, multi-agent
architectures, single-threshold detectors, end-to-end fine-tuned
classifiers).

## Core architecture

See [docs/architecture.md](docs/architecture.md) for the full pipeline
diagram and current implementation status. Summary:

```
Essay → normalization → sentence segmentation
      → [linguistic features | local LM instrumentation]
      → feature vector → reference-distribution comparison
      → explainable scoring → sentence/passage classification
      → evidence generation → web UI
```

Repo layout:

```
backend/     FastAPI app + NLP/ML pipeline (Python)
frontend/    Next.js + TypeScript + Tailwind UI
data/        Dataset working directory (gitignored; populated by scripts/)
scripts/     Dataset build/clean/split scripts
experiments/ Reproducible experiment configs + results (EXP-001, EXP-002, ...)
reports/     Generated evaluation reports
docs/        Architecture, methodology, dataset, evaluation, fairness,
             failure analysis, and the full decision log
```

## Features (target — see project-status.md for what's built)

- Paste an essay and get sentence-level classification: likely human,
  likely AI-assisted/mixed, likely machine-generated, or uncertain
- Passage-level grouping of neighboring suspicious sentences
- Numerical evidence behind every flag (e.g. "perplexity is in the lowest
  8% of the human reference distribution")
- Explicit uncertainty — the system can report "insufficient evidence"
  instead of forcing a classification
- Support for mixed/AI-polished essays, not just 100%-human vs 100%-AI

## Setup

### Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+ / npm
- No external paid API required — inference runs locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt   # full ML stack; Phase 1 only needed the top 3 packages
python -m spacy download en_core_web_sm   # needed for sentence segmentation (Phase 2) and later POS/dependency features (Phase 3)
uvicorn app.main:app --reload --port 8000
```

Health check: `curl http://localhost:8000/api/health`

Run tests:

```bash
cd backend && source .venv/bin/activate && python -m pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The essay textarea works; the "Analyze"
button is intentionally disabled until the backend pipeline exists
(Phases 2–8).

### Model setup

Not yet applicable — the local language model is introduced in Phase 4.
See [docs/decisions/DEC-004-no-llm-classifier.md](docs/decisions/DEC-004-no-llm-classifier.md)
for the constraints it will be built under (local only, instrument only).

### Dataset setup

Not yet applicable — see [docs/dataset.md](docs/dataset.md) (Phase 5).

### Running experiments

Not yet applicable — no experiments have been run. See
[docs/project-status.md](docs/project-status.md) for the experiment plan
(EXP-001 through EXP-008) once Phases 3–7 exist to produce them.

## Evaluation

Not yet available. See [docs/evaluation.md](docs/evaluation.md) — it
documents the planned metrics and reporting structure, with an explicit
note that no numbers will be added until real experiments have run.

## Results

Not yet available (Phase 10).

## Failure analysis

Not yet available (Phase 11). See
[docs/failure-analysis.md](docs/failure-analysis.md) for the required
structure — at least three confidently-wrong examples will be documented
there once the system exists to fail.

## Fairness

Not yet available (Phase 12). See [docs/fairness.md](docs/fairness.md)
for the planned methodology around second-language English writers and
the constraint that no fairness claim will be made without an actual
evaluation on appropriately labeled data.

## Limitations (current, Phase 3)

- The system does not classify or score essays yet — Phases 2–3 only
  normalize text, validate input, split essays into sentences, and
  compute a provisional set of linguistic features (sentence rhythm,
  vocabulary, repetition, POS/dependency) per sentence and per essay.
- None of the Phase 3 features have been validated against real human/AI
  writing yet — that requires the Phase 5 dataset (see
  [docs/decisions/DEC-006-phase3-feature-scope.md](docs/decisions/DEC-006-phase3-feature-scope.md),
  marked Provisional).
- spaCy (`en_core_web_sm`) and `wordfreq` are installed and used. PyTorch,
  Transformers, and scikit-learn are still not installed in the working
  dev environment — they are exercised starting Phase 4/5.

## Decision-making approach

Every non-trivial architectural, ML, data, or product decision is
recorded in [docs/decisions/](docs/decisions/) with alternatives
considered, evidence, trade-offs, and a condition for revisiting it. See
[docs/decision-summary.md](docs/decision-summary.md) for a quick table and
[docs/alternatives-considered.md](docs/alternatives-considered.md) for
approaches rejected outright. No decision claims experimental support it
doesn't have — provisional decisions are marked as such.

## Documentation guide

| Document | Purpose |
|---|---|
| [docs/architecture.md](docs/architecture.md) | System design, current vs. planned |
| [docs/methodology.md](docs/methodology.md) | What the system measures vs. infers |
| [docs/dataset.md](docs/dataset.md) | Provenance, licensing, splits, limitations |
| [docs/evaluation.md](docs/evaluation.md) | Metrics and results (once run) |
| [docs/failure-analysis.md](docs/failure-analysis.md) | Confidently-wrong examples |
| [docs/fairness.md](docs/fairness.md) | Second-language-writer fairness analysis |
| [docs/decisions/](docs/decisions/) | Full decision log (DEC-XXX records) |
| [docs/decision-summary.md](docs/decision-summary.md) | One-table skim of all decisions |
| [docs/alternatives-considered.md](docs/alternatives-considered.md) | Rejected whole-approach alternatives |
| [docs/final-decision-guide.md](docs/final-decision-guide.md) | Plain-language walkthrough of the whole system |
| [docs/project-status.md](docs/project-status.md) | Phase-by-phase progress, source of truth for "what exists" |

## Future improvements

Tracked as the "Next Steps" section of
[docs/project-status.md](docs/project-status.md), updated at the end of
every phase.
