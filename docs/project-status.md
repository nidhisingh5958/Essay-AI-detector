# Project Status

## Current Phase

Phase 5C — Live Human Corpus Acquisition & Inspection (complete: human
corpus acquired, license-verified, and inspected; awaiting review before
any AI/mixed sample generation)

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Phase 3 — Linguistic feature extraction, sentence + essay level
      (DEC-006, Provisional)
- [x] Phase 4 — Local language-model instrumentation via `distilgpt2`
      (DEC-007, DEC-008)
- [x] Phase 5, step 1 — Human dataset source evaluation (7 candidates
      researched, [DEC-009](decisions/DEC-009-human-dataset-source.md)
      recorded)
- [x] Phase 5, step 2 — acquisition pipeline built and unit-tested
- [x] Phase 5B — machine/mixed generation design: DEC-010, DEC-011,
      [generation-methodology.md](generation-methodology.md),
      EXP-DATA-001 design (not run)
- [x] Qwen2.5-1.5B-Instruct downloaded and smoke-tested (2 generations,
      not the pilot) — confirmed viable, found and documented a
      length-control gap
- [x] **Phase 5C — live acquisition and inspection (this update):**
  - **Fixed a real bug found via live data, not research:**
    `verify_license()` used `dataset.licenseName` based on web research
    of the `kaggle` package's API; the actual installed package exposes
    `dataset.license_name` (snake_case). Confirmed by inspecting the real
    `ApiDataset` object's attributes. Fixed; the refuse-on-mismatch logic
    itself was not changed. Test fixtures updated to match; full suite
    re-run and passing.
  - **Live license verification, both passed:**
    - PERSUADE 2.0 (`nbroad/persaude-corpus-2`): live license
      `CC BY-NC-SA 4.0` — **resolves** the discrepancy DEC-009's research
      found (Kaggle's authoritative metadata matches the GitHub repo, not
      the Learning Agency Lab site's "CC BY 4.0" framing).
    - ELLIPSE Corpus (`mpware/ellipse-corpus`): live license
      `CC BY-NC-SA 4.0`, exactly as expected.
  - **Both datasets downloaded**: `data/raw/persuade_2.0/` (852MB — see
    file-naming finding below), `data/raw/ellipse_corpus/` (15MB), both
    gitignored, neither committed.
  - **Full inspection performed** — see
    [reports/dataset-inspection.md](../reports/dataset-inspection.md) for
    complete findings. Highlights:
    - PERSUADE's largest file (`persuade_corpus_1.0.csv`, 852MB) is a
      *different*, discourse-element-annotated release, not what our
      pipeline uses — the real essay-level file is
      `persuade_2.0_human_scores_demo_id_github.csv` (25,996 essays, 15
      prompts, each with full instruction text).
    - **Corpus data-quality bug found:** PERSUADE's `word_count` column
      disagrees with a direct recount for ~5% of rows (worst case: 48x
      off — 14,818 claimed vs. 305 actual). Our pipeline already
      recomputes word counts independently (Phase 3), so this doesn't
      block anything, but the column itself must never be trusted.
    - 4 PERSUADE `essay_id_comp` values collide across different essays
      (source-data bug, not duplicate content).
    - **Paragraph boundaries confirmed preserved** (blank-line markers)
      in ~95% of essays in both corpora — resolves the open question from
      Phase 5B about paragraph-level mixed-sample feasibility.
    - **New finding:** PERSUADE itself has an `ell_status` field (~2,244
      "Yes" / ~22,451 "No") — not previously confirmed.
    - **Correction:** ELLIPSE has 44 unique prompts, not the ~29
      estimated from web research — `dataset-source-comparison.md`
      updated in place with this correction, old estimate left visible
      alongside it.
    - **Refined fairness methodology:** ELLIPSE is 100% ELL by corpus
      design, so it cannot supply a non-ELL comparison group alone. Plan
      now uses (a) ELLIPSE's continuous proficiency scores for a
      within-ELL-population gradient test, and (b) PERSUADE's own
      `ell_status` for a same-corpus coarse comparison.
    - Sensitive metadata inventoried for both corpora; recommendation is
      to exclude gender/race/economic-status/disability/grade from the
      working ML dataset entirely, keeping only `ell_status` and
      proficiency scores in a separate evaluation-only table.
    - Near-duplicate rates negligible in both corpora (0 exact dupes
      either corpus; 4 near-dupe rows in PERSUADE, 0 in ELLIPSE).
  - **[DEC-009](decisions/DEC-009-human-dataset-source.md) updated:
    Provisional → Accepted**, with a "Live Verification & Inspection
    Update" section added (original research-based Evidence preserved,
    not overwritten).
  - `scripts/inspect_corpus.py` written (word-count discrepancy,
    paragraph-marker coverage, near-duplicate heuristic, duplicate-ID
    report) with 9 tests against synthetic fixtures — never the real
    files.
  - Found (and left alone, per instructions) a redundant credential file
    at `.kaggle/kaggle.json` inside the repo itself — confirmed gitignored
    and never tracked/committed, but flagged as a hygiene item (loose
    file permissions, redundant with `~/.kaggle/access_token` which is
    what actually authenticated).
  - Documentation updated: `dataset.md`, `dataset-source-comparison.md`,
    `methodology.md`, `final-decision-guide.md`, `decision-summary.md`,
    this file.
  - All tests still passing: 43 backend + 14 scripts (5 acquisition-gate
    + 9 inspection-utility).

