# Methodology

> Status: not yet started. No features, scoring, or calibration exist yet
> (see [project-status.md](project-status.md)). This document reserves the
> structure that will be filled in as Phases 3–7 produce real work — it
> does not describe implemented behavior yet.

## Purpose of this document

Once implemented, this document must clearly separate:

- **What the system measures** — concrete, computed quantities (e.g.
  mean token log-probability, sentence-length coefficient of variation).
- **What the system infers** — a classification derived from comparing
  those measurements to reference distributions, with an explicit
  confidence/uncertainty level.

It must never claim that a measurement or inference *proves* authorship.
Writing style is evidence, not proof.

## Planned sections (to be written in the phases noted)

1. Problem formulation — Phase 1/6 (what "detection" means here: a
   calibrated estimate over writing characteristics, not an authorship
   proof)
2. Hypotheses driving feature selection — Phase 3/4 (recorded per-feature
   in `experiments/`, not asserted here without an experiment behind it)
3. Feature engineering (linguistic, rhythm, vocabulary, repetition,
   syntactic) — Phase 3
4. Language-model instrumentation and what it does/doesn't tell us —
   Phase 4, ties to [DEC-004](decisions/DEC-004-no-llm-classifier.md)
5. Reference-distribution construction — Phase 5
6. Scoring and calibration — Phase 6
7. Sentence-level and passage-level analysis — Phase 7
8. Mixed/AI-polished text handling — Phase 7
9. Uncertainty handling ("insufficient evidence" as a valid output) —
   Phase 6
10. Evaluation methodology (metrics, splits, what counts as "correct") —
    Phase 10

Each of these sections will cite the specific `experiments/EXP-XXX/` run
that justifies the choice made, per [decisions.md](decisions.md)'s
traceability requirement — not written from first-principles reasoning
alone.
