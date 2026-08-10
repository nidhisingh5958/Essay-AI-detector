# Methodology

> Status: Phase 3 feature computation exists (see
> [project-status.md](project-status.md) and
> [decisions/DEC-006-phase3-feature-scope.md](decisions/DEC-006-phase3-feature-scope.md)),
> but scoring, calibration, and reference distributions do not — so
> sections 5–10 below remain unwritten. Section 3 (feature engineering) is
> filled in; treat the rest as reserved structure, not implemented
> behavior.

## 3. Feature engineering (Phase 3 — implemented, provisional)

`backend/app/services/feature_extractor.py` computes, per sentence: word/
character/punctuation counts, average word length, POS ratios (noun,
verb, adjective, adverb, pronoun), and maximum dependency-tree depth. Per
essay: sentence-length mean/std/coefficient-of-variation, a short/medium/
long sentence-length distribution, type-token ratio, a windowed moving-
average type-token ratio, a rare-word ratio (via the `wordfreq` library's
Zipf-scale frequency data), and three repetition measures (repeated
bigrams, repeated trigrams, repeated sentence openings).

This is explicitly a **provisional** set (DEC-006): each feature is a
standard, literature-grounded stylometric measure, but none has been
tested yet against real human/AI-written text, because that requires the
Phase 5 dataset. **What the system measures** (the numbers above) is
therefore already true; **what the system infers** from them (whether any
of this indicates AI involvement) is not yet defined — that is Phase 6's
scoring/calibration work, informed by EXP-002 once Phase 5 exists.

## Purpose of this document

Once implemented, this document must clearly separate:

- **What the system measures** — concrete, computed quantities (e.g.
  mean token log-probability, sentence-length coefficient of variation).
- **What the system infers** — a classification derived from comparing
  those measurements to reference distributions, with an explicit
  confidence/uncertainty level.

It must never claim that a measurement or inference *proves* authorship.
Writing style is evidence, not proof.

## Remaining planned sections (to be written in the phases noted)

1. Problem formulation — Phase 6 (what "detection" means here: a
   calibrated estimate over writing characteristics, not an authorship
   proof)
2. Hypotheses driving feature selection — ongoing (recorded per-feature in
   `experiments/`, not asserted here without an experiment behind it; see
   DEC-006 for the Phase 3 starting hypotheses)
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
