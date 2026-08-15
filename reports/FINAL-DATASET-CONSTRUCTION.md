# FINAL-DATASET-CONSTRUCTION — PRIMARY-DATASET-v1

**Date**: 2026-08-14/15
**Status**: Dataset constructed and reviewed. **Detector work NOT
started** — this report is a stop-for-review checkpoint, per explicit
instruction.

## 1. Seed selection

Source: PERSUADE 2.0 (`data/raw/persuade_2.0/persuade_2.0_human_scores_demo_id_github.csv`),
`task == "Independent"` subset, word count in `[150, 320]`.

150 fresh seeds selected via `generation_utils.select_seed_essays()`
(`min_sentences=5, min_paragraphs=2, rng_seed=50`), excluding all **90**
seed IDs used across every prior generation experiment (EXP-DATA-001,
R1, R1-confirmation, R2-paragraph, R2-sentence, R3-sentence-light,
R3-paragraph-claim-survival, R4-full-ai-regression). Verified
programmatically: **0 overlap** between the 150 new seeds and the 90
prior seeds; 150 confirmed-unique new family IDs.

## 2. Family construction

Each of the 150 seeds is one family. Every family produced exactly
three sample records: `human` (unmodified), `full_ai` (whole-essay
generation), `sentence_light_controlled_v2` (surgical single-sentence
splice, full-paragraph context, light-copy-edit instruction) — the
same, unmodified mechanisms validated in EXP-DATA-001 through R4. No
`sentence_moderate_controlled_v2` or `paragraph_*` samples were
generated, per the Strategic Decision.

## 3. Split allocation

Assigned **before** generation via `generation_utils.assign_family_splits()`
(`rng_seed=50`, ratios 70/15/15), the existing, unmodified, already-
validated function:

| Split | Families | % |
|---|---|---|
| train | 105 | 70.0% |
| validation | 22 | 14.7% |
| test | 23 | 15.3% |
| **Total** | **150** | 100% |

**Hard invariant verified**: `find_family_split_violations()` run
against the full 450-record samples file returns **0 violations** —
every family's `human`/`full_ai`/`sentence_light_controlled_v2` records
share exactly one split. (Also re-verified across all 8 prior experiment
data files in this project: 0 violations everywhere — see
`scripts/tests/test_generation_utils.py`.)

## 4. Generation counts

| Category | Generated | QC passed | QC flagged | QC rejected |
|---|---|---|---|---|
| `human` | 150 | — (no QC applies) | — | — |
| `full_ai` | 150 | 148 | 2 | 0 |
| `sentence_light_controlled_v2` | 150 | 134 | 7 | 9 |
| **Total** | **450** | | | |

