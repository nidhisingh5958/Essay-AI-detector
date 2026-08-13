# Project Status

## Current Phase

**Generation-methodology phase concluded with a strategic, category-
specific decision for primary dataset construction (2026-08-13, post-R3
review).** The primary dataset construction PLAN is now documented
([docs/dataset.md](dataset.md)) but **NOT executed** — no large-scale
generation has run. **Stopped for review** per explicit instruction —
no scaling, no detector work, no EXP-003, no NLI added experimentally.

## Completed

- [x] Phases 1–5, 5B — repo scaffold, text pipeline, feature extraction,
      LM instrumentation, dataset acquisition/inspection, generation
      design (see prior status history for detail).
- [x] EXP-DATA-001 (60 samples) → redesign into 3 ground-truth regimes →
      EXP-DATA-001-R1 (18 records, n=3) →
      EXP-DATA-001-R1-confirmation (50 records, n=10): found the
      headline, permanent finding — **structural QC can pass samples
      that nevertheless alter the author's meaning**.
- [x] EXP-DATA-001-R2 (60 records): designed and calibrated the DEC-012
      automated semantic-preservation screen; redesigned sentence-level
      generation with full-paragraph context and controlled temperature;
      paragraph re-validation found a new claim-omission failure mode.
      [reports/EXP-DATA-001-R2.md](../reports/EXP-DATA-001-R2.md).
