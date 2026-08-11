# Project Status

## Current Phase

EXP-DATA-001-R1 complete (targeted redesign validation, executed for
real). **Stopped for review** per explicit instruction — no scaling, no
detector work, no EXP-003 started.

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Phase 3 — Linguistic feature extraction, sentence + essay level
      (DEC-006, Provisional)
- [x] Phase 4 — Local language-model instrumentation via `distilgpt2`
      (DEC-007, DEC-008)
- [x] Phase 5 — Human dataset source evaluation, acquisition pipeline,
      live acquisition + inspection
      ([DEC-009](decisions/DEC-009-human-dataset-source.md): Accepted)
- [x] Phase 5B — Machine/mixed generation design
      ([DEC-010](decisions/DEC-010-machine-generation-model.md),
      [DEC-011](decisions/DEC-011-mixed-text-generation.md))
- [x] EXP-DATA-001 — full pilot executed (60 samples). Found the
      whole-essay-instruction-plus-diff mechanism for light/moderate
      polish unreliable for sentence-level ground truth (70% structural
      drift). Findings preserved:
      [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md).
- [x] **This update — QC fix, DEC-011 redesign, and EXP-DATA-001-R1:**
  - Repo-local `.kaggle/kaggle.json` re-confirmed deleted; only
    `~/.kaggle/access_token` remains; nothing ever tracked.
  - **QC bug fixed**: `check_prompt_leakage` → `check_instruction_leakage`
    (takes meta-instruction-only argument, never prompt/target content)
    + new `check_ai_self_reference` (searches anywhere in text, not just
    as a preamble). 6 new tests added, including a preserved regression
    test reproducing the original false-positive bug and asserting the
    fix resolves it. `run_exp_data_001.py` patched to use the fix
    (not re-run in full — see below).
  - **DEC-011 redesigned, not patched with a threshold**: formalized
    three ground-truth regimes —
    - **Regime A** (surgical sentence transformation, exact truth):
      `sentence_rewrite_single` (unchanged) plus two **new** categories,
      `sentence_light_controlled` / `sentence_moderate_controlled` — same
      splice mechanism, lighter instruction wording, ground truth stays
      exact because the mechanism (not the wording) is what guarantees it.
    - **Regime B** (surgical paragraph transformation, exact truth):
      `paragraph_rewrite_single` (unchanged).
    - **Regime C** (whole-essay, essay-level-only): `light_polish`,
      `moderate_polish`, `heavy_revision` — **never** used for
      sentence-level claims; sentence-diffing retained only as a
      diagnostic (structural-drift detection, documented similarity
      ranges), explicitly never used to manufacture `modified_spans`.
    - Explicitly recorded: observed similarity range (0.07–0.97, no
      separable cluster), sentence consolidation, structural drift (70%),
      and the conceptual ambiguity of sentence-level attribution once
      sentences merge/split — a sequence-alignment algorithm
      (`difflib.SequenceMatcher` on sentence lists) was considered and
      explicitly **rejected as a ground-truth source** (though kept as a
      diagnostic tool) because it doesn't resolve that ambiguity, just
      produces a more sophisticated-looking guess.
  - **EXP-DATA-001-R1 executed** (18 records: 3 seeds × 6 categories,
    distinct seeds from the original pilot) — a small, explicitly-scoped
    validation, not a new full pilot. Results:
    [reports/EXP-DATA-001-R1.md](../reports/EXP-DATA-001-R1.md).
    - Regime A/B unchanged categories: 3/3, 3/3 passed.
    - **New controlled-span categories: 2/3, 2/3 passed, with
      dramatically better length control than the old whole-essay
      approach** (e.g. 12/12, 17/17 words target vs. actual) — promising,
      but n=3 per category is too small to call validated at scale.
    - One real failure caught correctly, not silently passed:
      `modification_scope_drift` (ratio 2.71 vs. expected [0.7, 1.3]) +
      `splice_resegmentation_mismatch`.
    - **Regime C confirmed behaving exactly as redesigned**: all 3
      `light_polish` samples got `ground_truth_confidence:
      "essay_level_only"` and `modified_spans: None` unconditionally;
      2/3 showing `structure_drift_observed` were correctly *not*
      rejected for it.
    - Zero instruction-leakage/AI-self-reference flags across all 18
      records (consistent with the QC fix; `full_ai` wasn't re-exercised
      in R1, so this specific category's real-world false-positive rate
      is confirmed only by the unit regression test, not a second live
      sample — noted as an open item).
    - New minor finding: near-duplicate check needs per-category scoping
      (flagged a splice variant as "near-duplicate" of its own human
      original — expected given the mechanism, not a real problem, but
      not yet fixed in code).
  - `docs/failure-analysis.md` populated with Part 1 (data generation
    pipeline failures, EXP-DATA-001) — clearly separated from Part 2
    (detector failures, still a placeholder since no detector exists).
  - Documentation updated: `generation-methodology.md` (three-regime
    structure, corrected ELLIPSE prompt count, `extract_prompts.py`
    marked as run), `decision-summary.md`, this file.

