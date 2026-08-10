# Failure Analysis

> Status: not started. There is no trained/calibrated system yet to
> produce failures from (see [project-status.md](project-status.md),
> Phase 11). This document is a placeholder for the required structure
> (Section 15/39) — it will be populated with at least three real,
> confidently-wrong examples once evaluation (Phase 10) has actually run,
> never with invented ones.

## Required structure per failure case (Phase 11)

For each of at least three essays the detector confidently gets wrong:

1. The essay/passage sample
2. Ground truth label
3. The system's prediction and stated confidence
4. The actual feature values that drove the (wrong) prediction
5. An analysis of why the detector likely failed — tied to specific
   feature behavior, not speculation
6. A concrete idea for how the system could improve, ideally phrased as a
   testable follow-up experiment

## Ground rule

These cases will not be hidden or cherry-picked to look better than they
are (Section 15: "Do not hide these examples"). The purpose of this
section is to demonstrate understanding of the system's real failure
modes, which is only possible once the system exists and has been run
against held-out data.
