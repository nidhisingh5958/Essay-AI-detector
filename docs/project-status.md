# Project Status

## Current Phase

Phase 5 — Dataset (in progress: source evaluation complete, acquisition
pipeline not yet built)

## Completed

- [x] Phase 1 — Repository structure, backend/frontend skeletons,
      documentation scaffolding, DEC-001 through DEC-004
- [x] Phase 2 — Text normalization, input validation, sentence
      segmentation (spaCy `en_core_web_sm`, DEC-005)
- [x] Phase 3 — Linguistic feature extraction, sentence + essay level
      (DEC-006, Provisional)
- [x] Phase 4 — Local language-model instrumentation via `distilgpt2`
      (DEC-007, DEC-008)
- [x] Phase 5, step 1 — Human dataset source evaluation:
  - Researched 7 candidate sources against provenance, licensing, domain
    relevance, size, privacy, and redistribution restrictions (real web
    research, cited — not assumed): PERSUADE 2.0, ELLIPSE Corpus, ICLE,
    TOEFL11/ETS, official college-published "Essays That Worked"
    examples, Reddit/essay-feedback forums, generic scraped Kaggle essay
    dumps
  - [docs/dataset-source-comparison.md](dataset-source-comparison.md)
    written with full comparison
  - [DEC-009](decisions/DEC-009-human-dataset-source.md) recorded
    (**Provisional**): selected PERSUADE 2.0 as the primary human corpus
    and reserved ELLIPSE specifically for the Phase 12 fairness analysis
    (genuine ELL-proficiency labels — the only candidate with
    appropriately-collected subgroup labels for that required analysis).
    Rejected the best domain match (official admissions-essay examples)
    on licensing/consent grounds, per explicit instruction to prioritize
    provenance/licensing over domain fit or size.
  - Confirmed no Kaggle CLI/credentials exist in this environment yet —
    actual download requires the user to provide Kaggle API credentials
- [x] Documentation updated: `dataset.md`, `decisions.md`,
      `decision-summary.md`
- [x] Phase 5, step 2a — acquisition pipeline built and unit-tested:
  - `scripts/dataset_sources.py`: `DatasetSource` config for PERSUADE 2.0
    and ELLIPSE, with `expected_licenses` from DEC-009
  - `scripts/acquire_dataset.py`: `verify_license()` checks live Kaggle
    metadata against DEC-009 before `acquire()` is allowed to call
    `dataset_download_files` — refuses (raises
    `LicenseVerificationError`) on a mismatched license or a
    not-found dataset ref, per the explicit "do not download or commit a
    dataset whose licensing/provenance has not been established"
    instruction
  - 5 tests (`scripts/tests/test_acquire_dataset.py`) using a fake Kaggle
    API object, confirming: license match passes, license mismatch
    raises and does **not** call the download function, missing dataset
    ref raises, and a successful run writes a reproducibility manifest —
    all passing, no real credentials needed for these tests
  - `kaggle` package installed into `backend/.venv` (shared, not a
    second virtualenv — documented in `scripts/README.md`) and confirmed
    to import cleanly

## In Progress

- [ ] Phase 5, step 2b — **actually run** `acquire_dataset.py` against
      the real Kaggle API. Blocked: no Kaggle API credentials
      (`~/.kaggle/kaggle.json` or `KAGGLE_USERNAME`/`KAGGLE_KEY`) exist in
      this environment. This is also the point at which the
      `dataset_sources.py` Kaggle refs (found via research, not yet
      independently confirmed via an authenticated API call) get their
      first real check — see "Known open item" in `scripts/README.md`.
- [ ] Cleaning/deduplication/leakage-safe-splitting scripts — not written
      yet; come after acquisition is confirmed working.
- [ ] Machine-written and mixed/AI-polished sample generation approach —
      not yet designed; needs its own decision record (Section 11/12).

## Experiments

None yet.

## Current Known Problems

- No data has been downloaded. DEC-009 is Provisional specifically
  because the PERSUADE license-framing discrepancy (CC BY-NC-SA 4.0 vs.
  CC BY 4.0 across two sources) has not been resolved against Kaggle's
  authoritative metadata.
- Both selected human corpora are a domain mismatch with real admissions
  essays (argumentative/proficiency-assessment writing, not personal
  narrative) — accepted deliberately (DEC-009) in exchange for clear
  provenance/licensing, but must be stated plainly wherever results are
  reported later, not minimized.
- No machine-written or mixed-sample generation approach has been chosen
  yet.
- The application still does not classify or score essays (unchanged from
  Phase 4).

## Decisions Pending

- Kaggle credential setup (user action required to unblock acquisition)
- Machine-written sample generation approach (which model(s)/prompts)
- Mixed/AI-polished sample construction methodology
- Train/validation/test split strategy specifics (leakage prevention by
  source essay is required; exact split ratios/stratification not yet
  decided)
- Which Phase 3/4 features are actually retained once EXP-002/EXP-003 can
  be run
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps

1. User to provide Kaggle API credentials so `scripts/acquire_dataset.py`
   can actually run — cannot proceed past this without them (see
   `scripts/README.md` for setup).
2. Once it runs: confirm the Kaggle refs in `dataset_sources.py` resolve
   to the intended datasets and the license check passes for real (not
   just against the fake API in tests); update DEC-009 status from
   Provisional to Accepted if so, or revise it if the live license or
   dataset differs from what research found.
3. Write cleaning/deduplication/statistics scripts and run them, then
   fill in the real numbers in `dataset.md` (replacing "Provisional"
   language with actual counts once verified).
4. Design and record a decision for machine-written and mixed/AI-polished
   sample generation before writing that code.
5. Update this file at the end of Phase 5.
