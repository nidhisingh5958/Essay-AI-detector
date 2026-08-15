# AI Detector for Admissions Essays

> **Status: research phase complete, production pipeline built and
> running end-to-end (2026-08-15).** Backend API, frozen detector,
> deterministic evidence mapping, and frontend are all implemented and
> tested. See [docs/project-status.md](docs/project-status.md) for the
> authoritative, continuously-updated record of exactly what has been
> built, tested, and verified.

## Overview

A web application that analyzes admissions essays for measurable,
explainable evidence about their writing characteristics — sentence by
sentence and passage by passage — instead of producing a single opaque
"AI probability."

## What this detects, and what it doesn't

**Can**: statistically distinguish whole-essay human writing from
whole-essay AI generation, using measurable stylometric features
(vocabulary diversity, repetition, sentence rhythm, word length,
punctuation density, syntactic structure). This has been shown to hold
across two architecturally distinct AI writing models
([reports/GEN-001.md](reports/GEN-001.md)), not just the one used to
build the detector. It surfaces sentence-level candidate passages with
real, above-chance (but imprecise) signal.

**Cannot**: reliably detect lightly AI-assisted/edited writing at the
essay level (this was tested and found to fail —
[reports/EXP-003C.md](reports/EXP-003C.md)); identify a specific
sentence as AI-written with certainty (roughly 5 in 6 flagged
sentences, at the recall-favoring configuration tested, are not the
true AI-touched one — [reports/EXP-003B.md](reports/EXP-003B.md));
claim universal AI detection (tested against exactly two generation
models); or claim to be "fair" (an evaluation found no detected
disparity across one proficiency variable, but the sample was too small
to rule out a smaller one — [reports/FAIR-001.md](reports/FAIR-001.md)).

See [docs/PRODUCT-AUDIT.md](docs/PRODUCT-AUDIT.md) §2–4 for the full,
evidence-cited breakdown of what the product can and cannot claim.

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
  documented, frozen dataset,
- produces an essay-level result and ranked, sentence-level candidate
  passages with explicit uncertainty, and
- shows the actual numbers behind every flag.

## Why this is not an LLM wrapper

A local language model is used only as an **instrument** — to extract
measurable quantities like token log-probability and perplexity. It is
never asked "is this AI-written?" and it never generates the
explanations shown to the user. All classification, scoring, and evidence
text come from our own code operating on computed features, a frozen
logistic-regression model, and a deterministic template layer. See
[docs/decisions/DEC-004-no-llm-classifier.md](docs/decisions/DEC-004-no-llm-classifier.md)
and [docs/decisions/DEC-017-evidence-explanation-mapping.md](docs/decisions/DEC-017-evidence-explanation-mapping.md)
for the full reasoning, and
[docs/alternatives-considered.md](docs/alternatives-considered.md) for
other rejected approaches.

## Core architecture

See [docs/architecture.md](docs/architecture.md) for the full pipeline
diagram and file-by-file layout. Summary:

```
Essay → normalization → sentence segmentation
      → [linguistic features | local LM instrumentation]
      → 29-feature vector → frozen detector (logistic regression)
      → deterministic evidence mapping → structured API response → web UI
```

Repo layout:

```
backend/     FastAPI app: production inference pipeline (Python)
frontend/    Next.js + TypeScript + Tailwind UI
data/        Dataset working directory (gitignored; populated by scripts/)
scripts/     Dataset construction, experiment-running, and model-artifact-build scripts (research only — never imported by backend/app/)
experiments/ Reproducible experiment configs + results (EXP-003A/B/B-R1/C, GEN-001, FAIR-001)
reports/     Full experiment reports (one per experiment, never overwritten)
docs/        Architecture, methodology, dataset, evaluation, fairness,
             failure analysis, API/frontend docs, and the full decision log
```

## Features

- Paste an essay and get an essay-level result: a strong machine-
  generated signal was detected, no strong signal was detected, or the
  result is inconclusive (insufficient evidence — never a fabricated
  score)
