# DEC-007 — Local Language Model Choice

## Status
Accepted

## Date
2026-08-10

## Context

Per [DEC-004](DEC-004-no-llm-classifier.md), a local causal language model
is needed purely as an instrument to compute token log-probabilities and
perplexity. It must run locally on a normal developer laptop (Section 3/21
of the project brief: no paid API, avoid huge models) and be loaded once
per process and reused (Section 5/21).

## Problem

Which specific local causal LM should be loaded?

## Alternatives Considered

### Alternative A: `distilgpt2` (82M parameters)
Advantages:
- Explicitly named as a suggested option in the project brief.
- Small enough to load and run forward passes on CPU quickly — verified
  locally: loads in under a second, 82M parameters, 1024-token context
  window, standard GPT-2 fast tokenizer with exact character-offset
  mapping (needed to attribute tokens back to sentences, see DEC-008).
- GPT-2-family models are a common, well-understood baseline in AI-text-
  detection literature for perplexity-based signals, so behavior here is
  not exotic or unvalidated as a category of instrument.

Disadvantages:
- Weaker/noisier probability estimates than a larger model, since it's a
  distilled, smaller model — a real limitation to document (Phase 10/11),
  not to hide.

### Alternative B: `gpt2` (124M parameters, the "small" GPT-2)
Advantages:
- Same tokenizer and architecture family as distilgpt2 (a code-level
  drop-in — switching later is a one-line constant change), somewhat
  better-calibrated probabilities.

Disadvantages:
- ~1.5x the parameters and correspondingly slower CPU inference for no
  guaranteed improvement in the specific signal this project needs
  (relative perplexity differences between human/AI/mixed sentences,
  compared against reference distributions rather than used as an
  absolute quality metric).

### Alternative C: EleutherAI `gpt-neo-125M`
Advantages:
- Comparable size/quality to gpt2-small, different training data mix.

Disadvantages:
- No concrete advantage over the GPT-2 family for this use case, and less
  standard/well-trodden tooling support than GPT-2's tokenizer/config
  classes. No reason to prefer it over the brief's own suggested option.

### Alternative D: A larger modern model (e.g. TinyLlama-1.1B, Phi-2)
Advantages:
- Likely better-calibrated, more "human-like" probability estimates from
  a stronger model.

Disadvantages:
- 10-25x the parameter count — directly conflicts with Section 21
  ("avoid huge models," "run on a normal developer laptop"). These models
  are also typically instruction-tuned/chat-oriented, not optimized for
  raw next-token probability estimation on arbitrary prose, and have no
  established precedent as a detector-instrument backbone the way GPT-2
  does.

### Alternative E: A classical n-gram language model (e.g. KenLM) instead
of a neural LM
Advantages:
- Extremely fast, no GPU/CPU tensor computation needed.

Disadvantages:
- Captures only local n-gram statistics, not the kind of longer-range
  contextual predictability a neural LM captures (e.g. "this sentence is
  suspiciously smooth given the whole preceding paragraph"). Also
  introduces a non-Python-ecosystem dependency (KenLM is a C++ library
  with its own build toolchain) for a weaker signal.

## Decision

Use `distilgpt2` via Hugging Face `transformers`
(`AutoTokenizer`/`AutoModelForCausalLM`), loaded once per process.

## Why

It satisfies the local/lightweight constraint with the least engineering
risk, is explicitly sanctioned by the project brief, and — critically —
shares its tokenizer/architecture family with `gpt2`, so if Phase
10/11 evaluation shows distilgpt2's signal is too weak or noisy, escalating
to `gpt2` is a one-constant change (`MODEL_NAME` in
`language_model.py`), not a rewrite.

## Evidence

Verified locally: model loads, produces token log-probabilities with
correct character-offset alignment via the fast tokenizer's
`return_offsets_mapping`, 1024-token context window, ~82M parameters. No
comparative accuracy experiment against `gpt2` was run — this decision is
about which starting model to instrument with, not a claim that
distilgpt2-derived features carry more signal than gpt2-derived ones
(that question is downstream of DEC-004's Revisit criterion, EXP-003).

## Trade-offs

Accepting a smaller, less powerful LM than what's technically available,
in exchange for guaranteed fast local CPU inference and a documented,
low-risk upgrade path if it proves insufficient.

## Consequences

Positive:
- Fast local inference with no GPU requirement.
- Drop-in upgrade path to `gpt2` if needed.

Negative:
- Probability estimates are noisier than a larger model's — must be
  reflected honestly in confidence/uncertainty reporting (Phase 6) and in
  failure analysis (Phase 11) if it turns out to be a source of errors.

## Revisit When

If EXP-003 (Phase 5/6) shows LM-derived features have weak or noisy
signal, first try escalating to `gpt2` (same tokenizer family, minimal
code change) before concluding the feature category itself is not useful
(that broader question is DEC-004's revisit criterion).

## Implementation

`backend/app/services/language_model.py`

## Tests / Experiments

`backend/tests/test_language_model.py`. Signal-validation experiment
(EXP-003) not yet run.
