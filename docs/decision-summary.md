# Decision Summary

Quick-reference table for reviewers. Full reasoning lives in
[`decisions/`](decisions/).

**Post-R3 strategic decision (2026-08-13)**: the generation-methodology
phase (DEC-011/012/013) has concluded with a category-specific decision
for primary dataset construction — see
[final-decision-guide.md](final-decision-guide.md) for the one-page
summary and [dataset.md](dataset.md) for the (not-yet-executed)
construction plan. In short: `sentence_light_controlled_v2` approved
with mandatory human review; `sentence_moderate_controlled_v2` and both
paragraph-level categories excluded (insufficient semantic reliability,
evidence preserved); DEC-012/DEC-013 reframed as risk-triage tools, not
a semantic safety gate.

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
| DEC-011 | Mixed-sample generation mechanism (Provisional — category-specific verdict, not combined) | Three ground-truth regimes (A/B surgical splice, C whole-essay essay-level-only). **R3 (2026-08-13): sentence-light-v2 confirmed at 2.5x scale — 25 fresh seeds, 22/25 (88%) preserved, 1/25 (4%) changed (a caught numeric substitution), promising. Paragraph claim-survival validation — 12 fresh seeds: light 9/12 preserved/2/12 changed, moderate 8/12 preserved/1/12 changed; 2 of 3 changed samples were reversal/merge-type drift that BOTH automated screens missed entirely — not ready for scale, evidence got stronger, not weaker. Sentence-moderate not re-run; 3 redesign candidates drafted, not tested** | Sequence-alignment (`difflib`) to rescue whole-essay diffing into sentence labels | Structural QC alone cannot catch semantic drift (validated, permanent finding); full-paragraph context plus controlled temperature sharply improved sentence-level results; R3 confirms sentence-light holds at scale while showing paragraph-level drift the screens can't yet catch (meaning reversals, not just dropped/changed facts) |
| DEC-012 | Automated semantic-preservation screening signal (Accepted, screening only — never ground truth) | Embedding similarity (`all-MiniLM-L6-v2`) + entity/number check (spaCy), combined so a fact-check flag always escalates to review; thresholds calibrated against 35 real reviewed samples, not invented | NLI/entailment model | Embedding similarity alone misses precise factual substitution (e.g. "one C"→"two Cs" scores ~0.87, too similar); 0/8 calibration, 0/5 R2 out-of-sample — but **R3 broke this for the first time**: 2/3 changed paragraph samples (meaning reversals touching no number/entity) scored `likely_preserved`. Safety property holds for numeric/entity substitution across all 3 rounds; does not hold for reversal-type drift — NLI now a live candidate, not just deferred |
| DEC-013 | Paragraph-level claim-survival screening signal (Accepted, screening only — validated against real true-positive AND false-negative cases) | Per-sentence embedding best-match coverage + aggregate fact-check on the full paragraph pair; two-state label (`no_omission_signal` / `possible_omission_flagged`) | Lowering DEC-012's whole-paragraph similarity threshold | An aggregate similarity score is the wrong tool for a dropped-single-sentence failure by construction. **R3 validation**: caught 1 real claim-drop correctly; missed 2/3 changed samples that were reversals or claim-drop-merged-with-a-flip inside one sentence — same blind spot as DEC-012, confirming both need a reversal-sensitive signal (NLI) to close the gap |

This table will grow through later phases (feature selection, scoring
method, calibration, dataset splitting, fairness methodology, etc.) as
those decisions are made and recorded.
