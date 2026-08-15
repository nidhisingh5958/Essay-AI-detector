# Project Status

## Current Phase

**Status at a glance (2026-08-15):**

**COMPLETED** (executed, results exist, reported):
- Dataset construction (PRIMARY-DATASET-v1, 150 families, 450 records generated)
- Dataset semantic review (mandatory human review of all 141 reviewable sentence-light samples)
- PRIMARY-DATASET-v1 freeze (425-sample inclusion manifest, approved, immutable)
- EXP-003A (human vs. full_ai)
- EXP-003B (human vs. ai_assisted — essay-level + sentence-localization)
- EXP-003B-R1 (length/count-vs-non-length localization diagnostic)
- **EXP-003C** (three-class: human/full_ai/ai_assisted, essay-level) — **EXECUTED / COMPLETE**

**NOT YET EXECUTED** (design/protocol exists; no code run, no data
generated, no model trained, no generator downloaded):
- **FAIR-001 — DESIGNED / NOT EXECUTED**
- **GEN-001 — DESIGNED / NOT EXECUTED**

Per explicit instruction, FAIR-001 and GEN-001 are **not** marked
executed or completed — only EXP-003C is. Full protocols:
[experiments/EXP-003.md](experiments/EXP-003.md) §9 (executed),
[experiments/FAIR-001.md](experiments/FAIR-001.md) (not executed),
[experiments/GEN-001.md](experiments/GEN-001.md) (not executed).

**PRIMARY-DATASET-v1 approved and FROZEN (2026-08-15) as the immutable
v1 benchmark** (150 families, 425 samples: 150 human + 148 full_ai +
127 `ai_assisted`; `data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json`
is authoritative — no silent mutation; a genuine defect gets a
documented, versioned `PRIMARY-DATASET-v2`, not a silent edit).

**EXP-003B-R1 (diagnostic: does localization survive controlling for
length/count?) executed and complete (2026-08-15).** Full report:
[reports/EXP-003B-R1.md](../reports/EXP-003B-R1.md). **Headline: yes —
non-length features alone reach 46.7% top-1 localization accuracy on
test, comparable to length/count-only (40.0%) and far above chance
(~8%).** Localization signal is not merely a length artifact of the
splice mechanism. A second, independent finding against the LM
instrument: genuine predictability features alone are the *weakest* of
five groups tested (13.3% top-1) — worse than non-LM stylometric alone
(40.0%) — reinforcing, not resolving, DEC-004's standing skepticism.
EXP-003B.md itself is unmodified (a separate, dated report). **EXP-003C,
fairness, and any cross-generator work are NOT run** — stop condition,
waiting for review.

EXP-003B (human vs. ai_assisted), executed 2026-08-15 — essay-level +
sentence-level localization, evaluated separately. Full report:
[reports/EXP-003B.md](../reports/EXP-003B.md). Headline: essay-level
detection of lightly AI-assisted essays fails on this benchmark
(chance-level for every feature group; the frozen threshold's test
result, 46.2%, is worse than the majority baseline, 59.0%).
Sentence-level localization showed real, above-chance signal (86.7%
test recall at 17.6% precision; 60% top-1 vs. 25% validation) — now
further diagnosed by EXP-003B-R1 above. Full-AI detection (EXP-003A)
does not transfer to lightly-assisted writing at the essay level.

EXP-003A (human vs. full_ai), executed 2026-08-15 — the first real
detector-signal result in this project. Full report:
[reports/EXP-003A.md](../reports/EXP-003A.md). Headline: stylometric
features (lexical diversity, repetition, word length) alone separate
PERSUADE human essays from Qwen2.5-1.5B-Instruct `full_ai` essays almost
perfectly (test: 45–46/46 depending on the pre-registered threshold
choice); the LM instrument (perplexity/predictability features) added
no measurable value over stylometric features alone — DEC-004's
standing caution against assuming "low perplexity = AI" is directly
reinforced. Result is scoped explicitly to this benchmark (one human
corpus, one generation model) — not a general AI-detection claim.

