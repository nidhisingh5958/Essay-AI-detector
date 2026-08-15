# Decision Summary

Quick-reference table for reviewers. Full reasoning lives in
[`decisions/`](decisions/).

**Post-R3 strategic decision (2026-08-13), executed 2026-08-14/15,
approved and FROZEN 2026-08-15**: the generation-methodology phase
(DEC-011/012/013) concluded with a category-specific decision for
primary dataset construction, and `PRIMARY-DATASET-v1` (150 families,
425-sample benchmark) has been built and approved as the immutable v1
benchmark — see [final-decision-guide.md](final-decision-guide.md) for
the one-page summary, [dataset.md](dataset.md) for the plan, and
[reports/FINAL-DATASET-CONSTRUCTION.md](../reports/FINAL-DATASET-CONSTRUCTION.md)
for actual results. In short: `sentence_light_controlled_v2` used with
mandatory human review (127/141 preserved, 90.1%);
`sentence_moderate_controlled_v2` and both paragraph-level categories
excluded (insufficient semantic reliability, evidence preserved);
DEC-012/DEC-013 reframed as risk-triage tools, not a semantic safety
gate — the construction run found this screen's miss rate is worse at
scale than previously documented (75% of real sentence-level "changed"
samples missed). **EXP-003A executed 2026-08-15** (human vs. full_ai,
298 essays) — see [reports/EXP-003A.md](../reports/EXP-003A.md).
Headline: stylometric features alone separate the two classes almost
perfectly (test: 45–46/46 depending on threshold); **the LM instrument
added no measurable value**, directly confirming DEC-004's standing
warning against assuming "low perplexity = AI." Scoped explicitly to
this benchmark and this one generation model — not general AI
detection. **EXP-003B executed 2026-08-15** (human vs. ai_assisted,
essay-level + sentence-localization, evaluated separately) — see
[reports/EXP-003B.md](../reports/EXP-003B.md). Headline: **essay-level
detection fails (chance-level; frozen-threshold test result worse than
the majority baseline)** — full-AI detection does not transfer to
lightly-assisted writing. **Sentence-level localization shows real
signal** (86.7% test recall at 17.6% precision; 60% top-1 per-essay
accuracy on test vs. 25% validation, noisy). **EXP-003B-R1 executed
2026-08-15** (diagnostic, reuses EXP-003B's sentence-level dataset
unchanged) — see [reports/EXP-003B-R1.md](../reports/EXP-003B-R1.md).
Headline: **localization signal survives removing length/count
features** (non-length-only reaches 46.7% top-1 test accuracy,
comparable to length/count-only's 40.0%, both far above the ~8% chance
rate); **genuine LM predictability features alone are the weakest
group tested (13.3%)** — a second data point against the LM
instrument's current usefulness, keeping DEC-004 open rather than
resolved. `lm_mean_token_count` reclassified as a length/count feature,
not predictability evidence.

**EXP-003C executed 2026-08-15** (three-class: human/full_ai/
ai_assisted, essay-level, merged from cached feature vectors — no new
extraction) — see [reports/EXP-003C.md](../reports/EXP-003C.md).
Headline: **`full_ai` remains essentially perfect (23/23 test recall);
`ai_assisted` collapses completely (0/16 correct, 15 absorbed into
`human`)** — overall accuracy 72.6%, macro-F1 0.564. LM group again
added zero measurable value (identical to stylometric-only on
validation) — a third independent confirmation. Per-sample probability
inspection shows real but weak `ai_assisted` signal the plain-argmax
decision rule can't yet use. Scoped to this benchmark, this generation
model only.

