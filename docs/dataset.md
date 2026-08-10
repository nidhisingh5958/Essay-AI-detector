# Dataset

> Status: not started. No data has been collected, generated, or committed
> yet (see [project-status.md](project-status.md), Phase 5). This document
> reserves the structure the brief requires (Section 12/37) — every field
> below is filled in only once it is actually true, and this notice is
> removed once real dataset work lands.

## Required documentation (to be completed in Phase 5)

- **Source(s)** of human-written essays — must have clear provenance and
  a license compatible with use in this project.
- **License(s)** for each source.
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
