# Evaluation

> Status: not started. No model, scoring system, or dataset exists yet to
> evaluate (see [project-status.md](project-status.md), Phase 10). No
> metrics are reported below because none have been measured — this
> document is a placeholder for the reporting structure the brief
> requires (Section 14), not a claim of results.

## What will be reported here (Phase 10, after Phases 5–7 exist)

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
