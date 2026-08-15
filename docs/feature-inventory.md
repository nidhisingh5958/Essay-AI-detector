# Feature Inventory

Catalogs every measurable signal this project can currently compute,
separated strictly into **IMPLEMENTED** (exists, tested, callable today)
and **PROPOSED** (not implemented — do not use as if it exists). Built
for [EXP-003](experiments/EXP-003.md); read that document for which of
these are actually selected for EXP-003A/B/C's primary feature set vs.
baselines.

Per DEC-004: every LM-derived row below is a **measurement**, not a
judgment — the local model (`distilgpt2`) never classifies anything.
Direction (whether a high or low value correlates with which class) is
explicitly **not asserted** below for any feature — that is exactly
what EXP-003 exists to measure empirically (see EXP-003 §"Do not assume
feature direction").

## IMPLEMENTED

### Sentence-level (`backend/app/services/feature_extractor.py::extract_sentence_features`)

| Feature | Definition | LM-derived? | Type | Known limitations |
|---|---|---|---|---|
| `word_count` | Count of alphabetic tokens in the sentence | No | stylometric | Sensitive to segmentation edge cases (informal punctuation — see failure-analysis.md Failure 3, 10) |
| `char_count` | Total characters across alphabetic tokens | No | stylometric | Correlated with `word_count` |
| `punctuation_count` | Count of punctuation tokens | No | stylometric | Not normalized by sentence length in this raw form |
| `avg_word_length` | `char_count / word_count` | No | stylometric | 0.0 for a sentence with no alphabetic tokens (rare, degenerate) |
| `noun_ratio`, `verb_ratio`, `adj_ratio`, `adv_ratio`, `pronoun_ratio` | POS tag count / total token count (including punctuation in denominator) | No | stylometric (syntactic) | Denominator includes non-word tokens; ratios across the 5 tags do not sum to 1 |
| `dependency_depth` | Maximum depth of the spaCy dependency parse tree for the sentence | No | stylometric (syntactic) | Recursive computation, O(tokens); sensitive to parser errors on informal/ungrammatical student writing |

### Essay-level (`extract_essay_features`)

| Feature | Definition | LM-derived? | Type | Known limitations |
|---|---|---|---|---|
| `sentence_count` | Number of segmented sentences | No | structural | — |
| `sentence_length_mean` / `_std` / `_cv` | Mean, population std-dev, and coefficient of variation of per-sentence word counts | No | rhythm | `_cv` undefined (0.0 by convention) when mean is 0 |
| `short_sentence_ratio` / `medium_sentence_ratio` / `long_sentence_ratio` | Fraction of sentences ≤10, 11–20, >20 words (DEC-006 thresholds) | No | rhythm | Bucket boundaries are a DEC-006 convention, not empirically tuned |
| `type_token_ratio` | Unique words / total words, essay-wide | No | vocabulary | Known to shrink with essay length — this is exactly why `moving_average_ttr` also exists |
| `moving_average_ttr` | Mean TTR over a 50-word sliding window (falls back to whole-essay TTR if essay has ≤50 words) | No | vocabulary | Window size (50) is a DEC-006 convention |
| `rare_word_ratio` | Fraction of words with `wordfreq.zipf_frequency < 3.0` | No | vocabulary | Threshold (3.0 Zipf) is a DEC-006 convention, not fitted; `wordfreq` may score domain-specific/proper-noun terms unreliably |
| `repeated_bigram_ratio` / `repeated_trigram_ratio` | Fraction of word n-grams that recur elsewhere in the essay | No | repetition | Whole-essay, not scoped to distance between repeats |
| `repeated_sentence_opening_ratio` | Fraction of sentences whose first-two-word opening recurs elsewhere | No | repetition | Case-insensitive; does not account for legitimate rhetorical repetition (e.g. anaphora) |

**Status**: DEC-006, Provisional — literature-grounded but explicitly
**not yet validated** against real human/AI-labeled text. EXP-003A is
the first experiment to measure whether any of these actually separate
the classes on PRIMARY-DATASET-v1.

### Token/sentence-level, LM-derived (`backend/app/services/language_model.py`)

| Feature | Definition | LM-derived? | Type | Known limitations |
|---|---|---|---|---|
| `TokenLogProb` (per token) | Log-probability of each token given all preceding tokens in the essay (teacher-forced, `distilgpt2`, one pass, chunked only past 1024 tokens) | Yes | LM instrument | First token of the essay (and of each subsequent chunk) is unscored — no preceding context; DEC-008 |
| `mean_log_prob` / `median_log_prob` | Mean/median of a sentence's token log-probabilities | Yes | LM instrument | `None` if the sentence has zero scored tokens (e.g. one-token first sentence) — reported as missing, not a fabricated 0 |
| `log_prob_variance` | Population variance of a sentence's token log-probabilities | Yes | LM instrument | 0.0 by convention for a sentence with exactly 1 scored token |
| `perplexity` | `exp(-mean_log_prob)` | Yes | LM instrument | Explicitly **not** validated as an "AI-ness" signal — DEC-004/methodology.md's standing warning: low perplexity means "unsurprising to `distilgpt2`," not "AI-written" |
| `token_count` | Number of scored tokens contributing to the above | Yes | LM instrument | — |

### Essay-level, LM-derived (`compute_predictability_deltas`)

| Feature | Definition | LM-derived? | Type | Known limitations |
|---|---|---|---|---|
| `predictability_delta` (per sentence, vs. previous) | `curr.mean_log_prob - prev.mean_log_prob` | Yes | LM instrument | `None` for the essay's first sentence, or whenever either side has no scored tokens |

**Status**: DEC-007 (model choice, `distilgpt2`) / DEC-008 (scoring
method) — implemented, tested (`backend/tests/test_language_model.py`),
**not yet validated for detection signal**. EXP-003's baselines (§7 of
EXP-003.md) test this feature family in isolation before combining it
with anything else, specifically to avoid assuming "low perplexity =
AI" as DEC-004 already warns against.