One background interruption occurred during this ~450-record,
multi-hour generation run (this environment's known behavior); resumed
cleanly via the established resumable pattern (checked `samples.jsonl`,
skipped completed `sample_id`s) — no duplicate or lost records.

## 5. QC results

**`full_ai` (2 flagged)**: both are genuine `ai_self_reference` —
output began "As an AI language model..." — confirmed real on manual
inspection, not false positives. **Excluded from the manifest.**
**0 instruction-leakage flags.**

**`sentence_light_controlled_v2` (7 flagged, 9 rejected)** — QC note
breakdown (a record can carry more than one note):

| Note | Count |
|---|---|
| `modification_scope_drift` (length ratio outside [0.7, 1.3]) | 13 |
| `splice_resegmentation_mismatch` (span boundaries untrustworthy) | 9 |
| `instruction_artifact_preamble` | 1 |

The 9 `splice_resegmentation_mismatch` records are hard-rejected — span
boundaries not trustworthy, never entered semantic review
(`semantic_preservation` stays `not_yet_reviewed`), excluded from the
manifest by construction. The `modification_scope_drift`/
`instruction_artifact_preamble` flags are QC *notices*, not hard
rejections — these 7 samples still underwent full mandatory human
review, same precedent as EXP-DATA-001-R3 (a length-ratio flag measures
structural fit, not meaning — see failure-analysis.md's headline
finding). **0 instruction-leakage flags, 0 self-reference flags** for
this category.

**No new failure mode was found** — every QC note type observed is
already documented from prior rounds (EXP-DATA-001 through R4). No stop
was triggered under the "new failure mode" clause.

## 6. Automated semantic-screen (DEC-012) results

Applied to all 141 `sentence_light_controlled_v2` records with a
resolvable span (150 − 9 hard-rejected):

| Label | Count |
|---|---|
| `likely_preserved` | 119 |
| `needs_review` | 22 |
| `likely_changed` | 0 |

**Screening only — see §8 for how this compared against mandatory human
review, including a significant miss rate this round.**

## 7. Human semantic review

**Every one of the 141 resolvable-span `sentence_light_controlled_v2`
samples received full manual review** against the documented drift
protocol (generation-methodology.md §12) — not a sample, not a
screen-triaged subset.

| Result | Count | % |
|---|---|---|
| `preserved` | 127 | 90.1% |
| `questionable` | 6 | 4.3% |
| `changed` | 8 | 5.7% |

This is a **larger, real drift rate than EXP-DATA-001-R3's smaller
sample showed** (R3: 1/25 = 4% changed at n=25; this round: 8/141 =
5.7% changed at n=141) — consistent with this project's established
expectation that larger samples surface rare failure modes a smaller
sample can miss, not a regression in the mechanism itself. Reported
honestly, not smoothed toward the earlier, more optimistic figure.

**Representative confirmed drift cases** (full list and rationale in
the samples file's `semantic_preservation_notes` field):
- **Full position reversal** (`A4106D0F4F19`): "Operating a mobile
  device should **not be allowed**" → "should **not be discouraged**"
  — states the opposite stance.
- **Negation dropped** (`64E208B0CC5E`): "...**not** take every thing
  serious" → "...handle things seriously" — literal meaning inverted.
- **Causal reversal** (`20D2723ED2DB`): "...won't consider doing
  school **because** you got rid of their favorite sport" → "...
  **despite** you getting rid of..." — opposite causal direction.
- **Agent/subject substitution** (`9FEEF0F10C42`): "**Schools** should
  offer classes...at home" → "**Students** should offer classes...at
  home."
- **Fabricated claim** (`DB133A962C7B`): a vague one-line original
  ("It is not that is interferes with their driving") was expanded with
  an entirely invented, specific claim about "lack of processing power
  in the driver's mind" with no basis in the source.

## 8. Automated screen vs. human review — disagreements (documented, not overridden)

Per explicit instruction, every disagreement is recorded, and **the
automated screen never overrode a human decision** in constructing this
dataset.

| automated_screen_label | semantic_preservation | Count |
|---|---|---|
| `likely_preserved` | `preserved` | 110 |
| `likely_preserved` | `questionable` | 3 |
| `likely_preserved` | **`changed`** | **6** |
| `needs_review` | `preserved` | 17 |
| `needs_review` | `questionable` | 3 |
| `needs_review` | **`changed`** | **2** |

**This is a significant, honestly-reported finding: 6 of the 8 real
`"changed"` samples (75%) were labeled `likely_preserved` by the
automated screen.** This is a materially higher miss rate than
EXP-DATA-001-R3's sentence-light batch showed (0/1 missed at n=25) —
the first time the screen's "changed" miss rate has been this high at
the *sentence* level specifically (DEC-012's previously-documented miss
rate was paragraph-level-only, from R3). All 6 missed cases are
meaning-reversal or claim-substitution drift that preserves high
embedding similarity and touches no number/entity — the exact
theoretical gap DEC-012 named and DEC-013 also could not close at the
paragraph level in R3, now confirmed to recur at the sentence level too,
at a materially higher rate than previously observed. **This is
updated into DEC-012 (see docs/decision-summary.md and DEC-012 itself)
as new, larger-scale, more severe evidence — not swept under the R3
paragraph-only framing.**

Every sample in this table that is `changed` or `questionable` — 14
samples total, regardless of automated screen label — is **excluded**
from the high-confidence benchmark. This dataset construction is the
concrete proof this project's "human review is the final label
authority" policy is not a formality: had the automated screen alone
been trusted, 6 real "changed" samples and 3 "questionable" ones would
have entered the benchmark as false positive ground truth.

## 9. Duplicate statistics

Naive O(n²) `near_duplicate_pairs_scoped` over 450 texts (~101,000
pairs) did not complete in reasonable time — not previously exercised
at this scale. A performance-only optimization was built
(`scripts/check_primary_dataset_duplicates.py`): a word-5-gram shingle
Jaccard pre-filter (mathematically safe — cannot produce a false
negative relative to the unmodified `near_duplicate_pairs_scoped`
threshold logic, which itself was not changed) reduced the real
comparison count from ~101,025 to **145** pairs, completing in seconds.

**Result: 0 cross-family duplicates.** 148 same-family matches
(expected and informational — a sentence-light splice is naturally
near-identical to its own human source; never treated as suspicious,
per DEC-011's established near-duplicate scoping design).

## 10. Leakage checks

| Check | Result |
|---|---|
| Family split violations | **0** |
| Cross-family duplicates | **0** |
| Overlap with 90 prior-experiment seeds | **0** |
| Instruction leakage (`full_ai` + `sentence_light`) | **0** |
| Metadata integrity (all required fields present) | **0 missing**, all 450 records |
| Provenance (`family_id` consistency, `source_sample_id` correctness) | Verified, no issues |

## 11. Final inclusion manifest

`data/generated/PRIMARY-DATASET-v1/inclusion_manifest.json`
(`scripts/build_primary_dataset_manifest.py`) — generated by filtering
the complete `samples.jsonl`, not by assuming every generated record is
valid.

**Inclusion rules** (documented plainly, including the one judgment
call):
- `human`: always included.
- `full_ai`: included iff `qc_status == "passed"` (excludes the 2 real
  self-reference samples).
- `sentence_light_controlled_v2`: included iff `semantic_preservation
  == "preserved"` — **including 6 samples with `qc_status == "flagged"`**
  (a length-ratio notice, not a semantic judgment) that a human reviewer
  confirmed were meaning-preserved, same precedent as
  EXP-DATA-001-R3. If this judgment call is not wanted, the strict
  `qc_status == "passed"`-only count would be **121** instead of 127 —
  both numbers are given here so this choice is auditable and
  reversible.

| Category | Included |
|---|---|
| `human` | 150 |
| `full_ai` | 148 |
| `sentence_light_controlled_v2` (`ai_assisted`) | 127 |
| **Total benchmark size** | **425** |

**Excluded, retained for failure analysis, never used as positive
ground truth**: 25 records total (2 `full_ai` self-reference, 9
sentence-light hard-QC-rejected, 6 `questionable`, 8 `changed`) — all
remain in `samples.jsonl` with full metadata, QC results, screen
results, and review notes intact.

## 12. Class distribution by split

| Split | human | full_ai | mixed (`ai_assisted`) | Split total |
|---|---|---|---|---|
| train | 105 | 103 | 90 | 298 |
| validation | 22 | 22 | 21 | 65 |
| test | 23 | 23 | 16 | 62 |
| **Total** | **150** | **148** | **127** | **425** |

**Observed imbalance, reported rather than resampled** (per explicit
instruction): the mixed-category acceptance rate varies notably by
split — train 90/105 (85.7%), validation 21/22 (95.5%), **test 16/23
(69.6%)**. At test's n=23, this is plausibly ordinary sampling variance
(the seeds landing in test were not selected for any content property,
just by the pre-generation RNG split), but it is flagged here rather
than silently accepted: anyone using the `test` split for a mixed-class
evaluation should be aware its `ai_assisted` count (16) is
proportionally smaller than train/validation's, and no regeneration was
done to correct it, per explicit instruction not to resample toward a
target count.

## 13. Limitations

- **Automated screen miss rate at sentence-level scale is worse than
  previously documented** — 6/8 (75%) of real `"changed"` samples this
  round were `likely_preserved`. See §8. This is now the primary,
  concrete justification for treating human review as non-optional,
  not a hypothetical.
- **Single reviewer** (the agent operating this pipeline) reviewed all
  141 samples — no inter-rater reliability figure exists for this or
  any prior round.
- **`sentence_moderate_controlled_v2` and paragraph-level categories
  remain entirely excluded** from this dataset — this benchmark does
  not represent the full space of AI-assisted writing this project's
  methodology explored, by design (DEC-011's Strategic Decision).
- **Test split's mixed-category count (16) is proportionally smaller**
  than train/validation — see §12.
- **No held-out generalization test** (a hosted-API-generated sample,
  DEC-010's deferred alternative) exists in this dataset — everything
  is generated by the same Qwen2.5-1.5B-Instruct model/revision.
- **PERSUADE/ELLIPSE domain-mismatch and `word_count` caveats**
  (documented since Phase 5C) remain unchanged and apply to this
  dataset's human essays as they did to every prior experiment's.
- **Fairness/demographic metadata was not attached to this dataset
  construction** — per §14/item 13 of the review, no demographic field
  was used as a feature or label; this dataset's scope is the
  human/full_ai/mixed detection benchmark only, not a fairness
  evaluation set (that remains separate future work per DEC-009).

## 14. Reproducibility record

| Field | Value |
|---|---|
| Source corpus | PERSUADE 2.0, `persuade_2.0_human_scores_demo_id_github.csv` |
| Seed selection method | `generation_utils.select_seed_essays`, `rng_seed=50` (`RNG_SEED=42 + 8`) |
| Split assignment method | `generation_utils.assign_family_splits`, `rng_seed=50`, ratios (0.7, 0.15, 0.15) |
| Family IDs | `data/generated/PRIMARY-DATASET-v1/samples.jsonl` (`family_id` field, 150 unique) |
| Generation model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Model revision | `989aa7980e4cf806f80c7fef2b1adb7bc71aa306` |
| `full_ai` config | temperature 0.85, top_p 0.95, per-sample seed (see `generation_config` field) |
| `sentence_light_controlled_v2` config | temperature 0.6, top_p 0.95, per-sample seed (see `generation_config` field) |
| Transformation config | `SENTENCE_LIGHT_CONTROLLED_V2_INSTRUCTION`/`_META` (`run_exp_data_001_r2_sentence.py`, unchanged since R2) |
| Construction script | `scripts/run_primary_dataset_v1.py` |
| QC version | `run_qc_common` + `modification_scope_drift`/`splice_resegmentation_mismatch` checks, unchanged since EXP-DATA-001-R2 |
| Semantic-screen version | DEC-012 `semantic_screen.py`, thresholds unchanged since calibration (`preserved_threshold=0.75, review_band=0.35`) |
| Manifest builder | `scripts/build_primary_dataset_manifest.py` |
| Construction dates | 2026-08-14 (generation) – 2026-08-15 (review, manifest, this report) |

A future reviewer can reproduce the seed/split selection exactly by
re-running `select_seed_essays`/`assign_family_splits` with the values
above against the same PERSUADE CSV, or read the exact family IDs
directly from `samples.jsonl`.

## Explicit non-findings

- No detector was trained, tuned, or evaluated.
- No accuracy, F1, or performance claim is made — none exists to make.
- No new generation methodology was introduced; every mechanism used
  was already validated in EXP-DATA-001 through R4.
- The apparent worsening of the automated screen's miss rate (§8) is
  reported as new evidence about the screen's reliability, not as a
  claim that the underlying `sentence_light_controlled_v2` generation
  mechanism itself got worse — 90.1% preserved at n=141 remains the
  strongest evidence profile of any sub-mechanism this project has
  produced.

**Per the stop condition: reporting and stopping here. No detector
training, threshold tuning, EXP-003, accuracy/F1 claims, or UI
evaluation follow from this report without further explicit review.**
