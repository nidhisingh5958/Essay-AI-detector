# Fairness

> Status: not started. No evaluation data with appropriate subgroup labels
> exists yet (see [project-status.md](project-status.md), Phase 12). This
> document is a placeholder for the required analysis (Section 16/40) —
> it is not a claim that fairness has been evaluated or established.

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