## In Progress

- [ ] **Awaiting user review of Phase 5C findings** before any AI/mixed
      sample generation, per explicit instruction to stop here.
- [ ] EXP-DATA-001 pilot execution — unblocked in principle (corpus
      acquired, model downloaded) but explicitly not run pending review.
- [ ] `scripts/extract_prompts.py` — can now be written for real (prompt
      text confirmed available and cleanly mappable in PERSUADE; ELLIPSE
      has only short prompt titles, no full instruction text).
- [ ] Cleaning/deduplication/leakage-safe-splitting scripts — not written
      yet; informed by the real data-quality findings above (handle the
      4 ID collisions, the `ell_status` blank-string-vs-NaN
      inconsistency, exclude sensitive demographic columns).

## Experiments

- `EXP-DATA-001` (generation pipeline pilot) — **designed, not run.**

## Current Known Problems

- No AI/mixed sample has been generated. No train/validation/test split
  exists yet.
- DEC-010 and DEC-011 remain Provisional — a 2-generation smoke test is
  not pilot-scale validation.
- The diff-similarity threshold and structure-drift tolerance for the
  polish-category mixed samples are still unset, deferred to
  EXP-DATA-001.
- PERSUADE's `word_count` column and 4 duplicate `essay_id_comp` values
  need explicit handling in any preprocessing code (documented, not yet
  fixed in code since no processed dataset has been built yet).
- Both corpora remain a domain mismatch with real admissions essays
  (unchanged conclusion, now on firmer evidence).
- A redundant, loosely-permissioned Kaggle credential file exists inside
  the repo at `.kaggle/kaggle.json` (gitignored, never committed) —
  hygiene item, not a leak.
- The application still does not classify or score essays.

## Decisions Pending

- Whether Qwen2.5-1.5B-Instruct's actual output quality is sufficient at
  pilot scale (DEC-010, deferred to EXP-DATA-001)
- Diff-similarity threshold / structure-drift tolerance (DEC-011,
  deferred to EXP-DATA-001)
- Train/validation/test split ratios/stratification specifics (the
  family-level leakage invariant is fixed; exact ratios are not)
- Which Phase 3/4 features are actually retained once EXP-002/EXP-003 can
  be run
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps (pending review — not started)

1. User reviews Phase 5C findings (this update + the inspection report)
   and either approves proceeding to EXP-DATA-001 or requests changes.
2. Write `scripts/extract_prompts.py` against the real PERSUADE
   `prompt_name`/`assignment` columns (and ELLIPSE's `prompt` column,
   noting its lack of full instruction text).
3. Run EXP-DATA-001 pilot (10 seed essays × 6 categories), using real
   prompts and the now-confirmed paragraph-boundary convention.
4. Use pilot findings to fix the diff-similarity threshold and confirm/
   revise DEC-010's model choice; update both decisions accordingly.
5. Only after pilot review: design the cleaning/deduplication/leakage-
   safe-splitting scripts, informed by the specific data-quality issues
   this inspection found.
