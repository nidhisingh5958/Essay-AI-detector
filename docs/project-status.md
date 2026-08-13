# Project Status

## Current Phase

EXP-DATA-001-R1-confirmation complete (50 samples, real execution).
**Stopped for review** per explicit instruction — no scaling, no
detector work, no EXP-003 started.

## Completed

- [x] Phases 1–5, 5B — see prior status snapshots (repo scaffold, text
      pipeline, feature extraction, LM instrumentation, dataset
      acquisition/inspection, generation design).
- [x] EXP-DATA-001 — full pilot (60 samples). Found whole-essay-diff
      polish unreliable for sentence-level ground truth (70% structural
      drift). [Report](../reports/EXP-DATA-001.md), preserved.
- [x] QC leakage bug fixed (`check_prompt_leakage` →
      `check_instruction_leakage` + `check_ai_self_reference`), DEC-011
      redesigned into three ground-truth regimes.
- [x] EXP-DATA-001-R1 — targeted validation (18 records, n=3/category).
      Controlled-span mechanism looked promising.
      [Report](../reports/EXP-DATA-001-R1.md).
- [x] **This update:**
  - Kaggle credential cleanup re-verified (unchanged from prior state —
    no repo-local credential, external `~/.kaggle/access_token` only,
    nothing tracked).
  - **Near-duplicate scoping fixed**: `near_duplicate_pairs_scoped`
    (family-aware — same-family similarity expected/allowed,
    cross-family similarity is the real detection target), 5 required
    regression tests.
  - **Real bug found and fixed along the way**: `difflib.SequenceMatcher`'s
    default `autojunk=True` badly understates similarity for text over
    ~200 characters (observed: ~0.28 instead of ~0.97 for a one-word
    change in a ~200-char sentence). Fixed with `autojunk=False` in both
    `near_duplicate_pairs_scoped` and `align_and_diff_sentences` — the
    latter means EXP-DATA-001's reported Regime C similarity range
    (0.07–0.97) should be read as approximate, not exact (the
    *structural* 70%-drift finding is unaffected). Regression test added.
  - **`semantic_preservation` field added**: `not_yet_reviewed` /
    `preserved` / `questionable` / `changed`, assigned by manual human
    review only — never by a model call (`scripts/apply_semantic_review.py`
    performs the merge, not the judgment).
  - **Per-sample metadata expanded** for measurability: `intended_span_index`,
    `span_target_words`, `span_actual_words`,
    `length_ratio_actual_vs_target`, `resegmentation_ok` (explicit bool),
    `instruction_leakage_flagged`, `ai_self_reference_flagged`,
    `cross_family_duplicate_flag` — all always present, not just noted
    when triggered, so raw distributions can be reported.
  - **`generate_paragraph_transform` built** (generic, parallel to
    `generate_sentence_transform`) — light/moderate controlled paragraph
    rewrites, new capability.
  - **EXP-DATA-001-R1-confirmation executed**: 50 records, 10 seeds
    **previously unseen** in any prior experiment, 5 categories (human +
    sentence light/moderate controlled + paragraph light/moderate
    controlled). Regime C explicitly excluded (unchanged, not retested).
    Required 3 separate background-process launches due to environment
    session interruptions — the script was made resumable (skips
    already-completed samples via `samples.jsonl` inspection) specifically
    to survive this, and did.
    - **Finding: category-specific split, not a uniform result.**
      Paragraph-level controlled transformation: 19/20 QC-passed, 0
      resegmentation failures, 18/20 judged `"preserved"` on manual
      semantic review. Sentence-level: 12/20 QC-passed, and — the most
      important finding — **4 samples passed every automated check while
      still changing the essay's actual meaning** (e.g. "at least one C"
      altered to "two Cs"; a specific grievance replaced by a generic,
      unrelated sentence). Combined sentence-level semantic-preservation:
      33% preserved, 47% changed.
    - Zero cross-family duplicates (34 same-family matches correctly not
      flagged — validates the scoping fix in practice).
    - Zero instruction-leakage/AI-self-reference flags across all 50
      records (though `full_ai` wasn't re-exercised this round either).
    - Zero metadata/provenance integrity violations.
    - Full results: [reports/EXP-DATA-001-R1-confirmation.md](../reports/EXP-DATA-001-R1-confirmation.md).
  - **DEC-011 updated with confirmation evidence — status stays
    Provisional, not marked Accepted.** Recommendation: **B — promising
    but requires another revision**, specifically for sentence-level
    controlled transformation; paragraph-level is close to ready.
  - Documentation updated: `generation-methodology.md` (schema now shows
    a real record, three-regime section updated with the sentence/
    paragraph reliability split), `failure-analysis.md` (3 new preserved
    failures: QC-blind semantic drift, structural-artifact insertion,
    the `autojunk` bug), `decision-summary.md`.

## In Progress

- [ ] **Stopped for review, as explicitly instructed.** Not scaling to
      thousands of samples, not building the final dataset, not
      training/evaluating a detector, not running EXP-003.
- [ ] Sentence-level controlled-transformation remediation (one of: a
      second automated semantic-drift signal, mandatory semantic-review
      gate, or more surrounding context per edit) — options recorded in
      DEC-011, none chosen or implemented yet.
- [ ] Paragraph-level: technically closer to ready, but not yet scaled
      beyond n=10 or run without Regime C explicitly excluded from a
      combined pilot.

## Experiments

- `EXP-DATA-001` — 60 samples, executed 2026-08-10. Preserved.
- `EXP-DATA-001-R1` — 18 records, n=3/category, executed 2026-08-10.
- `EXP-DATA-001-R1-confirmation` — 50 records, n=10/category (sentence +
  paragraph light/moderate only, Regime C excluded), executed 2026-08-10.

All three are data-generation-pipeline validation experiments. None
involves a detector; no detection accuracy/F1/generalization claim is
made from any of them.

## Current Known Problems

- **Sentence-level controlled transformation has a real, evidenced
  semantic-drift problem** that structural QC cannot catch on its own —
  not solved, only diagnosed and measured.
- Why sentence-level `light` instructions drifted *more* than `moderate`
  ones is observed but not explained (temperature and wording both
  varied together across experiments so far — not isolated).
- Semantic review so far has one reviewer (the agent operating this
  pipeline reading text directly) — no inter-rater reliability figure
  exists.
- `full_ai` has not been re-exercised with the fixed leakage check in any
  live run since the original bug was found — confirmed by unit
  regression test only.
- EXP-DATA-001's reported Regime C similarity range (0.07–0.97) was
  computed before the `autojunk` fix and should be read as approximate.
- PERSUADE's `word_count` column unreliability and 4 duplicate
  `essay_id_comp` values (documented since Phase 5C) still need handling
  in future preprocessing code.
- Both selected human corpora remain a domain mismatch with real
  admissions essays (documented since Phase 5C).
- The application still does not classify or score essays.

## Decisions Pending

- Which remediation path for sentence-level semantic drift (three
  candidates recorded in DEC-011, none chosen)
- Whether/how to scale paragraph-level controlled transformation beyond
  n=10
- Whether the model itself (Phi-3.5-mini-instruct escalation, DEC-010)
  needs testing for the sentence-level category specifically
- Train/validation/test split ratios beyond the family-level invariant
  (fixed and verified working across all three experiments so far)
- Which Phase 3/4 features are retained once EXP-002/EXP-003 can run
- Scoring/calibration method (Phase 6)
- Passage-grouping strategy (Phase 7)

## Next Steps (pending review — not started)

1. User reviews EXP-DATA-001-R1-confirmation findings and the DEC-011
   update.
2. If approved: design and implement a remediation for sentence-level
   semantic drift (one of the three DEC-011 candidates) before that
   category is used at scale.
3. Consider a paragraph-level-only scale-up as a separate, lower-risk
   next step, since it's closer to ready.
4. Continue to hold off on any detector work (training, evaluation,
   EXP-003) until the dataset generation pipeline itself is considered
   ready — sentence-level specifically is not yet.
