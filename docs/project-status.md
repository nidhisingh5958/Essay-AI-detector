# Project Status

## Current Phase

EXP-DATA-001 pilot complete (executed for real). **Stopped for review**
per explicit instruction — no scaling, no detector work, no EXP-003
started.

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Phase 3 — Linguistic feature extraction, sentence + essay level
      (DEC-006, Provisional)
- [x] Phase 4 — Local language-model instrumentation via `distilgpt2`
      (DEC-007, DEC-008)
- [x] Phase 5, steps 1–2 — Human dataset source evaluation + acquisition
      pipeline built ([DEC-009](decisions/DEC-009-human-dataset-source.md))
- [x] Phase 5B — Machine/mixed generation design
      ([DEC-010](decisions/DEC-010-machine-generation-model.md),
      [DEC-011](decisions/DEC-011-mixed-text-generation.md),
      [generation-methodology.md](generation-methodology.md))
- [x] Qwen2.5-1.5B-Instruct downloaded and smoke-tested
- [x] **Phase 5C — Live acquisition + inspection:**
  - Repo-local `.kaggle/kaggle.json` deleted (redundant with
    `~/.kaggle/access_token`, which is what actually authenticates);
    confirmed via `git ls-files` that no credential was ever tracked.
  - Fixed a real bug found via live data: `dataset.licenseName` (assumed
    from research) → `dataset.license_name` (the actual `kaggle` package
    attribute). Refuse-on-mismatch logic itself unchanged.
  - **Both corpora live-license-verified and acquired**: PERSUADE 2.0 and
    ELLIPSE, both `CC BY-NC-SA 4.0` — resolving DEC-009's open PERSUADE
    discrepancy.
  - **Full inspection performed** —
    [reports/dataset-inspection.md](../reports/dataset-inspection.md).
    Key findings: PERSUADE's real essay file is
    `persuade_2.0_human_scores_demo_id_github.csv` (not the 852MB
    discourse-annotated `_1.0` file); its `word_count` column is
    unreliable for ~5% of rows (worst case 48x off); paragraph boundaries
    (`\n\n`) survive in ~95% of essays in both corpora; PERSUADE itself
    carries an `ell_status` field; ELLIPSE has 44 prompts (not ~29 as
    earlier research estimated, corrected in place); both corpora
    negligibly duplicated.
  - **[DEC-009](decisions/DEC-009-human-dataset-source.md): Provisional
    → Accepted.**
- [x] **EXP-DATA-001 pilot — executed for real, 2026-08-10** (this
      update). 10 seed PERSUADE essays × 6 categories (human, full_ai,
      light_polish, moderate_polish, sentence_rewrite_single,
      paragraph_rewrite_single) = 60 samples. Full results:
      [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md).
  - New code: `scripts/generation_utils.py` (19 tests, pure logic:
    length budgeting, sentence-diff alignment, seed selection, family-
    split assignment, QC checks), `scripts/qwen_generate.py` (model
    wrapper), `scripts/extract_prompts.py` (2 tests; run for real against
    PERSUADE, wrote 15 prompt files to `data/prompts/persuade_2.0/`),
    `scripts/run_exp_data_001.py` (orchestrator), `scripts/analyze_exp_data_001.py`
    (post-hoc analysis).
  - **What worked:** full-essay generation (7/10 clean QC pass, 3/10
    only flagged by a QC bug — see below) and surgical-splice rewrites
    (sentence: 6/10 clean, 9/10 including a real correctness catch;
    paragraph: 9/10 clean). Zero near-duplicates. Zero metadata-schema
    violations. Zero leakage-invariant violations (family/split
    consistency verified programmatically across all 60 samples).
  - **What didn't work:** `light_polish`/`moderate_polish` (whole-essay-
    instruction-plus-diff mechanism) failed at **70% structure-drift**
    — the model consolidates/restructures sentences despite explicit
    instructions not to (confirmed via manual inspection, not a
    segmenter bug). Even the 30% that aligned showed a continuous,
    non-separable similarity distribution — **no diff-similarity
    threshold could be responsibly set from this data**, so none was
    invented.
  - **QC bug found and diagnosed:** `check_prompt_leakage` compared
    against the whole instruction (including the embedded essay prompt),
    flagging essays for legitimately discussing their own prompt. All 3
    flagged `full_ai` samples were false positives on manual review.
  - **Real correctness catch validated:** `splice_resegmentation_mismatch`
    QC check caught 2 genuine edge cases (informal run-on student
    writing causing re-segmentation to disagree after a splice) and
    correctly rejected them rather than producing wrong ground truth.
  - **[DEC-011](decisions/DEC-011-mixed-text-generation.md) updated:**
    status changed to "Provisional — partially invalidated by pilot
    evidence." Proposed fix (not implemented): replace exact-sentence-
    count-match alignment with `difflib.SequenceMatcher`-based sequence
    alignment on sentence lists; add dedicated length control for polish
    categories; fix the prompt-leakage check's scope.
  - **[DEC-010](decisions/DEC-010-machine-generation-model.md) updated:**
    model quality confirmed good where cleanly tested (full generation,
    surgical splice); polish-category failures not yet attributable to
    the model specifically vs. the methodology — flagged as needing a
    one-variable-at-a-time follow-up test.
  - Per instructions, **no threshold was invented to force a passing
    result**, and **no regeneration was attempted to make the numbers
    look better** — the methodology problem is documented and a fix is
    proposed, not silently patched.

