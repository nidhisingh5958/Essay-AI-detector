# Dataset

> Status: human corpus **acquired, live-verified, and inspected** (see
> [project-status.md](project-status.md), Phase 5C, and the full
> [dataset inspection report](../reports/dataset-inspection.md)). No
> AI/mixed samples have been generated yet, and no train/validation/test
> split exists yet — those remain Phase 5D+.

## Human-writing source(s) — Accepted

Selected after comparing seven candidate sources against provenance,
licensing, domain relevance, size, and privacy — full comparison in
[dataset-source-comparison.md](dataset-source-comparison.md), decision
recorded in
[decisions/DEC-009-human-dataset-source.md](decisions/DEC-009-human-dataset-source.md)
(**Accepted** as of 2026-08-10, after live license verification and file
inspection — originally Provisional based on web research only):

- **PERSUADE 2.0** — primary corpus for general reference distributions.
  **Confirmed via the actual acquired file**
  (`persuade_2.0_human_scores_demo_id_github.csv`): 25,996 essays
  (25,992 unique IDs — 4 collide, see inspection report), grades 6–12,
  15 prompts each with full instruction text, two task types
  (`Independent` / `Text dependent`). **Live-verified license:
  CC BY-NC-SA 4.0** — this resolves the discrepancy noted during the
  research phase (Kaggle's authoritative metadata matches the GitHub
  repo's framing, not the Learning Agency Lab site's "CC BY 4.0" framing).
- **ELLIPSE Corpus** — used for the Phase 12 fairness analysis. Confirmed
  via the actual file (`ELLIPSE_Final_github.csv`): 6,482 essays, 44
  unique prompts (correcting the ~29 estimated from web research), seven
  proficiency scores (Overall + six analytic sub-scores). **Live-verified
  license: CC BY-NC-SA 4.0**, exactly as expected, no discrepancy. Note:
  ELLIPSE is 100% English Language Learners by corpus design — see
  "Refined fairness methodology" below.

Full schema, statistics, data-quality findings, and per-corpus
limitations: [reports/dataset-inspection.md](../reports/dataset-inspection.md).
That report is the authoritative source for every number about these two
corpora going forward — this document summarizes it, not the reverse.

**Real data-quality issues found on inspection (documented, not
disqualifying):** PERSUADE's corpus-provided `word_count` column
disagrees with a direct recount for ~5% of rows (worst case: a 48x
discrepancy) — our pipeline already recomputes word counts independently
(Phase 3), so this doesn't block anything, but the column itself must
never be trusted. 4 PERSUADE `essay_id_comp` values collide across
different essays (a source-data bug, not duplicate content). Both
corpora preserve paragraph boundaries via blank-line markers in ~95% of
essays — resolving the open question from Phase 5B about whether
paragraph-level mixed-sample transformations are feasible (they are, for
the ~95% majority).

**Refined fairness methodology:** ELLIPSE cannot supply a non-ELL
comparison group by itself (100% ELL by design). The plan is now: (a) use
ELLIPSE's *continuous* proficiency scores to test whether detector
behavior correlates with proficiency level within the ELL population, and
(b) use PERSUADE's own `ell_status` field (newly confirmed present:
~2,244 "Yes" / ~22,451 "No") for a same-corpus ELL-vs-non-ELL comparison,
rather than comparing across the two different corpora directly. Full
reasoning in DEC-009's "Live Verification & Inspection Update" section.

