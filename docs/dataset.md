# Dataset

> Status: source research complete, no data downloaded yet (see
> [project-status.md](project-status.md), Phase 5). This document
> reserves the structure the brief requires (Section 12/37) — every field
> below is filled in only once it is actually true.

## Human-writing source(s) — selected, Provisional

Selected after comparing seven candidate sources against provenance,
licensing, domain relevance, size, and privacy — full comparison in
[dataset-source-comparison.md](dataset-source-comparison.md), decision
recorded in
[decisions/DEC-009-human-dataset-source.md](decisions/DEC-009-human-dataset-source.md):

- **PERSUADE 2.0** (The Learning Agency Lab / Georgia State University) —
  primary corpus for general reference distributions. ~25,000
  argumentative essays, grades 6–12, CC BY-NC-SA 4.0 (license framing has
  a discrepancy across sources that must be resolved against Kaggle's
  authoritative metadata before download — see DEC-009).
- **ELLIPSE Corpus** (Vanderbilt University / The Learning Agency Lab) —
  reserved for the Phase 12 fairness analysis specifically, because it
  carries genuine English-language-proficiency labels. ~6,500 essays,
  grades 8–12, CC BY-NC-SA 4.0.

Both are marked **Provisional**, not Accepted: no file has been
downloaded or inspected yet, and DEC-009 requires the license field to be
verified programmatically (against Kaggle's own dataset metadata) as the
first step of the acquisition script, before anything is kept.

**Known domain mismatch, stated plainly:** both corpora are
argumentative/proficiency-assessment student essays, not personal-
narrative college admissions essays. No available, appropriately-licensed
corpus of genuine admissions essays was found — the closest domain match
(colleges' own published "Essays That Worked" examples) was rejected for
licensing/consent reasons (see DEC-009). This mismatch will be stated
again in `docs/evaluation.md` once real results exist, not minimized.

## Required documentation (remaining, to be completed as Phase 5 proceeds)

- **License(s)** for each source — see above; final confirmation pending
  the programmatic check described in DEC-009.
- **Machine-written sample generation** — which model(s), which prompts,
  and why those were chosen (recorded as a decision in
  [decisions/](decisions/) when implemented).
- **Mixed / AI-polished sample generation** — how "AI touched some
  sentences" examples are constructed, since this is a core requirement
  (Section 11) and not just human-vs-machine.
- **Dataset size** and human/machine/mixed distribution.
- **Topics and domains** covered, and how representative they are of
  actual admissions essays.
- **Preprocessing and deduplication** steps.
- **Train/validation/test split strategy**, with explicit attention to
  leakage prevention (Section 13) — splitting by source essay, not by
  row, so transformed versions of the same underlying essay never cross
  splits.
- **Known limitations and biases** — including topic coverage, writer
  demographics (to the extent knowable and appropriately labeled), and
  any skew introduced by the machine-sample generation process.

## Explicit constraint

Raw datasets are not committed to this repository (Section 12: "Do not
commit huge datasets into Git"). Once Phase 5 lands, this repository will
instead contain:

- `scripts/` — reproducible download/generation/cleaning scripts
- `data/` — gitignored working directory populated by those scripts
- This document — describing what the scripts produce, with real numbers
  once they have actually been run