- Ranked, sentence-level candidate passages ("potentially AI-assisted"),
  each highlighted in the essay text with its own evidence
- Deterministic, traceable evidence for every result — every statement
  maps to a real, measured feature value compared against a human-
  reference range, never an LLM-generated explanation
- Explicit limitations always shown alongside the result

## Setup

### Prerequisites

- Python 3.11+ (developed against 3.14)
- Node.js 20+ / npm
- No external paid API required — inference runs entirely locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Build the frozen model artifacts** (one-time; not committed to git —
see [docs/production-detector.md](docs/production-detector.md) for why):

```bash
cd ../scripts
python3 build_essay_detector_artifact.py
python3 build_sentence_detector_artifact.py
python3 build_feature_reference_stats.py
```

These deterministically reproduce (not retrain) EXP-003A's and
EXP-003B's already-frozen models from the tracked research feature
files, and verify the reproduction against the recorded results before
writing anything — see the scripts themselves and
[production-detector.md](docs/production-detector.md) for the exact
verification performed. **Requires `data/generated/PRIMARY-DATASET-v1/`
and the `experiments/EXP-003A/` / `experiments/EXP-003B/` feature files
to be present** (see "Dataset setup" below if starting from a completely
fresh clone).

**Run the API**:

```bash
cd ../backend
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
cp .env.local.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if the backend runs elsewhere
npm run dev
```

Open http://localhost:3000. Paste an essay, click Analyze — the full
pipeline runs against the locally-running backend.

Run tests: `npm test` (from `frontend/`).
Production build check: `npm run build`.

### Model setup (the LM instrument)

The local language model (`distilgpt2`, see
[docs/decisions/DEC-007-local-language-model-choice.md](docs/decisions/DEC-007-local-language-model-choice.md))
downloads automatically from the Hugging Face Hub the first time
`backend/app/services/language_model.py` runs, and is cached locally
afterward (`~/.cache/huggingface/`) — no manual download step, but the
very first run needs network access. It is used strictly as a
measurement instrument, never to classify.

### Dataset setup

`PRIMARY-DATASET-v1` (150 families, 425-sample benchmark, PERSUADE 2.0 +
ELLIPSE) has been built, frozen, and used for all six experiments — see
[docs/dataset.md](docs/dataset.md) for full construction detail and
[docs/decisions/DEC-009-human-dataset-source.md](docs/decisions/DEC-009-human-dataset-source.md)
for source licensing. The raw/generated dataset itself is gitignored
(never committed) — a fresh clone needs `scripts/acquire_dataset.py`
(Kaggle API credentials required) and the generation pipeline
(`scripts/run_primary_dataset_v1.py`) to reproduce it from scratch. The
already-computed feature files the production build scripts need
(`experiments/EXP-003A/features.jsonl`, etc.) **are** tracked in git.

### Running experiments

All six planned/approved experiments have run — see
[docs/decision-summary.md](docs/decision-summary.md) for a one-page
summary of every result, or `reports/EXP-003A.md` /
`reports/EXP-003B.md` / `reports/EXP-003B-R1.md` /
`reports/EXP-003C.md` / `reports/GEN-001.md` / `reports/FAIR-001.md`
for full detail on each. No further research experiment is currently
authorized (see [docs/PRODUCT-AUDIT.md](docs/PRODUCT-AUDIT.md) for the
research-to-product handoff and why).

## Evaluation

See [docs/evaluation.md](docs/evaluation.md) for the full metrics
structure and where each number comes from. Headline: near-perfect
whole-essay AI-generation detection (EXP-003A/GEN-001), effectively no
signal for lightly-assisted essay-level classification (EXP-003B/C),
real but imprecise sentence-level localization signal (EXP-003B/B-R1).

## Failure analysis