- [x] EXP-DATA-001-R3 (86 records, two separate experiments): confirmed
      `sentence_light_controlled_v2` at 2.5x scale (25 seeds: 88%
      preserved, 4% changed); added the DEC-013 paragraph claim-survival
      screen and found it — together with DEC-012 — misses meaning-
      reversal drift (2/3 changed paragraph samples missed, the first
      break in this project's "0 changed mislabeled preserved" record).
      Two real extraction bugs found and fixed in shared screening
      infrastructure. [reports/EXP-DATA-001-R3.md](../reports/EXP-DATA-001-R3.md).
- [x] **This update — post-R3 strategic decision + primary dataset
      construction plan (2026-08-13):**
  - **Category-specific decision for the primary dataset** (DEC-011
    "Strategic Decision" section):
    - `sentence_light_controlled_v2` — **approved for controlled dataset
      construction, with mandatory semantic review** (not a claim of
      perfect safety).
    - `sentence_moderate_controlled_v2` — **excluded**:
      "Insufficient semantic reliability for primary dataset
      construction." May be revisited as future work.
    - `paragraph_light_controlled` / `paragraph_moderate_controlled` —
      **excluded**: "Promising structural mechanism but insufficient
      semantic reliability for primary dataset construction." Nothing
      deleted or hidden — all experiments and failures remain fully
      documented.
  - **DEC-012 and DEC-013 reframed**: from implying a "safety property"
    to explicitly **"automated semantic-risk screening / triage"** —
    never a semantic safety gate, never a substitute for human review.
    The pipeline is now documented explicitly: automated screening →
    risk triage → mandatory human semantic review → final ground truth.
    The screen never overrides review; `"changed"`/`"questionable"`
    samples are excluded from the high-confidence dataset regardless of
    the screen's label.
  - **NLI explicitly deferred, not added**: documented as a possible
    future screening enhancement (DEC-012 Alternative B), not
    implemented — per explicit instruction not to add it just to try to
    recover the broken safety-property framing.
  - **`docs/dataset.md`** (new) — the primary dataset construction plan:
    150 fresh families (proposed, adjustable), categories A (human) + B
    (`full_ai`) + C (`sentence_light_controlled_v2`, preserved-only),
    family/split strategy (unchanged 70/15/15 family-level invariant),
    deduplication, mandatory semantic-review protocol, and explicit
    rejected/questionable-sample retention (never discarded, never used
    as positive ground truth). **Design only — not executed.**
  - **`docs/final-decision-guide.md`** (new) — one-page summary of
    what's in/out and why, for quick reference.
  - Documentation updated: `generation-methodology.md` (status banner),
    `failure-analysis.md` (pointer to the strategic decision, evidence
    chain preserved), `decision-summary.md`, `decisions.md`, DEC-011,
    DEC-012, DEC-013.

## In Progress

- [ ] **Stopped for review, as explicitly instructed.** Not generating
      the primary dataset yet, not scaling to thousands of samples, not
      training/evaluating a detector, not running EXP-003, not adding
      NLI experimentally.
- [ ] Primary dataset generation (per `docs/dataset.md`) — plan
      documented, execution not authorized yet.
- [ ] Sentence-moderate instruction redesign — 3 candidates drafted, not
      tested; not part of the primary dataset regardless.
- [ ] A reversal-sensitive screening signal (NLI) for paragraph-level —
      documented as future work, not designed or implemented.

## Experiments

- `EXP-DATA-001` — 60 samples, 2026-08-10. Preserved.
- `EXP-DATA-001-R1` — 18 records, n=3/category, 2026-08-10.
- `EXP-DATA-001-R1-confirmation` — 50 records, n=10/category, 2026-08-10.
- `EXP-DATA-001-R2` — 60 records (2×30), n=10/category, two separate
  paragraph/sentence experiments, 2026-08-13.
- `EXP-DATA-001-R3` — 86 records (50 sentence-light + 36 paragraph
  claim-survival), n=25/12, two separate experiments, 2026-08-13.

All five are data-generation-pipeline validation experiments — the
evidence base for the strategic decision above. None involves a
detector; no detection accuracy/F1/generalization claim is made from
any of them. **The primary dataset itself (`docs/dataset.md`) has not
yet been generated.**

## Current Known Problems

- **Both automated semantic screens (DEC-012, DEC-013) have a confirmed
  blind spot for meaning-reversal and claim-drop-merged-with-a-flip
  drift** — this is exactly why they are reframed as triage tools and
  why mandatory human review is a hard requirement for the primary
  dataset, not a recommendation.
- **Sentence-moderate and paragraph-level are excluded from the primary
  dataset** — not a temporary gap, a scoped decision; revisiting either
  requires new evidence, not just a request to include them.
- Semantic review still has one reviewer (the agent operating this
  pipeline) — no inter-rater reliability figure exists across any round.
  This is a real constraint on how much manual review capacity the
  primary dataset's mandatory-review requirement can draw on.
- `full_ai` still hasn't been re-exercised with the fixed leakage check
  in any live run since the original bug was found — relevant since
  `full_ai` is Category B of the primary dataset plan.
- EXP-DATA-001's original Regime C similarity range (0.07–0.97) predates
  the `autojunk` fix and should be read as approximate.
- EXP-DATA-001-R2's paragraph-level `automated_screen_*` values were
  computed before the two `extract_span_pair` bugs found in R3 were
  fixed — frozen and not recomputed, but should be read with that
  caveat (see DEC-012's "Known Issue" note).
- PERSUADE's `word_count` column unreliability, 4 duplicate
  `essay_id_comp` values, and the general PERSUADE/ELLIPSE domain
  mismatch with real admissions essays remain unchanged (documented
  since Phase 5C).
- The application still does not classify or score essays.

## Decisions Pending

- Authorization to execute `docs/dataset.md`'s primary dataset
  construction plan (currently design-only).
- Sentence-moderate instruction redesign: which of the 3 drafted
  candidates (or another) to test, and under what controlled experiment
  — independent of the primary dataset, future work.
- A reversal-sensitive screening signal for paragraph-level (NLI,
  DEC-012 Alternative B) — design not started, future work.
- Whether the model itself (Phi-3.5-mini-instruct escalation, DEC-010)
  needs testing.
- Whether/how ELLIPSE (fairness corpus, DEC-009) factors into this
  primary dataset vs. a separate fairness-evaluation set — not decided.
- Which Phase 3/4 features are retained once EXP-002/EXP-003 can run.
- Scoring/calibration method (Phase 6).
- Passage-grouping strategy (Phase 7).

## Next Steps (pending review — not started)

1. User reviews the strategic decision, `docs/dataset.md`, and
   `docs/final-decision-guide.md`.
2. If approved: execute the primary dataset construction plan (150
   fresh families, per `docs/dataset.md`) — generation, QC, mandatory
   semantic review, then a written report of actual results (not a
   promise these projected rates will hold exactly).
3. Sentence-moderate redesign testing and the NLI reversal-detection
   signal remain separate future-work tracks, not blockers for the
   primary dataset.
4. Continue to hold off on any detector work (training, evaluation,
   EXP-003) until the primary dataset itself exists and is reviewed.
