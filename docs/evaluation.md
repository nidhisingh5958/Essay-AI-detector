# Evaluation

> Status: **six experiments executed, 2026-08-15** — EXP-003A, EXP-003B,
> EXP-003B-R1, EXP-003C, GEN-001, FAIR-001. Full metrics live in each
> experiment's own report (not duplicated here — see
> [decision-summary.md](decision-summary.md) for a quick-reference
> summary and [PRODUCT-AUDIT.md](PRODUCT-AUDIT.md) §1 for the
> synthesized evidence table). This document remains the reporting
> *structure* the brief requires; the checklist below is now checked
> off against what was actually measured, not still a placeholder.

## What has been reported (per experiment)

- **Dataset and split**: PRIMARY-DATASET-v1 (150 families, 425-sample
  benchmark, frozen); every experiment above references its exact
  split counts in its own report.
- **Accuracy, precision, recall, F1**: reported per experiment —
  EXP-003A (~98–100% test accuracy), EXP-003B (near-chance essay-level,
  86.7%/17.6% sentence-level recall/precision), EXP-003C (72.6%
  accuracy, macro-F1 0.564, `ai_assisted` collapse), GEN-001 (97.8%/100%
  cross-generator), FAIR-001 (subgroup FP/FN rates, not accuracy).
- **Confusion matrix**: reported for EXP-003A, EXP-003C, GEN-001.
- **False-positive rate, false-negative rate**: reported for EXP-003A/B/C/GEN-001,
  and specifically by fairness subgroup in FAIR-001.
- **Sentence-level, passage-level, essay-level results reported
  separately**: yes — EXP-003B/B-R1 report sentence-level localization
  entirely separately from essay-level classification, exactly as
  planned; essay-level accuracy alone was never used as the sole
  headline (every report states both).
- **Calibration quality**: not formally assessed as a separate metric
  in any experiment; the closest evidence is EXP-003C's per-sample
  probability inspection (§12 of that report), which found probabilities
  carry real information even where the plain-argmax decision doesn't
  — a partial, not comprehensive, calibration finding.
- **Precision/recall trade-off discussion**: EXP-003B/B-R1 explicitly
  discuss this for sentence localization (recall-favoring threshold
  selection, with the resulting low precision stated plainly, not
  hidden). Not separately discussed for essay-level `full_ai` detection
  (accuracy is high enough there that the trade-off is less material).

## Original planned structure (Phase 10, kept for reference)

- Dataset and split used (referencing [dataset.md](dataset.md))
- Experiment configuration (referencing the specific `experiments/EXP-XXX/`
  run)
- Accuracy, precision, recall, F1
- Confusion matrix
- False-positive rate, false-negative rate
- Sentence-level, passage-level, and essay-level results reported
  separately (Section 14) — essay-level accuracy alone will not be used
  as the headline result, since the product's core claim is sentence/
  passage-level explainability
- Calibration quality (are stated confidence levels actually reliable?)
- Precision/recall trade-off discussion — an explicit statement of
  whether the system is tuned to minimize false accusations of students
  (favoring precision) or to catch more machine-written text (favoring
  recall), and why

## Ground rule

No number appears in this document unless it came from an experiment that
was actually run and is referenced by its `experiments/EXP-XXX/` ID. If a
metric looks favorable, it is reported; if it looks weak, it is reported
just as plainly (Section 14: "Do not fabricate metrics").
