# Alternatives Considered

This document records architecture- and approach-level alternatives that
were evaluated and rejected outright, as distinct from
[`decisions/`](decisions/) which records the alternatives around a
decision that *was* made (including the one chosen). Entries here are
approaches the project will not pursue at all.

This file grows across phases. Phase 1 only fixes the foundational,
whole-system approach — feature-level and calibration-level alternatives
(sentence segmentation methods, calibration methods, specific feature
sets) are deferred to the phases that actually produce evidence for them,
and will be added there rather than guessed at now.

---

## 1. LLM-as-classifier

**What it was:** Send the essay (or each sentence) directly to a large
language model with a prompt like "Is this AI-written? Give a
percentage."

**Why considered:** It is the fastest possible way to produce a plausible-
looking output, and is what most people picture when they hear "AI
detector."

**Advantages:** Trivial to implement; no feature engineering, no dataset,
no calibration needed.

**Disadvantages:** Not explainable (no measurable feature backs the
number), not reproducible (sensitive to prompt/model-version drift),
cannot honestly show sentence-level evidence without fabricating a
rationale after the fact, cannot be calibrated against a reference
distribution, and requires a paid external API for the strongest models.

**Why rejected:** Explicitly excluded by the project brief (this is
precisely the "Essay → ChatGPT → 73% AI" pattern the brief rejects), and
independently a poor fit for an evaluable, explainable system. See
[DEC-004](decisions/DEC-004-no-llm-classifier.md).

**Future usefulness:** None, as a classifier. A local causal LM remains
useful purely as a feature-extraction instrument (DEC-004).

---

## 2. Retrieval-Augmented Generation (RAG)

**What it was:** Retrieve similar known-human or known-AI essays from a
corpus and use that retrieval to inform or generate a verdict.

**Why considered:** RAG is a common pattern for "grounding" LLM outputs in
real data.

**Advantages:** Could surface similar reference examples for a user to
compare against.

**Disadvantages:** The task here is not question-answering or generation
grounded in a knowledge base — it's per-sentence statistical
classification against reference *distributions*, not a retrieval problem.
Adding a retrieval layer would introduce a vector index and similarity
search step that doesn't map onto how the scoring actually needs to work
(comparing scalar feature values to population statistics, not comparing
document embeddings).

**Why rejected:** No part of the problem as scoped requires retrieval;
adding it would be unjustified architectural complexity (explicitly
flagged as something to avoid, Section 43).

**Future usefulness:** Conceivable if the product later wanted to show a
user "essays with similar feature profiles," but that's a distinct feature
from detection itself and out of scope.

---

## 3. Multi-agent architecture

**What it was:** Multiple cooperating LLM-based agents (e.g. one agent
extracts features, another critiques, another decides).

**Why considered:** Multi-agent pipelines are a popular pattern for
complex reasoning tasks.

**Advantages:** Could in principle divide "extraction" from "judgment."

**Disadvantages:** Reintroduces the exact problem DEC-004 rules out —
judgment would end up being made by an LLM agent rather than by our
measurable scoring system, just with extra steps and extra latency/cost.
It also adds orchestration complexity with no corresponding requirement:
this is a single-request, single-response analysis task, not a multi-step
tool-use problem.

**Why rejected:** Unnecessary architectural complexity for a task that is
fundamentally "compute features → compare to reference distributions →
score" — a pipeline, not an agentic reasoning loop.

**Future usefulness:** None identified for this project's scope.

---

## 4. Large fine-tuned transformer as an end-to-end classifier

**What it was:** Fine-tune a transformer (e.g. RoBERTa) directly on
human/AI-labeled essays to output a classification, instead of building
handcrafted/statistical features.

**Why considered:** This is the standard approach in published AI-text-
detection literature and often achieves strong benchmark accuracy.

**Advantages:** Potentially higher raw accuracy than a feature-based
approach; well-studied in the literature.

**Disadvantages:** Produces an opaque score with no per-feature evidence —
explaining *why* a fine-tuned transformer flagged a sentence would require
a separate interpretability method (e.g. attention visualization or
SHAP), which is significantly harder to make honest and legible to a
non-technical user than "perplexity is in the lowest 8% of the human
reference distribution." It also requires a labeled training set large
enough to fine-tune on, which raises the same provenance/leakage
concerns as the reference-distribution approach but with less
interpretable output per unit of data.

**Why rejected:** Explainability (Sections 5, 19) is a core, explicitly
weighted evaluation criterion for this project — a feature-based,
distribution-comparison approach is directly interpretable by
construction, which a fine-tuned transformer is not without substantial
additional work.