**Known domain mismatch, stated plainly:** both corpora are
argumentative/proficiency-assessment student essays, not personal-
narrative college admissions essays. No available, appropriately-licensed
corpus of genuine admissions essays was found — the closest domain match
(colleges' own published "Essays That Worked" examples) was rejected for
licensing/consent reasons (see DEC-009). This mismatch will be stated
again in `docs/evaluation.md` once real results exist, not minimized.

## Sensitive metadata handling

Both corpora include demographic columns (gender, race/ethnicity,
economic status, disability status, grade). Per the requirement not to
feed demographic metadata into the detector, the working ML dataset
(once built) will carry forward only: essay text, prompt/task
identifiers, and — kept in a separate evaluation-only table, never joined
into the detector's feature vector — PERSUADE's `ell_status` and
ELLIPSE's proficiency scores, since those are the only fields this
project's actual fairness scope (Section 16: second-language writers)
requires. Other demographic columns are recommended for exclusion
entirely, not just non-use — full reasoning in the inspection report.

## Machine data — designed, not generated

Full-essay machine generation targets the **same prompt and approximate
length** as a paired human seed essay, specifically so the detector can't
succeed by learning topic or length differences between human and machine
text instead of writing-style differences. Model choice:
[DEC-010](decisions/DEC-010-machine-generation-model.md)
(Qwen2.5-1.5B-Instruct, Provisional — not yet downloaded or run). Full
mechanism: [generation-methodology.md](generation-methodology.md),
Section 3.

## Mixed / AI-assisted data — designed, not generated

Eight transformation categories (light/moderate polish, single/multi
sentence rewrite, single/multi paragraph rewrite, heavy revision), each
derived from a human seed essay. The mechanism differs by category —
exact surgical splicing for the sentence/paragraph-rewrite categories,
whole-essay-instruction-plus-diff for the polish/heavy-revision
categories — chosen per category to match what's actually being
simulated. Full design and reasoning:
[DEC-011](decisions/DEC-011-mixed-text-generation.md) and
[generation-methodology.md](generation-methodology.md), Section 4.

## Generation methodology

See [generation-methodology.md](generation-methodology.md) for the
complete walkthrough: family/pairing design, prompt sourcing (extracted
from the acquired corpus's own metadata, not hand-authored categories —
Section 2 there explains why), length matching, diversity strategy, and
quality control.

## Ground-truth construction

Ground truth is **never** produced by running the detector on generated
text — it comes entirely from the known generation process (which
sentences were surgically replaced, or which were diffed as changed).
Each sample records a `ground_truth_confidence` of `high` (full
generation or surgical splice), `approximate` (diff-based polish
categories), or `essay_level_only` (heavy revision, where sentence-level
localization isn't meaningful). See generation-methodology.md Section 9
for the full metadata schema.

## Sentence-level provenance

Every mixed sample's `modified_spans` field records exactly which
sentence(s)/character range(s) are AI-authored, preserved through to
final storage — this is what makes sentence-level detector evaluation
possible later (Phase 10): e.g. checking whether the detector correctly
flags sentences 2–3 of a 4-sentence essay when that's exactly what was
AI-rewritten, not just whether it flagged the essay as "mixed" overall.

## Leakage prevention

**Hard invariant:** every sample derived from one human seed essay (the
original plus all 8 transformations of it) shares one `family_id` and
must be assigned to the same train/validation/test split. Split
assignment happens at the family level *before* generation runs, not
after — see [DEC-011](decisions/DEC-011-mixed-text-generation.md) for why
this ordering specifically matters (generating first and splitting after
is the exact bug this prevents).

## Quality control

Every generated/transformed sample is checked for generation failures
(empty output, out-of-bounds length, prompt leakage, excessive
repetition, leftover instruction artifacts, failed sentence-count
alignment for diff-based categories, exact/near duplicates) before being
accepted. Rejections are logged with a reason, never silently discarded —
full list in generation-methodology.md Section 8. These checks catch
*generation failures*, not "hard to classify" cases — genuinely ambiguous
but well-formed samples are kept, since real mixed writing is often
ambiguous and filtering that out would make the dataset less realistic,
not more.

## Known limitations (dataset design, current)

- **Domain mismatch** (stated above): PERSUADE/ELLIPSE are argumentative/
  proficiency-assessment essays, not personal-narrative admissions
  writing. Machine and mixed samples inherit this same domain, since they
  're generated on the same prompts.
- **Single generation model**: all machine/mixed samples in the initial
  dataset come from one small local model
  ([DEC-010](decisions/DEC-010-machine-generation-model.md)). A detector
  that performs well against this model's output has not been shown to
  generalize to text produced by other/larger models (e.g. what students
  realistically have access to). A held-out slice generated by a
  different, never-used-in-training model is a documented future
  consideration (DEC-010, "Revisit When"), not yet implemented.
- **Approximate ground truth for polish/heavy-revision categories**: the
  diff-based similarity threshold isn't numerically fixed yet — it's
  deferred to real pilot examples (EXP-DATA-001), not guessed.
- **Paragraph-boundary survival — now verified, resolved.** Both corpora
  preserve blank-line paragraph markers in ~95% of essays (see inspection
  report); the paragraph-rewrite categories are feasible for that
  majority, with the remaining single-block essays excluded from that
  category rather than given an invented paragraph split.
- **Machine/mixed generation itself has not been executed.** This section
  describes a design intended for a pilot (EXP-DATA-001, not yet run),
  not a claim about generated samples existing.

## Explicit constraint

Raw datasets are not committed to this repository (Section 12: "Do not
commit huge datasets into Git") — confirmed in practice: `data/raw/`
(852MB + 15MB of acquired files) is gitignored and was never staged. This
repository instead contains:

- `scripts/` — reproducible acquisition/inspection scripts
  (`acquire_dataset.py`, `inspect_corpus.py`), plus generation scripts to
  come (Phase 5D+)
- `data/` — gitignored working directory populated by those scripts
- `reports/dataset-inspection.md` — real numbers from the actual acquired
  files
- This document — summarizing the above, updated to match