Detector experiment design (2026-08-15, prerequisite to the above):
[docs/experiments/EXP-003.md](experiments/EXP-003.md) specifies
EXP-003A (human vs. full_ai), EXP-003B (human vs. ai_assisted, essay +
sentence-localization), EXP-003C (three-class, deferred until A/B run)
— feature inventory ([feature-inventory.md](../feature-inventory.md)),
baselines, model/threshold strategy, localization evaluation, and
evidence-mapping design are complete (DEC-014–017). A descriptive
analysis of the mixed-acceptance imbalance (test 69.6% vs. train 85.7%)
found no clear systematic cause — consistent with ordinary sampling
variance at small per-split, per-prompt sample sizes — and the test set
was **not** altered based on it.

PRIMARY-DATASET-v1 remains **approved and FROZEN** (150 families, 425
samples: 150 human + 148 full_ai + 127 `ai_assisted`;
`data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json` is
authoritative — no silent mutation; a genuine defect gets a documented,
versioned `PRIMARY-DATASET-v2`, not a silent edit).

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
- [x] **EXP-DATA-001-R4 (2026-08-14) — full_ai pre-scale regression,
      required prerequisite for 150-family construction:** 10 fresh
      seeds, `full_ai` only. **Clean: 0 leakage flags, 0 self-reference
      flags, 10/10 QC passed, length ratio 0.89–1.15 (median 1.08), 0
      cross-family duplicates, 0 family-split-invariant violations
      (verified across ALL 8 experiment data files, not just this one),
      clean topic/prompt adherence on manual spot-check of all 10
      essays.** No regression found; `full_ai` mechanism unchanged, as
      instructed. New reusable utility added:
      `generation_utils.find_family_split_violations()` (tested,
      2 regression tests) — makes the hard leakage invariant
      programmatically checkable, for this round and the upcoming
      150-family build.
      [reports/EXP-DATA-001-R4-full-ai-regression.md](../reports/EXP-DATA-001-R4-full-ai-regression.md).
