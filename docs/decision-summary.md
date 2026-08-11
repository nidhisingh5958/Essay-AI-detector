# Decision Summary

Quick-reference table for reviewers. Full reasoning lives in
[`decisions/`](decisions/).

| ID | Decision | Chosen Approach | Main Alternative | Why |
|----|----------|------------------|-------------------|-----|
| DEC-001 | Backend | FastAPI (Python) | Node.js/Express | Whole ML stack (Transformers, spaCy, scikit-learn) is Python-only; avoids a cross-language boundary just to reach the model |
| DEC-002 | Frontend | Next.js + TypeScript + Tailwind | Plain React + Vite | Matches the actual UI shape (few views, composable evidence widgets) and the brief's recommendation |
| DEC-003 | Repo layout | Single monorepo | Separate repos per component | Keeps code, docs, decisions, and experiments cross-referenceable in one tree |
| DEC-004 | Language model role | Local LM as feature-extraction instrument only; scoring is our own code | LLM-as-classifier | Explainability requires measurable features, not an opaque verdict; local-only avoids paid API dependency |
| DEC-005 | Sentence segmentation | spaCy `en_core_web_sm` statistical pipeline | Regex/rule-based splitting | Handles abbreviations/punctuation correctly; same pipeline reused for Phase 3 POS/dependency features, keeping boundaries consistent |
| DEC-006 | Phase 3 feature scope (Provisional) | Rhythm/vocabulary/repetition/POS features now, via `wordfreq` for rarity; signal validation deferred | Wait for Phase 5 dataset before writing any feature code | Dataset scripts themselves need feature machinery; each feature is literature-grounded even without labeled data yet |
| DEC-007 | Local LM choice | `distilgpt2` | `gpt2` (small) | Brief-suggested, fastest local CPU option, same tokenizer family as gpt2 for an easy upgrade path |
| DEC-008 | LM scoring method | Whole-essay single pass, tokens attributed to sentences by offset | Score each sentence independently | Preserves true preceding-document context, needed for the neighboring-sentence predictability-change signal; fewer forward passes |
| DEC-009 | Human dataset source (**Accepted** 2026-08-10 — live-verified + inspected) | PERSUADE 2.0 (primary) + ELLIPSE (fairness) | Official "Essays That Worked" examples | Best domain match (real admissions essays) had licensing/consent problems that disqualified it; PERSUADE/ELLIPSE have live-confirmed CC BY-NC-SA 4.0 licenses, and inspection confirmed both are usable (with documented data-quality caveats) |
| DEC-010 | Machine generation model (Provisional, pilot-tested) | Qwen2.5-1.5B-Instruct (local) | Hosted API (GPT-4o-mini/Claude/Gemini) | Local, free, reproducible, instruction-tuned; EXP-DATA-001 confirmed good quality for full-generation + surgical splice; hosted API still reserved for a future held-out generalization test only |
| DEC-011 | Mixed-sample generation mechanism (Provisional — redesigned + targeted-validated) | Three ground-truth regimes: surgical sentence/paragraph splice (Regimes A/B, exact truth, instruction intensity is just a parameter) vs. whole-essay (Regime C, essay-level-only, never sentence metrics) | Sequence-alignment (`difflib`) to rescue whole-essay diffing into sentence labels | EXP-DATA-001 found whole-essay polish's sentence attribution is genuinely ambiguous (70% structure drift, no separable similarity distribution), not just hard to threshold — a better alignment algorithm doesn't resolve that ambiguity, so sentence-level light/moderate examples now go through the same controlled-span mechanism as surgical rewrite instead |

This table will grow through later phases (feature selection, scoring
method, calibration, dataset splitting, fairness methodology, etc.) as
those decisions are made and recorded.