See [docs/failure-analysis.md](docs/failure-analysis.md) — three real,
documented failure cases (a recurring individual-essay false positive
across four experiments, the `ai_assisted` essay-level collapse, and
the LM feature group's degradation under cross-generator transfer), none
invented, none hidden.

## Fairness

See [docs/fairness.md](docs/fairness.md) and
[reports/FAIR-001.md](reports/FAIR-001.md). No material disparity was
detected across the one available English-proficiency variable
(`ell_status`) — explicitly bounded: the sample (n=10 in the smaller
group) can only rule out a large disparity, not a smaller one. Not a
general fairness certification.

## Limitations (current, production)

- Essay-level classification is binary (human vs. `full_ai`) only — the
  system does not expose a three-way essay-level classifier, because
  `ai_assisted` essay-level classification was tested and found to
  collapse completely (EXP-003C).
- Sentence-level candidate passages carry real signal (60% top-1 test
  accuracy vs. ~8% chance) but are not proof — most essays will surface
  a handful of candidates, not a definitive list.
- Tested against exactly two generation models (Qwen2.5-1.5B-Instruct,
  Phi-3.5-mini-instruct) — not a claim of universal AI detection.
- The LM-derived feature group (perplexity, predictability) has not
  demonstrated incremental value over stylometric features alone, across
  four independent experiments — kept in the frozen model because it's
  the only configuration with a complete validation-threshold-selection
  procedure behind it, not because its contribution is proven.
- Fairness evaluation is limited by a small available sample (n=10) —
  an absence of detected disparity is not proof of fairness.
- distilgpt2 is a small model; its probability estimates are noisier
  than a larger model's would be — an accepted, documented trade-off.

## Decision-making approach

Every non-trivial architectural, ML, data, or product decision is
recorded in [docs/decisions/](docs/decisions/) with alternatives
considered, evidence, trade-offs, and a condition for revisiting it. See
[docs/decision-summary.md](docs/decision-summary.md) for a quick table and
[docs/alternatives-considered.md](docs/alternatives-considered.md) for
approaches rejected outright. No decision claims experimental support it
doesn't have — provisional decisions are marked as such, and several
remain intentionally Provisional/open rather than force-resolved.

## Documentation guide

| Document | Purpose |
|---|---|
| [docs/PRODUCT-AUDIT.md](docs/PRODUCT-AUDIT.md) | Research-to-product synthesis: what the detector can/cannot claim, architecture audit, phased implementation plan |
| [docs/architecture.md](docs/architecture.md) | System design, as built |
| [docs/production-detector.md](docs/production-detector.md) | The frozen model artifacts: exact config, build/verification process |
| [docs/evidence-mapping.md](docs/evidence-mapping.md) | Sentence ranking + deterministic evidence-mapping design |
| [docs/api.md](docs/api.md) | `POST /api/analyze` request/response schema, errors, examples |
| [docs/frontend.md](docs/frontend.md) | Frontend architecture, user flow, offset-safety details |
| [docs/methodology.md](docs/methodology.md) | What the system measures vs. infers |
| [docs/dataset.md](docs/dataset.md) | Provenance, licensing, splits, limitations |
| [docs/evaluation.md](docs/evaluation.md) | Metrics and results, per experiment |
| [docs/failure-analysis.md](docs/failure-analysis.md) | Confidently-wrong examples |
| [docs/fairness.md](docs/fairness.md) | English-proficiency fairness analysis |
| [docs/decisions/](docs/decisions/) | Full decision log (DEC-001 through DEC-019) |
| [docs/decision-summary.md](docs/decision-summary.md) | One-table skim of all decisions and experiment headlines |
| [docs/alternatives-considered.md](docs/alternatives-considered.md) | Rejected whole-approach alternatives |
| [docs/final-decision-guide.md](docs/final-decision-guide.md) | Plain-language walkthrough of dataset construction |
| [docs/project-status.md](docs/project-status.md) | Phase-by-phase progress, source of truth for "what exists" |

## Future improvements

Tracked as the "Decisions Pending" / "Next Steps" sections of
[docs/project-status.md](docs/project-status.md). No further research
experiment, model retraining, or new feature is currently authorized —
see [docs/PRODUCT-AUDIT.md](docs/PRODUCT-AUDIT.md) for the standing
research-freeze rationale.