## In Progress

- [ ] **Stopped for review, as explicitly instructed.** Not scaling the
      dataset, not training/evaluating a detector, not starting EXP-003.
- [ ] Implementing the proposed DEC-011 alignment fix (sequence-based
      diffing) — proposed, not started.
- [ ] Adding dedicated length control for polish categories — proposed,
      not started.
- [ ] Fixing `check_prompt_leakage`'s scope — proposed, not started.
- [ ] A follow-up pilot on just the polish categories, after the above
      fixes — not started.

## Experiments

- `EXP-DATA-001` — **executed 2026-08-10.** Results:
  [reports/EXP-DATA-001.md](../reports/EXP-DATA-001.md). Data-generation-
  pipeline validation only; no detector accuracy claims made or implied.

## Current Known Problems

- Light/moderate polish mixed-sample categories are **not usable as
  currently designed** — see DEC-011.
- `check_prompt_leakage` produces false positives when the instruction
  embeds prompt/target text the output is expected to reference — fix
  proposed, not applied.
- No dedicated length-control mechanism exists for polish categories.
- `generation_model_revision` metadata falls back to the bare model name
  rather than a pinned commit SHA — minor reproducibility gap.
- Raw PERSUADE text contains non-breaking-space characters (`\xa0`) not
  fully handled by `text_normalizer.py` — cosmetic, seen in a couple of
  spliced pilot outputs.
- PERSUADE's `word_count` column and 4 duplicate `essay_id_comp` values
  still need explicit handling in future preprocessing code (documented
  since Phase 5C, unchanged).
- The application still does not classify or score essays — none of this
  phase's work touches the detector itself.

## Decisions Pending

- Whether to implement the DEC-011 sequence-alignment fix before or
  alongside a Phi-3.5-mini-instruct follow-up test (DEC-010 recommends
  testing one variable at a time)
- Diff-similarity threshold for polish categories — still open, now with
  a clearer path (fix alignment first, then re-examine)
- Train/validation/test split ratios/stratification specifics beyond the
  family-level invariant (already fixed and verified working)
- Which Phase 3/4 features are actually retained once EXP-002/EXP-003 can
  be run
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps (pending review — not started)

1. User reviews EXP-DATA-001 findings and the proposed DEC-011 fix.
2. If approved: implement the `difflib`-based sequence-alignment
   redesign for `light_polish`/`moderate_polish`, add dedicated length
   control, fix `check_prompt_leakage`'s scope.
3. Run a small follow-up pilot on just the polish categories to confirm
   the fix works before considering a model change.
4. Only after that: consider scaling generation, which remains a
   separate, explicit decision — not an automatic consequence of a
   passing pilot.
5. Update this file at each step.
