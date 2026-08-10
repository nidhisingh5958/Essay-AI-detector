# DEC-004 — Language Models Are an Instrument, Never the Classifier

## Status
Accepted

## Date
2026-08-10

## Context

The most common naive way to build an "AI detector" is: send the essay to
a large language model and ask "is this AI-written?" This is explicitly
rejected by the project brief (Sections 2 and 43), and independently, it
is a poor design for an explainable, evaluable system: the verdict comes
from an opaque model call, there is no measurable feature behind it, it
cannot be calibrated against a reference distribution, and it cannot be
evaluated with reproducible metrics — a different phrasing of the prompt
or a model version change silently changes results.

## Problem

How should any language model be used in this system, if not to classify?

## Alternatives Considered

### Alternative A: LLM-as-classifier ("Is this essay AI-written? Answer
with a percentage.")
Advantages:
- Trivial to implement, no feature engineering required.

Disadvantages:
- Not explainable: no measurable feature backs the number.
- Not reproducible: sensitive to prompt wording and model version.
- Cannot show sentence-level evidence honestly (would require asking the
  LLM to fabricate a rationale after the fact, i.e. fake explainability —
  explicitly disallowed, Section 19).
- Cannot be calibrated against a reference distribution.
- Explicitly rejected by the project brief.

### Alternative B: Remote LLM API used only for token-probability
extraction (e.g. via an API that exposes logprobs)
Advantages:
- Larger models than what runs locally, potentially better-calibrated
  probabilities.

Disadvantages:
- Introduces a paid external dependency and a network requirement,
  contradicting Section 3 ("run locally without requiring a paid external
  API," "prefer local inference").
- Nondeterministic availability/versioning outside our control.

### Alternative C: Local causal LM used purely as an instrument
(token log-probabilities, perplexity, predictability/burstiness), feeding
our own feature-based scoring system.
Advantages:
- Runs fully locally, no API cost or network dependency.
- Produces genuinely measurable, numeric features (log-prob, perplexity)
  that can be compared against reference distributions and shown to the
  user as evidence.
- The final classification is produced by our own scoring/calibration
  code, which is inspectable and testable — not a black-box verdict.

Disadvantages:
- A small local model (e.g. distilgpt2) is weaker than a large hosted
  model, so its probability estimates are noisier. This is a real
  limitation to document (docs/methodology.md, docs/failure-analysis.md),
  not to hide.

### Alternative D: No language model at all — purely handcrafted
linguistic/statistical features (sentence rhythm, vocabulary, repetition,
POS patterns).
Advantages:
- Fully local, fully interpretable, no model-loading cost.

Disadvantages:
- Discards a category of signal (predictability/perplexity) that the
  brief explicitly asks us to investigate (Section 6A) and that prior AI-
  text-detection literature treats as informative. Rejecting it outright
  without testing it would be a decision made without evidence, which the
  brief also disallows (Section 27).

## Decision

Use a small local causal language model strictly as a feature-extraction
instrument (log-probabilities, perplexity, burstiness). All classification,
scoring, and explanation generation is done by our own code against
reference distributions built from our dataset. No LLM (local or remote)
is ever asked to produce a verdict, a percentage, or a natural-language
explanation of why a sentence was flagged.

## Why

This is the only alternative that satisfies all real constraints
simultaneously: local/no paid API (Section 3), explainability with
measurable evidence (Sections 5, 19), and not discarding a plausibly
useful signal without testing it (Section 27). Alternative D remains a
fallback: if the local LM's signal turns out not to be useful once
measured (Phase 4/5 experiments), the architecture already supports
scoring without it, since it's one feature group among several (Section
6).

## Evidence

No experiment yet — this is a foundational constraint fixed before any
feature-quality measurement was possible. Whether the LM features actually
help will be tested empirically in EXP-003 ("linguistic + perplexity" vs
EXP-002 "linguistic only") once the dataset and feature pipeline exist
(Phases 4–5). This decision fixes *how* the LM may be used, not whether
its output ends up mattering.

## Trade-offs

We give up the (illusory) simplicity of an LLM-as-judge approach, in
exchange for an implementation that requires real feature engineering,
reference-distribution construction, and calibration work before it
produces any classification at all.

## Consequences

Positive:
- Every number shown to the user is traceable to a computed feature.
- The system can be evaluated with standard metrics (precision/recall/F1)
  because its output is deterministic given fixed model weights and code,
  not a live LLM call.

Negative:
- More upfront engineering effort than an LLM-wrapper approach.
- Local model quality ceiling — documented as a limitation, revisited if
  evidence (EXP-003 and later) shows the signal is too weak to be useful.

## Revisit When

If EXP-003 shows local-LM-derived features (perplexity, log-prob variance)
provide no measurable improvement over linguistic-only features on
validation F1, in which case the LM feature group would be dropped (not
the local-only-instrument principle itself, which is a hard constraint
from the brief).

## Implementation

To be added in Phase 4: `backend/app/services/language_model.py`.

## Tests / Experiments

To be added: `experiments/EXP-003-token-probabilities/`.
