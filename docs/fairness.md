# Fairness

> Status: **Design only, 2026-08-15 — not executed.** A concrete
> evaluation plan now exists (below), using PERSUADE's `ell_status`
> field and, for a future extension, ELLIPSE's continuous proficiency
> scores — but no fairness evaluation has been run against
> PRIMARY-DATASET-v1 or any detector. This document is not a claim that
> fairness has been evaluated or established; see
> [EXP-003.md](experiments/EXP-003.md) §12 for how this fits into the
> current detector-experiment design phase.

## Concrete evaluation design (not yet executed)

**Data source**: PRIMARY-DATASET-v1's `human` records carry
`family_id == essay_id_comp`, the same key used in the original
PERSUADE 2.0 CSV, which includes `ell_status` (`Yes`/`No`, ~2,244
`Yes` / ~22,451 `No` / ~1,209 unlabeled in the full corpus) — a direct,
non-inferred, already-collected subgroup label. `full_ai` and
`ai_assisted` samples share their family's `family_id`, so the same
join recovers the seed essay's `ell_status` for every sample in a
family, including AI-touched ones (the label describes the *human
writer* the family originated from, not the AI text itself — this
distinction matters and must be stated in any future report using it).

**Procedure** (when executed, not now):
1. Join `ell_status` onto PRIMARY-DATASET-v1's manifest via `family_id`
   — **in a separate join table, never merged into the training feature
   matrix**. This mirrors this project's existing near-duplicate/QC
   metadata pattern (rich provenance kept alongside, not inside, the
   feature vectors a model trains on).
2. For a trained detector (EXP-003A/B, post-freeze), compare, split by
   `ell_status`:
   - False-positive rate (human essays incorrectly flagged)
   - False-negative rate (AI/mixed essays missed)
   - Detector-score/evidence-strength distribution
   - Which IMPLEMENTED features (feature-inventory.md) most differ
     between `ell_status` groups **independent of the AI/human label** —
     i.e., checking whether the *feature distributions themselves*
     already differ by language-learner status for reasons unrelated to
     AI assistance (the core concern below), not just whether the
     final detector's error rate differs.
3. Report disparities plainly if found, with magnitude and which
   features appear to drive them — never a bare "no disparity found"
   without the actual comparison behind it.

**Future extension (not part of the current dataset)**: ELLIPSE
(`data/raw/ellipse_corpus/ELLIPSE_Final_github.csv`) provides continuous
proficiency sub-scores (Cohesion, Syntax, Vocabulary, Phraseology,
Grammar, Conventions, Overall) for a separate corpus of English-language
-learner writing — a finer-grained proficiency signal than PERSUADE's
binary `ell_status`. Incorporating ELLIPSE requires its own dataset
extension (DEC-009 anticipated this; not built) and is **not** part of
PRIMARY-DATASET-v1 — noted here as the natural next step once a fairness
evaluation using PERSUADE's `ell_status` alone has actually run.

**Explicitly excluded as detector features or labels, per instruction**:
`gender`, `race_ethnicity`, `economically_disadvantaged`,
`student_disability_status` — all present in the raw PERSUADE CSV, none
carried into any generated sample record already (verified: `make_human_record`
and every generation function only ever read `essay_id_comp`/`full_text`/
`word_count`/`prompt_name`/`task`/`assignment` from the source row —
see `scripts/run_exp_data_001.py::load_candidate_records`), and none
will be joined in for detector training or evaluation, only for the
fairness comparison above, and even there never as a model input.

**Known limitations of this plan, stated now**:
- `ell_status` is binary and self/institution-reported in PERSUADE, not
  a continuous or independently-verified proficiency measure — ELLIPSE's
  richer scores would improve this if incorporated later.
- ~1,209 PERSUADE essays have no `ell_status` label — any essay whose
  seed lacks a label is excluded from the fairness comparison, not
  imputed.
- The comparison describes the *source human writer's* subgroup for a
  whole family, including its AI-touched samples — it cannot say
  anything about the AI generation model's own behavior conditioned on
  a subgroup, only about detector error rates on writing *originating
  from* essays by writers in that subgroup.

## Core concern

Second-language English writers often produce writing with different
statistical characteristics than native-English writers (e.g. different
sentence-length distributions, different rates of certain function-word
usage, potentially different perplexity under an English-trained language
model) for reasons unrelated to AI assistance. If the detector's reference
distributions or scoring conflate "unusual relative to a general human
reference" with "AI-like," second-language writers could be
disproportionately flagged. This is a real risk to investigate, not an
assumed conclusion.

## Planned methodology (Phase 12)

- Use only evaluation data with appropriate, explicitly-consented subgroup
  labels — never infer language background or any other sensitive
  attribute from the writing itself (Section 16: "Do not infer someone's
  identity from writing").
- Compare, across labeled subgroups where such data is available:
  - false-positive rate
  - false-negative rate
  - confidence/evidence-strength distribution
  - the underlying feature distributions that most influence scoring
    (e.g. perplexity, sentence-length variance, lexical diversity)
- Report disparities plainly if found, including the magnitude and which
  features appear to drive them.
- Propose mitigations only backed by the observed disparity (e.g.
  subgroup-aware reference distributions, feature reweighting) — not
  generic fairness boilerplate.

## Ground rule

No fairness claim ("this system is fair" or "no disparity was found") will
appear in this document unless backed by an actual evaluation on
appropriately labeled data. If no such data is available, that limitation
will be stated explicitly rather than the analysis being skipped silently.