- [x] **PRIMARY-DATASET-v1 (2026-08-14/15) — 150-family primary dataset
      construction, executed per approved plan, no methodology
      changes:**
  - 150 fresh seeds (0 overlap with the 90 prior-experiment seeds),
    family splits assigned before generation (105/22/23 train/
    validation/test), **0 family-split-invariant violations**.
  - Generated 450 records (150 human + 150 full_ai + 150
    sentence-light). `full_ai`: 148/150 QC-passed (2 genuine
    self-reference, excluded). Sentence-light: 134/150 QC-passed
    cleanly, 7 flagged, 9 hard-rejected (unresolvable span).
  - **Every one of 141 reviewable sentence-light samples got mandatory
    human semantic review**: 127 preserved (90.1%), 6 questionable, 8
    changed — a real, larger-sample drift rate than R3's n=25 batch
    showed (4%), reported honestly, not smoothed.
  - **Significant new finding**: the DEC-012 automated screen labeled
    6 of the 8 real "changed" samples `likely_preserved` (75% miss
    rate) — materially worse than any prior round documented. All 6
    misses are meaning-reversal/agent-substitution drift touching no
    number or entity (e.g. "should not be allowed" → "should not be
    discouraged" — a full position reversal). DEC-012 updated with
    this as new evidence, correcting the earlier framing that treated
    the paragraph-level miss as the only confirmed gap.
  - **0 cross-family duplicates** (450-record near-duplicate check
    required a performance optimization — shingle-based candidate
    pre-filtering, mathematically safe, not a methodology change — to
    complete; the naive O(n²) approach didn't finish in reasonable
    time at this scale).
  - Inclusion manifest built by filtering, not assuming validity:
    **425 total (150 human + 148 full_ai + 127 ai_assisted)**. 25
    excluded records retained in full with metadata for failure
    analysis, never used as positive ground truth.
  - Observed, reported-not-corrected imbalance: test split's mixed-
    category acceptance rate (16/23, 69.6%) is lower than train
    (85.7%) and validation (95.5%) — plausible small-sample variance,
    flagged rather than resampled.
  - New tooling (execution-support only, not methodology):
    `scripts/run_primary_dataset_v1.py`,
    `scripts/build_primary_dataset_manifest.py`,
    `scripts/check_primary_dataset_duplicates.py`.
  - Full detail: [reports/FINAL-DATASET-CONSTRUCTION.md](../reports/FINAL-DATASET-CONSTRUCTION.md).
    Updated: `docs/dataset.md` (actuals vs. projection), DEC-012 ("Third
    Validation, at Scale"), `decision-summary.md`.
- [x] **PRIMARY-DATASET-v1 approved and frozen; EXP-003 experiment
      design phase (2026-08-15) — design only, nothing executed:**
  - **Freeze verified**: `find_family_split_violations()` re-run against
    both the full 450-record samples file and the 425-record included-
    only subset — **0 violations either way**. Exact composition
    re-confirmed per split (train 105/103/90, validation 22/22/21, test
    23/23/16 for human/full_ai/ai_assisted).
  - **Mixed-acceptance imbalance descriptively analyzed** (non-sensitive
    variables only: source length, span length/position, prompt topic,
    QC note type, length ratio) — no clear systematic cause found;
    consistent with sampling variance at small per-split/per-prompt
    cell sizes. **Test set not altered.**
  - **DEC-012 finalized**: kept as "automated semantic-risk triage,"
    explicitly not ground truth, not a safety gate, not a claim of
    reliable universal drift detection. Historical evidence (calibration
    → R2 → R3 → PRIMARY-DATASET-v1) preserved showing exactly how and
    why this framing changed.
  - **`docs/feature-inventory.md`** (new): every IMPLEMENTED feature (23
    stylometric + 6 LM-derived) cataloged with definition, location,
    level, limitations; PROPOSED features clearly separated and marked
    not-yet-implemented.
  - **`docs/experiments/EXP-003.md`** (new): full design for EXP-003A
    (human vs. full_ai), EXP-003B (human vs. ai_assisted, essay +
    sentence-localization), EXP-003C (three-class, deferred until A/B
    run) — baselines, model/threshold strategy, metrics, test-set-freeze
    protocol, fairness-design pointer, reproducibility requirements,
    dataset-scope limitation, remaining methodological risks.
  - **4 new decision records**: DEC-014 (feature set & baselines),
    DEC-015 (model selection & threshold strategy — L2-regularized
    logistic regression primary, random forest as a non-preferred
    nonlinearity check, train+validation only for both), DEC-016
    (sentence-localization evaluation, using exact `modified_spans`
    provenance, never inferred), DEC-017 (evidence/explanation mapping —
    fixed deterministic templates, no generative model ever produces
    explanation text, extending DEC-004's constraint to the explanation
    layer).
  - **`docs/fairness.md`** updated with a concrete (not-yet-executed)
    design: compare detector false-positive/false-negative rates by
    PERSUADE's `ell_status`, joined via `family_id` in a separate table,
    never as a training feature; confirmed no sensitive demographic
    field (gender/race/economic status/disability) is carried into any
    generated sample record.
  - New data-layer utility (not modeling code):
    `scripts/exp003_data_prep.py` — manifest loading/integrity checks,
    and `build_sentence_localization_labels()` (DEC-016), verified to
    produce exactly 1 `ai_assisted` sentence per accepted sample across
    all 127 included records. 8 new tests
    (`scripts/tests/test_exp003_data_prep.py`).
  - **No detector trained, no threshold tuned, no test-set performance
    inspected.**
- [x] **EXP-003A — human vs. full_ai, executed once, fully frozen
      protocol (2026-08-15):**
  - 298 essays (150 human, 148 full_ai), 208/44/46 train/validation/test,
    **0 family-leakage violations**, **0 missing feature values** across
    298 essays × 29 features.
  - Baselines: majority 50.0%; stylometric-only **100.0%** (validation);
    LM-only 79.5% (validation).
  - Primary (combined logistic regression, `C=0.00599` via CV on train):
    100.0% validation. Random-forest comparison: also 100.0% — did not
    trigger a primary-model switch (DEC-015), since no performance
    argument existed for trading away interpretability.
  - Threshold selected on validation only (0.47, from an argmax-F1 sweep
    that landed on an arbitrary tie-break point — documented candidly).
  - **Frozen test result: 45/46 = 97.8%** (95% CI [88.7%, 99.6%]) at the
    pre-registered threshold; 46/46 = 100% at the unselected default 0.5,
    reported for transparency only, not substituted as the result.
  - **Feature-group finding, reported honestly**: the LM instrument
    (perplexity/predictability features) added **no measurable value**
    over stylometric features alone — every ablation including the full
    stylometric set stayed at 100% validation; removing all 5 LM
    within-sentence features, or just the predictability-delta feature,
    changed nothing. DEC-004's standing caution against assuming "low
    perplexity = AI" is directly reinforced by this result.
  - Signal is distributed across many stylometric features (max
    |standardized coefficient| = 0.21), driven most by lexical diversity
    (`type_token_ratio`, `moving_average_ttr` — near-zero range overlap
    between classes) and repetition (`repeated_bigram_ratio`) — not one
    dominant or suspicious single feature.
  - One test error (`302DC21A6DEE__human`, score 0.49 vs. threshold
    0.47) — a marginal, low-confidence miss on an atypically lexically-
    diverse human essay, not a confident failure.
  - **Explicitly scoped**: describes performance distinguishing PERSUADE
    2.0 from Qwen2.5-1.5B-Instruct specifically — not general AI
    detection.
  - Full report: [reports/EXP-003A.md](../reports/EXP-003A.md). Raw
    outputs: `experiments/EXP-003A/features.jsonl`,
    `experiments/EXP-003A/results.json`.
- [x] **EXP-003B — human vs. ai_assisted, executed once, fully frozen
      protocol, TWO separate evaluations (2026-08-15):**
  - Essay-level: 277 essays (150 human, 127 ai_assisted), 195/43/39
    train/validation/test. Sentence-level (localization): 1,578 of
    1,707 raw sentences retained (129 excluded for undefined
    `predictability_delta`, documented not imputed — 8 essays lost
    their only positive-labeled sentence entirely as a result). **0
    family-leakage violations** on both datasets.
  - **Essay-level: chance-level for every feature group** (majority
    baseline 51.2% ≈ stylometric-only ≈ LM-only ≈ combined 53.5%
    validation). Threshold selection (argmax F1) landed on a degenerate,
    near-always-positive rule (0.34) — **frozen test result 46.2%,
    worse than the 59.0% majority baseline** — reported honestly as a
    real consequence of applying this procedure to a near-chance
    problem, not hidden.
  - **Sentence-level localization: real, above-chance signal.** Frozen
    threshold (0.06, reflecting ~8% positive prevalence): test recall
    86.7% (13/15) at precision 17.6% (61 false positives/182 negatives).
    New per-essay top-1 ranking metric (added to address "don't let
    essays with more sentences dominate"): 60.0% test / 25.0%
    validation — noisy given small per-split counts (15–20 essays), but
    well above the ~8% chance rate.
  - **Central finding**: full-AI detection (EXP-003A) does **not**
    transfer to lightly AI-assisted writing at the essay level — the
    aggregate signal is washed out when ~90% of the essay is unchanged
    human text. Sentence-level, in-context comparison recovers real
    signal the essay-level aggregate destroys.
  - Sentence-level top coefficient is length/token-count-related
    (`lm_mean_token_count`), a more surface-level signal than EXP-003A's
    broad lexical-diversity finding — flagged as a caveat, not
    over-interpreted.
  - Cross-experiment note: the same human essay (`302DC21A6DEE`) was
    EXP-003A's one error and among EXP-003B's essay-level errors —
    flagged as a property of that specific essay (elevated lexical
    diversity), not two unrelated coincidences.
  - 4 decision records updated with real evidence, status reflecting
    evidence not automatic completion: DEC-004 (LM contribution —
    inconclusive, not resolved either direction), DEC-015 (threshold
    strategy — degenerate-threshold risk now concretely evidenced),
    DEC-016 (localization — design validated, detection performance
    weak), DEC-017 (evidence mapping — first real worked examples,
    cautious-language design held up on a low-confidence case).
  - 9 new tests (`test_run_exp003b.py`, `test_exp003b_extract_features.py`)
    — pipeline correctness, not expected performance.
  - Full report: [reports/EXP-003B.md](../reports/EXP-003B.md). Raw
    outputs: `experiments/EXP-003B/features_essay.jsonl`,
    `experiments/EXP-003B/features_sentence.jsonl`,
    `experiments/EXP-003B/results.json`.
- [x] **EXP-003B-R1 — diagnostic: does localization survive removing
      length/count features? (2026-08-15). Reuses EXP-003B's sentence-
      level dataset unchanged; EXP-003B.md not modified.**
  - 6 feature groups, exact columns pre-defined (`lm_mean_token_count`
    reclassified as a length/count feature, not predictability
    evidence, per explicit instruction — its name alone doesn't make it
    LM evidence). Threshold selected independently per group (sweep on
    validation, freeze, test once) — no group compared at a fixed 0.5.
  - **Top-1 test accuracy**: A (all 29) 60.0%; B (length/count only,
    11 feats) 40.0%; C/F (non-length combined, 18 feats) **46.7%**; D
    (LM-only, 6 feats) 13.3%; E (stylometric non-length only, 13 feats)
    40.0%.
  - **Central finding**: non-length features alone (C/F) match or beat
    length/count alone (B) — **localization signal is not merely a
    length/count artifact**. Full set (A) still beats either subset
    alone, suggesting partial complementarity.
  - **LM finding**: genuine predictability features isolated from count
    (D) are the *weakest* group (13.3%) — worse than non-LM stylometric
    alone (E, 40.0%) — a second data point against the LM instrument's
    current usefulness, not a resolution either way.
  - D and E's fixed-threshold precision/recall/F1 were identical and
    degenerate (both flag every test sentence positive) — documented
    honestly; top-1 ranking was the metric that actually differentiated
    them.
  - Group A's numbers reproduced EXP-003B's original result exactly — a
    validated internal consistency check before drawing new conclusions.
  - DEC-004 updated with this as a second, still-inconclusive data
    point (status stays open). DEC-015/016/017 explicitly left
    unchanged — no new evidence warranted a status change for any of
    them, stated plainly rather than updated by default.
  - 6 new tests (`test_run_exp003b_r1.py`) — group-definition
    correctness (disjointness, the documented C==F equivalence,
    `token_count`'s reclassification), not expected performance.
  - Full report: [reports/EXP-003B-R1.md](../reports/EXP-003B-R1.md).
    Raw output: `experiments/EXP-003B-R1/results.json`.
  - **EXP-003C, fairness, cross-generator, and NLI experiments
    explicitly NOT run** — stop condition, waiting for review.
- [x] **Design phase for the next three experiments (2026-08-15) —
      protocols only, nothing executed:**
  - **EXP-003C protocol expanded** (`experiments/EXP-003.md` §9): data
    (reuses cached features, no new extraction), feature groups (same
    3), model (multinomial logistic regression extension of DEC-015,
    same discipline), metrics (accuracy/macro-F1/weighted-F1/per-class/
    confusion matrix, explicit focus on human↔ai_assisted,
    human↔full_ai, ai_assisted↔full_ai confusion pairs), and an explicit,
    justified resolution of the sentence-level question: **provenance
    DOES support exact 3-class sentence labels** (not a labeling
    problem), but sentence-level 3-class is **deferred, not attempted**,
    for stated reasons (comparability with A/B, an untested feature-
    validity question for aggregate stylometric features on isolated
    sentences, further-worsened class imbalance).
  - **FAIR-001 protocol designed** (`experiments/FAIR-001.md`,
    DEC-018): a critical feasibility check (a legitimate design-phase
    data inspection, not execution) found the frozen test split has
    only **1 of 23 families with `ell_status=Yes`** — insufficient for
    any comparison. Design response: score all 150 families with the
    already-frozen model (deterministic re-application, not retraining
    or reselection), raising the subgroup to 10 — still small, an
    **inconclusive result is anticipated and disclosed in advance**, not
    discovered later and downplayed. Small-sample threshold (n<10 →
    "insufficient data") fixed before any execution.
  - **GEN-001 protocol designed** (`experiments/GEN-001.md`, DEC-019):
    recommends **Phi-3.5-mini-instruct** (MIT, local, free, genuinely
    different vendor/corpus from Qwen) as the held-out generator, scoped
    to `full_ai` only for this first pass (`ai_assisted` cross-generator
    testing explicitly deferred with stated reasons, not silently
    dropped). Reuses PRIMARY-DATASET-v1's existing 23 test-split human
    essays unmodified — only new `full_ai` counterparts would be
    generated, stored separately, never merged into PRIMARY-DATASET-v1.
  - 2 new decision records (DEC-018, DEC-019), both Provisional/
    design-only.
  - 3 new protocol-correctness tests (`test_fair001_gen001_protocol.py`)
    — verify the underlying feasibility/reuse claims against real data,
    not the (unimplemented) experiments themselves.
  - **No model trained, no new AI samples generated, no generator
    downloaded, no experiment executed.**
- [x] **EXP-003C — three-class (human/full_ai/ai_assisted), essay-level,
      executed once per the approved protocol (2026-08-15). GEN-001 and
      FAIR-001 explicitly NOT run.**
  - Dataset: 425 essays merged from cached EXP-003A/EXP-003B feature
    vectors (150 human rows verified byte-identical between sources
    before merging — no new feature extraction). Split: train 298
    (105/103/90), validation 65 (22/22/21), test 62 (23/23/16). **0
    family-leakage violations.** 0 missing feature values.
  - Baseline (majority = human): validation accuracy 33.8%, macro-F1
    0.169.
  - Feature-group comparison (validation): stylometric-only and
    combined tied **exactly** (67.7% accuracy, macro-F1 0.559, same
    chosen `C`) — LM-only weaker (53.8%, macro-F1 0.432). **Third
    independent experiment finding no LM contribution** (after
    EXP-003A, EXP-003B-R1).
  - **Frozen test result: 72.6% accuracy (45/62), macro-F1 0.564,
    weighted-F1 0.628.**
  - **`full_ai` remains essentially perfect: 23/23 recall.**
  - **`ai_assisted` collapsed completely: 0/16 correct** — precision/
    recall/F1 all exactly 0.0. 15 of 16 misclassified as `human`, 1 as
    `full_ai`. **`human`→`ai_assisted` confusion: 0 cases** — the
    failure is one-directional, not symmetric.
  - Per-sample probability inspection (not just the final decision)
    shows the model carries real, elevated `ai_assisted` signal
    (~0.38–0.45, above the 30.2% training base rate) that the plain-
    argmax decision rule couldn't convert into correct predictions —
    an honest nuance beyond the stark 0/16, not a different result.
  - Cross-experiment note: family `302DC21A6DEE` was misclassified
    again — its `human` sample predicted `full_ai` (margin 0.006, the
    narrowest possible call), its `ai_assisted` sample also predicted
    `full_ai`. **Third separate experiment (after A and B) where this
    one essay behaves atypically.**
  - DEC-004 updated with this as a third independent data point (status
    stays open, pattern now consistent across 3 designs). DEC-014/015/
    017 left unchanged — no new evidence warranted a change.
  - 5 new tests (`test_run_exp003c.py`) — multiclass metrics/confusion-
    matrix correctness, merge-file integrity; none assert a particular
    performance number.
  - Full report: [reports/EXP-003C.md](../reports/EXP-003C.md). Raw
    outputs: `experiments/EXP-003C/features_essay.jsonl`,
    `experiments/EXP-003C/results.json`.
  - **GEN-001, FAIR-001, sentence-level three-class, NLI, and cross-
    generator work explicitly NOT run** — stop condition, waiting for
    review.

## In Progress

- [ ] **Stopped for review, as explicitly instructed** (required after
      EXP-003C). Not running GEN-001 or FAIR-001, not downloading a
      generator, not running sentence-level three-class, not modifying
      PRIMARY-DATASET-v1 or the frozen test set, not adding NLI, not
      optimizing the production application.
- [ ] Whether/how to improve `ai_assisted` detection given EXP-003C's
      complete essay-level collapse (0/16) — genuinely open; the
      per-sample probability nuance (§12 of reports/EXP-003C.md)
      suggests a different decision rule or class-weighting could help,
      neither attempted nor recommended yet.
- [ ] FAIR-001 — protocol complete (experiments/FAIR-001.md, DEC-018),
      not executed. Anticipated to be inconclusive given n=10 subgroup
      size — disclosed in the design, not a reason to skip running it.
- [ ] GEN-001 — protocol complete (experiments/GEN-001.md, DEC-019),
      not executed. No generator downloaded yet.
- [ ] Whether to add a validation-signal-strength guard to threshold
      selection (DEC-015's Revisit-When item, from EXP-003B's
      degenerate essay-level threshold) — flagged, not designed.
- [ ] Whether/how to address the automated screen's documented miss rate
      (NLI, DEC-012 Alternative B) — documented as future work, not
      designed or implemented, per explicit instruction not to add it
      reactively.
- [ ] Sentence-moderate instruction redesign — 3 candidates drafted, not
      tested; not part of the primary dataset regardless.

## Experiments

- `EXP-DATA-001` — 60 samples, 2026-08-10. Preserved.
- `EXP-DATA-001-R1` — 18 records, n=3/category, 2026-08-10.
- `EXP-DATA-001-R1-confirmation` — 50 records, n=10/category, 2026-08-10.
- `EXP-DATA-001-R2` — 60 records (2×30), n=10/category, two separate
  paragraph/sentence experiments, 2026-08-13.
- `EXP-DATA-001-R3` — 86 records (50 sentence-light + 36 paragraph
  claim-survival), n=25/12, two separate experiments, 2026-08-13.
- `EXP-DATA-001-R4` — 20 records (10 human + 10 full_ai), n=10,
  pre-scale regression check, 2026-08-14. Clean, no regression.

These six are data-generation-pipeline validation experiments — the
evidence base for the strategic decision above and the go/no-go check
for scaling. None involves a detector; no detection accuracy/F1/
generalization claim is made from any of them.

**`PRIMARY-DATASET-v1`** — 450 records generated (150 families × 3
categories), 425 in the final inclusion manifest, constructed
2026-08-14/15. This IS the primary dataset — see
[reports/FINAL-DATASET-CONSTRUCTION.md](../reports/FINAL-DATASET-CONSTRUCTION.md).

**`EXP-003A`** — the first real detector-signal experiment: 298 essays
(human vs. full_ai), executed 2026-08-15, single frozen test evaluation
(45–46/46 depending on threshold choice). See
[reports/EXP-003A.md](../reports/EXP-003A.md). Scoped explicitly to
this benchmark and this one class pair — not a general AI-detection
accuracy claim.

**`EXP-003B`** — human vs. ai_assisted, essay-level (chance-level, a
real negative result) + sentence-level localization (real, imprecise
signal), executed 2026-08-15. See
[reports/EXP-003B.md](../reports/EXP-003B.md). Scoped to one generation
mechanism (`sentence_light_controlled_v2`) — not evidence about
`sentence_moderate_controlled_v2` or paragraph-level assistance.

**`EXP-003B-R1`** — diagnostic, reuses EXP-003B's sentence-level dataset
unchanged: does localization survive removing length/count features?
Executed 2026-08-15. See
[reports/EXP-003B-R1.md](../reports/EXP-003B-R1.md). Yes — non-length
features alone reach 46.7% top-1 accuracy, comparable to length/count
alone (40.0%); LM-only is the weakest group tested (13.3%).

**`EXP-003C`** — three-class (human/full_ai/ai_assisted), essay-level,
merged from cached EXP-003A/B feature vectors (no new extraction).
Executed 2026-08-15. See "Current Phase" above and
[reports/EXP-003C.md](../reports/EXP-003C.md). `full_ai` remains
essentially perfect (23/23 recall); `ai_assisted` collapses completely
(0/16 correct, 15 absorbed into `human`); overall accuracy 72.6%,
macro-F1 0.564. Scoped to this benchmark, this generation model — not
general AI detection.

## Current Known Problems

- **PRIMARY-DATASET-v1 is frozen** — if EXP-003 surfaces a genuine
  dataset defect, the response is a documented, versioned
  `PRIMARY-DATASET-v2` proposal, not a silent edit to v1. No such defect
  has been found yet.
- **Both automated semantic screens (DEC-012, DEC-013) have a confirmed
  blind spot for meaning-reversal drift, now shown to be WORSE at scale
  than previously documented** — PRIMARY-DATASET-v1 found the DEC-012
  screen missed 75% (6/8) of real sentence-level "changed" samples, not
  the near-zero rate the smaller R3 batch suggested. This is exactly why
  mandatory human review is a hard requirement, not a recommendation —
  and this round is the concrete proof, not a hypothetical one.
- **Sentence-moderate and paragraph-level remain excluded from the
  primary dataset** — not a temporary gap, a scoped decision; revisiting
  either requires new evidence, not just a request to include them.
- Semantic review still has one reviewer (the agent operating this
  pipeline) — no inter-rater reliability figure exists across any round,
  including the 141-sample PRIMARY-DATASET-v1 review.
- Test split's mixed-category (`ai_assisted`) count (16/23 families,
  69.6% acceptance) is proportionally lower than train/validation —
  observed, reported, not resampled. Relevant to anyone using the test
  split for a class-balanced evaluation.
- EXP-DATA-001's original Regime C similarity range (0.07–0.97) predates
  the `autojunk` fix and should be read as approximate.
- EXP-DATA-001-R2's paragraph-level `automated_screen_*` values were
  computed before the two `extract_span_pair` bugs found in R3 were
  fixed — frozen and not recomputed, but should be read with that
  caveat (see DEC-012's "Known Issue" note).
- PERSUADE's `word_count` column unreliability, 4 duplicate
  `essay_id_comp` values, and the general PERSUADE/ELLIPSE domain
  mismatch with real admissions essays remain unchanged (documented
  since Phase 5C) and apply to PRIMARY-DATASET-v1's human essays too.
- The application still does not classify or score essays.

## Decisions Pending

- Authorization to execute GEN-001, next in the approved order (protocol:
  experiments/GEN-001.md, DEC-019) — not executed, per explicit stop
  condition after EXP-003C.
- Authorization to execute FAIR-001 (protocol: experiments/FAIR-001.md,
  DEC-018) — last in the approved order, anticipated inconclusive
  given n=10 subgroup size, still worth running.
- Whether/how to improve `ai_assisted` detection given EXP-003C's
  complete essay-level collapse (0/16) — the per-sample probability
  nuance suggests real but weak signal the plain-argmax rule can't use;
  a class-weighted or cost-sensitive decision rule is a plausible next
  step, not attempted or recommended yet.
- Whether to pursue the non-length stylometric signal further (POS
  ratios, vocabulary, dependency depth — EXP-003B-R1's group E) as the
  more promising direction than the LM instrument.
- Whether a validation-signal-strength guard should be added to
  threshold selection (DEC-015's Revisit-When item).
- Sentence-level three-class — explicitly deferred in EXP-003C's own
  design (experiments/EXP-003.md §9F), not scheduled.
- Sentence-moderate instruction redesign: which of the 3 drafted
  candidates (or another) to test — independent of GEN-001/FAIR-001,
  future work.
- A reversal-sensitive screening signal (NLI, DEC-012 Alternative B) —
  design not started, future work, explicitly not part of this phase.
- Scoring/calibration method (Phase 6) — depends on GEN-001/FAIR-001
  results and any `ai_assisted`-detection improvement work.
- Passage-grouping strategy (Phase 7).

## Next Steps (pending review — not started)

1. User reviews [reports/EXP-003C.md](../reports/EXP-003C.md) — the
   three-class result, especially `ai_assisted`'s complete essay-level
   collapse and its asymmetric confusion pattern.
2. If approved: execute GEN-001 next (per the approved order), per its
   already-complete design (experiments/GEN-001.md, DEC-019) — small,
   local, free held-out generalization test, `full_ai` category only.
3. FAIR-001 follows GEN-001 in the approved order — not blocking, but
   not run automatically either.
4. GEN-001's held-out evaluation uses the already-frozen EXP-003A model
   unchanged — no refitting on the new generator's data under any
   circumstance.
5. Sentence-moderate redesign testing and the NLI reversal-detection
   signal remain separate future-work tracks, not blockers for GEN-001
   or FAIR-001.
6. Continue to hold off on FAIR-001, GEN-001, sentence-level three-class,
   NLI, cross-generator work beyond GEN-001's first pass, and any
   broader accuracy/F1 claims until explicitly authorized.