## PROPOSED (not implemented — do not treat as available)

These are named because they were considered in DEC-006/DEC-004's
original scoping discussion or are natural next candidates, **not**
because they exist. None should be referenced as an EXP-003 feature
unless implemented and tested first.

| Proposed feature | Rationale | Why not yet implemented |
|---|---|---|
| Function-word distribution | Standard stylometric signal (DEC-006 explicitly named this as a candidate for later) | Deferred in DEC-006 pending evidence the current set is insufficient |
| Clause-boundary / conjunction-based complexity | Alternative to dependency depth | Rejected in DEC-006 as a cruder proxy for the same thing dependency depth already measures |
| NLI/entailment-based signal | Considered for DEC-012/DEC-013's semantic screens | Deferred (DEC-012 Alternative B) — a screening-tool candidate, not a detector feature; would require a new model dependency |
| Sentence-embedding-based features (beyond DEC-012's screening use) | `sentence-transformers` is already a dependency (DEC-012) | Not evaluated as a detector feature; DEC-012 uses it only for the semantic-preservation screen, a different purpose (dataset QC, not detection) |
| Cross-sentence coherence/cohesion metrics | ELLIPSE's own scored dimensions (Cohesion, Syntax, etc.) suggest this category has precedent | Not implemented; would require new computation, not currently justified without evidence existing features are insufficient |
| Second local-LM signal (e.g. a larger model for cross-checking) | Could reduce dependence on one small model's idiosyncrasies | Explicitly out of scope — DEC-007 fixed `distilgpt2` as the single instrument; adding a second is a new decision, not proposed here |

## How this inventory is used

EXP-003A/B/C (see [experiments/EXP-003.md](experiments/EXP-003.md))
selects its primary feature set and baselines exclusively from the
IMPLEMENTED table above. No PROPOSED feature is used in any baseline or
the primary model until it is implemented, tested, and added to this
inventory as IMPLEMENTED first.