**FAIR-001 and GEN-001 remain DESIGNED / NOT EXECUTED**
([FAIR-001](experiments/FAIR-001.md), [GEN-001](experiments/GEN-001.md),
DEC-018/019) — approved execution order is EXP-003C → GEN-001 →
FAIR-001; only EXP-003C has run so far, per the explicit stop condition.

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
| DEC-012 | Automated semantic-risk screening/triage signal (Accepted, triage only — never ground truth, never a safety gate) | Embedding similarity (`all-MiniLM-L6-v2`) + entity/number check (spaCy), combined so a fact-check flag always escalates to review; thresholds calibrated against 35 real reviewed samples, not invented | NLI/entailment model | Numeric/entity substitution detection is reliable (0 misses across calibration, R2, R3, and PRIMARY-DATASET-v1). Reversal-type drift is not: R3 found 2/3 changed paragraph samples missed; **PRIMARY-DATASET-v1 found this is WORSE at sentence-level scale — 6/8 (75%) of real "changed" samples missed at n=141**, vs. 0/1 at R3's n=25. NLI is now evidenced at two granularities as a future candidate, not implemented |
| DEC-013 | Paragraph-level claim-survival screening signal (Accepted, screening only — validated against real true-positive AND false-negative cases) | Per-sentence embedding best-match coverage + aggregate fact-check on the full paragraph pair; two-state label (`no_omission_signal` / `possible_omission_flagged`) | Lowering DEC-012's whole-paragraph similarity threshold | An aggregate similarity score is the wrong tool for a dropped-single-sentence failure by construction. **R3 validation**: caught 1 real claim-drop correctly; missed 2/3 changed samples that were reversals or claim-drop-merged-with-a-flip inside one sentence — same blind spot as DEC-012, confirming both need a reversal-sensitive signal (NLI) to close the gap |
| DEC-014 | EXP-003 feature set & baselines (Provisional, design-only) | Every IMPLEMENTED feature (feature-inventory.md), no fabricated additions; 3 baselines (majority, stylometric-only, LM-only) | Filter features by intuition before measuring signal | Operationalizes DEC-004's deferred "does the LM instrument help beyond stylometry" question as a concrete 3-way baseline comparison, using only already-implemented, tested code |
| DEC-015 | EXP-003 model selection & threshold strategy (Provisional, design-only) | L2-regularized logistic regression (primary) + random forest (secondary nonlinearity check, not auto-preferred); threshold selected on validation only, frozen before test | Deep neural network; gradient boosting as primary | 425 samples is too small for a deep model without severe overfitting; logistic regression's coefficients directly serve DEC-017's evidence-mapping requirement |
| DEC-016 | Sentence-level localization evaluation design (Provisional, design-only) | Ground truth from exact stored `modified_spans` provenance, never inferred by similarity; precision/recall/F1/confusion matrix reported separately from essay-level metrics | Infer AI-touched sentences via diff/similarity | Diff-based sentence attribution was already rejected once (DEC-011's Post-Pilot Methodology Redesign) for being unreliable/ambiguous; exact provenance already exists in the data |
| DEC-017 | Evidence/explanation mapping design (Provisional, design-only) | Fixed, deterministic template layer: feature value → normalized measurement → evidence statement; no generative model ever produces explanation text | Post-hoc LLM-generated natural-language explanation | Extends DEC-004's "LM is an instrument, never the judge" constraint to the explanation layer — an LLM-written explanation would be un-auditable against the actual feature values it claims to describe |
| DEC-018 | FAIR-001 fairness evaluation methodology (Provisional, design-only) | PERSUADE `ell_status`, joined via `family_id` in a separate table; score ALL 150 families with the already-frozen model (not just the 23-family test split); small-sample threshold (n<10 → "insufficient data") fixed in advance | Only evaluate on the frozen test split; wait for an ELLIPSE-based extension | Test-split alone has only 1 `ell_status=Yes` family — meaningless for any rate comparison. Scoring all 150 (10 `Yes` total) doesn't touch model development, only reads the already-frozen model's output on more inputs |
| DEC-019 | GEN-001 held-out generator selection (Provisional, design-only) | Phi-3.5-mini-instruct (MIT, local, free) as the held-out generator; reuse PRIMARY-DATASET-v1's existing 23 test-split human essays unmodified, generate only new `full_ai` counterparts; `full_ai` category only for this first pass | A different-size Qwen variant (rejected — not sufficiently different, same vendor/family); a hosted API model (deferred — real cost, less reproducible, revisits DEC-010's vendor-lock-in concerns) | Genuinely different vendor/corpus/architecture from Qwen while staying local/free/reproducible, matching this project's standing model-choice preference (DEC-007/010) |

This table will grow through later phases (feature selection, scoring
method, calibration, dataset splitting, fairness methodology, etc.) as
those decisions are made and recorded.
