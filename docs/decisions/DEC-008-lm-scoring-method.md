# DEC-008 — Language Model Scoring Method (Whole-Document vs. Per-Sentence)

## Status
Accepted

## Date
2026-08-10

## Context

Section 6A asks for per-sentence predictability signals (mean/median
token log-probability, perplexity, log-probability variance) and for how
predictability *changes between neighboring sentences*. A causal LM's
probability for a token is conditioned on everything that came before it
in the input it's given — so how much context each sentence's tokens are
scored with is a real design choice, not just an implementation detail.

## Problem

Should each sentence be scored by the LM in isolation, or should the
whole essay be scored in one pass (or a few, for long essays) with each
token's log-probability then attributed back to its containing sentence?

## Alternatives Considered

### Alternative A: Score each sentence independently
Feed each sentence to the model on its own (optionally batched together
with padding).

Advantages:
- Simple to reason about; no chunk-boundary or offset-attribution
  bookkeeping.
- Trivially batchable across sentences in one call.

Disadvantages:
- Every sentence's first token is scored with zero preceding context,
  since the model sees only that sentence — this "no-context first token"
  problem is paid once *per sentence* rather than once per ~1024-token
  chunk.
- Discards genuine document context: a sentence that is highly predictable
  *given what the essay already established* would look artificially
  "surprising" when scored alone, and vice versa. This directly
  undermines the neighboring-sentence predictability-change signal the
  brief asks for (Section 6A) — that signal is about how predictability
  shifts in context, which requires scoring in context.

### Alternative B: Score the whole essay in one pass (chunked only if it
exceeds the model's context window), then attribute each token's
log-probability back to whichever sentence's character range contains it
Advantages:
- Each token (except the very first token of the whole essay, and one
  token at each chunk boundary for essays long enough to need chunking)
  is scored with its true preceding context — the sentence-to-sentence
  predictability *change* signal is measuring what it's supposed to.
- More efficient for the common case: most essays fit inside distilgpt2's
  1024-token context window, so this is a *single* forward pass for the
  entire essay rather than N passes (one per sentence) — directly serves
  Section 21's "batch computations where possible."

Disadvantages:
- Requires chunking logic for essays exceeding 1024 tokens, and offset-
  based attribution of tokens to sentences (via the fast tokenizer's
  character offsets, already available per DEC-007's verification).
- Each chunk boundary introduces one token with no preceding context
  within that chunk — a small, bounded, and documented approximation
  (at most one dropped/unconditioned token per ~1024 tokens), not hidden.

## Decision

Score the whole (normalized) essay in one pass, chunking only when it
exceeds the model's context window (1024 tokens for distilgpt2), and
attribute each scored token back to its containing sentence via character
offsets.

## Why

This is both more efficient for typical essay lengths and more faithful
to what the brief's "predictability" and "change in predictability
between neighboring sentences" signals are actually supposed to measure —
context-conditioned surprise, not isolated-sentence surprise.

## Evidence

Structural/correctness decision, verified by tests
(`test_language_model.py`) confirming: (1) token log-probabilities are
computed only for tokens with at least one preceding token in their
scoring window, (2) sentence attribution via character offsets correctly
groups tokens, (3) chunking activates only when input exceeds the context
window and does not crash or silently drop entire sentences. No
comparative experiment against per-sentence scoring (Alternative A) was
run, since Alternative A's conceptual mismatch with the required
neighboring-sentence signal (Section 6A) makes it unsuitable regardless of
measured output quality.

## Trade-offs

Slightly more implementation complexity (offset-based attribution,
chunk-boundary handling) in exchange for context-faithful scores and
fewer forward passes.

## Consequences

Positive:
- Sentence-level LM features reflect actual document context.
- One forward pass per essay in the common case (essay under ~1024
  tokens) rather than one per sentence.

Negative:
- Essays long enough to require chunking (order of ~4,000+ words) get a
  small number of context-free tokens at chunk boundaries — bounded and
  documented, not a correctness bug, but worth surfacing in
  docs/evaluation.md if it correlates with errors on long essays.
- A sentence whose entire span falls within the one "no-context" token at
  the very start of the essay (only possible for a first sentence that is
  a single token long) yields no scorable tokens; such a sentence's LM
  features are reported as unavailable (`None`) rather than fabricated,
  consistent with the project's "insufficient evidence" principle
  (Section 8).

## Revisit When

If Phase 10/11 evaluation shows chunk-boundary artifacts measurably harm
accuracy on long essays, consider adding a small token-overlap between
chunks (re-feeding the tail of the previous chunk as unscored context for
the next) to eliminate the per-chunk context-free token.

## Implementation

`backend/app/services/language_model.py`

## Tests / Experiments

`backend/tests/test_language_model.py`