**Future usefulness:** Could be explored later as one more *feature*
(e.g. a fine-tuned classifier's output score fed in alongside other
features, with its own reference distribution) rather than as the sole
decision-maker — but only with evidence that it adds signal beyond the
simpler features, and only if an interpretable way to surface its
contribution is designed. Not planned; noted for completeness.

---

## 5. Single perplexity threshold as "the detector"

**What it was:** Pick one perplexity value (e.g. "perplexity < 20 =
AI") and classify on that alone.

**Why considered:** It's the simplest possible use of a language model
signal and is a common naive baseline.

**Advantages:** Extremely simple, no calibration pipeline needed.

**Disadvantages:** The brief explicitly warns against assuming "low
perplexity = AI" as a universal rule (Section 6A) — perplexity depends
heavily on topic, vocabulary, and writing style, and a fixed threshold
would not account for that or for second-language writers' naturally
different predictability profiles (a fairness concern, Section 16).

**Why rejected:** Arbitrary, unevaluated thresholds are explicitly
disallowed (Section 8: "Do not build the detector around arbitrary
thresholds"). Any use of perplexity must go through reference-distribution
comparison and calibration, evaluated with real metrics.

**Future usefulness:** Perplexity itself remains a candidate feature
(see [DEC-004](decisions/DEC-004-no-llm-classifier.md)) — what's rejected
here is using it alone, via a hardcoded threshold, as the entire system.

---

## 6. Dataset composition: fully synthetic vs. human-only vs.
human+AI (binary) vs. human+AI+mixed

**What was compared:** how much of the dataset's authorship variety to
actually construct.

- **Fully synthetic** (no real human data — e.g. generate both "human-
  style" and "AI-style" text from models): avoids any human-data
  licensing/privacy question entirely, but there's no reason to believe
  model-generated "human-style" text has the actual statistical
  properties of real human writing — this would validate the pipeline
  against itself, not against reality. Rejected.
- **Human-only** (no machine or mixed samples at all): defeats the
  purpose — there is nothing to detect. Rejected trivially, included only
  for completeness.
- **Human + AI, binary** (every sample is either fully human or fully
  machine-generated, no mixed category): far simpler to build and label,
  but directly contradicts Section 11's explicit requirement to support
  realistic partial-AI-assistance scenarios, and would make sentence-
  level evaluation meaningless (every sentence in a given sample has the
  same label by construction, so there's nothing to localize). Rejected.
- **Human + AI + mixed** (chosen): the only composition that lets
  sentence-level and passage-level detection be evaluated meaningfully,
  and the only one that reflects how AI assistance plausibly actually
  occurs (partial, not all-or-nothing). Selected — see
  [DEC-011](decisions/DEC-011-mixed-text-generation.md) for the mixed-
  category taxonomy and mechanism.

## 7. Same generation model for both dataset construction and detection

**What it was:** use `distilgpt2` (the detection instrument, DEC-007) to
also generate the machine/mixed samples.

**Why considered:** avoids introducing a second model/dependency.

**Why rejected:** `distilgpt2` is not instruction-tuned — it cannot
reliably follow "write an essay about X" or "rewrite only this sentence"
instructions, which the generation pipeline depends on (DEC-011's
surgical-splice mechanism specifically needs instruction adherence).
Separately, generating and detecting with the same model risks the
detector learning that specific model's continuation quirks rather than
anything that generalizes — precisely the failure mode Section 17 warns
about. See [DEC-010](decisions/DEC-010-machine-generation-model.md).

## 8. Local generation model vs. hosted API

Full comparison in [DEC-010](decisions/DEC-010-machine-generation-model.md).
Summary: a hosted frontier API (GPT-4o-mini, Claude Haiku, Gemini Flash)
would produce higher-quality, more diverse generations, but costs money
at dataset scale, requires network/API-key access not present in this
environment, and weakens exact reproducibility (server-side model
versions can change). A small local instruction-tuned model
(Qwen2.5-1.5B-Instruct, Apache-2.0) was selected instead, consistent with
this project's local-first posture throughout (DEC-004, DEC-007,
DEC-008). Hosted APIs remain a documented *future* option specifically
for a held-out, never-used-in-training generalization-test slice
(Section 17) — not for primary dataset construction.

---

## Deferred entries

The following alternatives are relevant to later phases and will be
documented here once there is actual evidence to compare, rather than
speculated on now:

- Specific handcrafted feature sets vs. purely statistical features
  (Phases 3–5, tracked via `experiments/`)
- Calibration methods (Phase 6)
- Passage-grouping strategies (Phase 7)
- Diff-similarity threshold and structure-drift tolerance for the
  polish-category mixed samples (deferred to EXP-DATA-001 pilot evidence,
  per [DEC-011](decisions/DEC-011-mixed-text-generation.md))