## In Progress

- [ ] **Stopped for review, as explicitly instructed.** Not scaling the
      dataset, not training/evaluating a detector, not starting EXP-003.
- [ ] Confirming the controlled-span redesign at larger scale (~10 seeds)
      before treating it as validated — proposed, not started.
- [ ] Near-duplicate check per-category scoping fix — proposed, not
      implemented.
- [ ] `sentence_rewrite_multi`, `paragraph_rewrite_multi` — designed, not
      yet exercised in any pilot.

## Experiments

- `EXP-DATA-001` — executed 2026-08-10, 60 samples. Results:
  [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md). Preserved as
  project history.
- `EXP-DATA-001-R1` — executed 2026-08-10, 18 records, targeted redesign
  validation. Results: [reports/EXP-DATA-001-R1.md](../reports/EXP-DATA-001-R1.md).

Both are data-generation-pipeline validation experiments; neither
involves a detector, and no detection accuracy/F1/generalization claim
is made from either.

## Current Known Problems

- The controlled-span light/moderate mechanism is promising but
  validated only at n=3 per category — needs a larger run before being
  treated as solved.
- Near-duplicate detection needs per-category scoping (false positive
  found, not yet fixed).
- `check_instruction_leakage`'s fix wasn't re-exercised against a live
  `full_ai` sample in R1 — confirmed by unit test only for that specific
  category.
- PERSUADE's `word_count` column and 4 duplicate `essay_id_comp` values
  still need explicit handling in future preprocessing code (documented
  since Phase 5C, unchanged).
- Both selected human corpora remain a domain mismatch with real
  admissions essays (unchanged conclusion, documented since Phase 5C).
- The application still does not classify or score essays — none of this
  work touches the detector itself.

## Decisions Pending

- Whether to run a larger-scale confirmation of the controlled-span
  mechanism before considering DEC-011 ready to move from Provisional to
  Accepted
- Whether the model itself (Phi-3.5-mini-instruct escalation, DEC-010)
  needs testing, now properly separable from the methodology question
- Near-duplicate check scoping fix
- Train/validation/test split ratios/stratification specifics beyond the
  family-level invariant (already fixed and verified working across both
  EXP-DATA-001 and EXP-DATA-001-R1)
- Which Phase 3/4 features are actually retained once EXP-002/EXP-003 can
  be run
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps (pending review — not started)

1. User reviews EXP-DATA-001-R1 findings and the DEC-011 redesign.
2. If approved: run a larger-scale (~10 seed) confirmation of the
   controlled-span mechanism specifically, and fix the near-duplicate
   scoping gap.
3. Only after that: consider scaling generation — a separate, explicit
   decision, not an automatic consequence of a passing validation check.
4. Continue to hold off on any detector work (training, evaluation,
   EXP-003) until the dataset pipeline itself is considered ready.
